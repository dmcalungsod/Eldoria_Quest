import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo before importing anything that uses it
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

# Now import the modules under test
from game_systems.adventure.adventure_rewards import STAT_EXP_GAINS  # noqa: E402
from game_systems.combat.combat_engine import CombatEngine  # noqa: E402


class TestStatXPRefinement(unittest.TestCase):
    def setUp(self):
        self.mock_player = MagicMock()
        self.mock_player.stats.max_hp = 100
        self.mock_player.hp_current = 100

        self.mock_monster = {
            "name": "Test Goblin",
            "HP": 50,
            "max_hp": 50,
            "atk": 10,
            "def": 0,
            "xp": 10,
        }

        self.mock_skills = []
        self.mock_stats = {
            "HP": 100,
            "MP": 50,
            "STR": 10,
            "DEX": 10,
            "MAG": 10,
            "AGI": 10,
            "LCK": 10,
            "DEF": 0,
        }

    def test_hits_taken_tracking(self):
        """Test that hits_taken is incremented when damage is taken."""
        engine = CombatEngine(
            player=self.mock_player,
            monster=self.mock_monster,
            player_skills=self.mock_skills,
            player_mp=50,
            player_class_id=1,
            stats_dict=self.mock_stats,
            action="defend",  # Force defend to ensure no dodge/crit randomness interference
        )

        # Mock monster attack to always hit (patching where it is used)
        with patch(
            "game_systems.combat.combat_engine.DamageFormula.monster_attack"
        ) as mock_attack:
            mock_attack.return_value = (10, False, "hit")  # dmg, crit, event_type

            # Force monster to attack
            with patch(
                "game_systems.monsters.monster_actions.MonsterAI.choose_action"
            ) as mock_ai:
                mock_ai.return_value = {"type": "attack"}

                result = engine.run_combat_turn()

                self.assertEqual(result["turn_report"]["hits_taken"], 1)
                self.assertEqual(
                    result["turn_report"]["damage_taken"], 5
                )  # Defend halves damage (10 -> 5)

    def test_hits_taken_ignored_on_dodge(self):
        """Test that hits_taken is NOT incremented on dodge."""
        engine = CombatEngine(
            player=self.mock_player,
            monster=self.mock_monster,
            player_skills=self.mock_skills,
            player_mp=50,
            player_class_id=1,
            stats_dict=self.mock_stats,
            action="defend",
        )

        # Patch DamageFormula where it is used in CombatEngine
        with patch(
            "game_systems.combat.combat_engine.DamageFormula"
        ) as MockDamageFormula:
            MockDamageFormula.monster_attack.return_value = (0, False, "dodge")

            with patch(
                "game_systems.monsters.monster_actions.MonsterAI.choose_action"
            ) as mock_ai:
                mock_ai.return_value = {"type": "attack"}

                result = engine.run_combat_turn()

                self.assertEqual(result["turn_report"]["hits_taken"], 0)
                self.assertEqual(result["turn_report"].get("player_dodge", 0), 1)

    def test_dynamic_damage_tagging(self):
        """Test that skills correctly tag damage based on scaling_stat."""
        # Skill scaling with MAG
        mag_skill = {
            "key_id": "fireball",
            "name": "Fireball",
            "mp_cost": 5,
            "scaling_stat": "MAG",
            "skill_level": 1,
        }

        # Skill scaling with DEX (e.g. AGI mapped to DEX hits)
        agi_skill = {
            "key_id": "swift_strike",
            "name": "Swift Strike",
            "mp_cost": 5,
            "scaling_stat": "AGI",
            "skill_level": 1,
        }

        engine = CombatEngine(
            player=self.mock_player,
            monster=self.mock_monster,
            player_skills=[mag_skill, agi_skill],
            player_mp=50,
            player_class_id=2,  # Mage
            stats_dict=self.mock_stats,
            action="skill:fireball",
        )

        with patch(
            "game_systems.combat.damage_formula.DamageFormula.player_skill"
        ) as mock_skill_dmg:
            mock_skill_dmg.return_value = (20, False, "hit")

            # 1. Test MAG Skill
            result = engine.run_combat_turn()
            self.assertEqual(result["turn_report"]["mag_hits"], 1)
            self.assertEqual(result["turn_report"]["dex_hits"], 0)

            # 2. Test AGI Skill (Should map to dex_hits)
            # Re-initialize engine with new action
            engine = CombatEngine(
                player=self.mock_player,
                monster=self.mock_monster,
                player_skills=[mag_skill, agi_skill],
                player_mp=50,
                player_class_id=2,
                stats_dict=self.mock_stats,
                action="skill:swift_strike",
            )
            result = engine.run_combat_turn()
            self.assertEqual(result["turn_report"]["dex_hits"], 1)

    def test_endurance_xp_formula(self):
        """Test the new Endurance XP formula."""
        # Formula: hits_taken * 1.0 + damage_taken * 0.1

        # Case 1: 5 hits, 50 damage
        report1 = {"hits_taken": 5, "damage_taken": 50}
        exp1 = STAT_EXP_GAINS["end_exp"](report1)
        expected1 = (5 * 1.0) + (50 * 0.1)  # 5 + 5 = 10
        self.assertEqual(exp1, 10.0)

        # Case 2: 5 hits, 0 damage (Perfect tanking)
        report2 = {"hits_taken": 5, "damage_taken": 0}
        exp2 = STAT_EXP_GAINS["end_exp"](report2)
        expected2 = (5 * 1.0) + (0 * 0.1)  # 5 + 0 = 5
        self.assertEqual(exp2, 5.0)

    def test_luck_xp_formula(self):
        """Test the new Luck XP formula."""
        # Formula: 0.5 + (crit * 0.5) + (dodge * 0.5)

        # Case 1: Base (no crits/dodges)
        report1 = {"player_crit": 0, "player_dodge": 0}
        exp1 = STAT_EXP_GAINS["lck_exp"](report1)
        self.assertEqual(exp1, 0.5)

        # Case 2: 2 Crits, 1 Dodge
        report2 = {"player_crit": 2, "player_dodge": 1}
        exp2 = STAT_EXP_GAINS["lck_exp"](report2)
        expected2 = 0.5 + (2 * 0.5) + (1 * 0.5)  # 0.5 + 1.0 + 0.5 = 2.0
        self.assertEqual(exp2, 2.0)
