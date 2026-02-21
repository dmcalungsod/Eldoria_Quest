import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["discord"] = MagicMock()
sys.modules["cogs"] = MagicMock()
sys.modules["cogs.ui_helpers"] = MagicMock()

# Setup mocks for UI helpers
sys.modules["cogs.ui_helpers"].make_progress_bar = MagicMock(return_value="[|||||]")
sys.modules["cogs.ui_helpers"].get_health_status_emoji = MagicMock(return_value="💚")

from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.monsters.monster_actions import MonsterAI  # noqa: E402
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds # noqa: E402
from game_systems.player.player_stats import PlayerStats # noqa: E402
from game_systems.player.level_up import LevelUpSystem # noqa: E402

class TestTelegraphEnhancement(unittest.TestCase):
    def setUp(self):
        # Setup Player Wrapper
        self.stats = PlayerStats(str_base=10, end_base=10, dex_base=10, agi_base=10, mag_base=10)
        self.player_wrapper = MagicMock(spec=LevelUpSystem)
        self.player_wrapper.stats = self.stats
        self.player_wrapper.level = 1
        self.player_wrapper.hp_current = 500
        self.player_wrapper.hp_max = 500
        self.player_wrapper.add_exp = MagicMock(return_value=False)

        # High Power Skill (Ultimate)
        self.ultimate_skill = {
            "key_id": "ultimate_doom",
            "name": "Ultimate Doom",
            "power": 2.5,
            "mp_cost": 0,
            "type": "magical"
        }

        # Medium Power Skill
        self.medium_skill = {
            "key_id": "heavy_hit",
            "name": "Heavy Hit",
            "power": 1.5,
            "mp_cost": 0,
            "type": "physical"
        }

        self.monster = {
            "name": "Void Lord",
            "HP": 1000,
            "max_hp": 1000,
            "MP": 100,
            "ATK": 50,
            "DEF": 10,
            "level": 10,
            "tier": "Boss",
            "skills": [self.ultimate_skill],
        }

    def test_monster_ai_guaranteed_telegraph(self):
        """
        Verify that skills with Power >= 2.0 ALWAYS telegraph, regardless of RNG.
        """
        # Mock side_effect:
        # 1. Skill Chance: 1 (Pass)
        # 2. Telegraph Chance: 100 (Fail - would fail if logic was missing)
        with patch("random.randint", side_effect=[1, 100]):
            with patch("random.choice", return_value=self.ultimate_skill):
                action = MonsterAI.choose_action(self.monster, 1000, 100)

                self.assertEqual(action["type"], "telegraph",
                                 "Power >= 2.0 should trigger telegraph even if RNG is bad")
                self.assertEqual(action["skill"], self.ultimate_skill)

    def test_monster_ai_conditional_telegraph(self):
        """
        Verify that skills with 1.5 <= Power < 2.0 still rely on RNG.
        """
        self.monster["skills"] = [self.medium_skill]

        # Case 1: RNG Fails
        # Call 1: Skill Chance (1) - Pass
        # Call 2: Telegraph Chance (51) - Fail
        with patch("random.randint", side_effect=[1, 51]):
            with patch("random.choice", return_value=self.medium_skill):
                action = MonsterAI.choose_action(self.monster, 1000, 100)
                # Should be normal skill usage, NOT telegraph
                self.assertEqual(action["type"], "skill")

        # Case 2: RNG Succeeds
        # Call 1: Skill Chance (1) - Pass
        # Call 2: Telegraph Chance (50) - Pass
        with patch("random.randint", side_effect=[1, 50]):
             with patch("random.choice", return_value=self.medium_skill):
                action = MonsterAI.choose_action(self.monster, 1000, 100)
                self.assertEqual(action["type"], "telegraph")

    def test_perfect_guard_mechanic(self):
        """
        Verify that defending against an 'execute_charge' action results in
        70% damage reduction and MP restoration.
        """
        # Simulate that monster has already telegraphed and is now executing
        execute_action = {"type": "execute_charge", "skill": self.ultimate_skill}

        # Setup monster state
        self.monster["charged_skill"] = self.ultimate_skill

        # Setup engine with player defending
        # We give player 50 MP (Max 100) to verify MP gain
        stats_dict = {"MP": 100, "HP": 500, "END": 10, "AGI": 10, "STR": 10, "DEX": 10, "MAG": 10}

        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value=execute_action):
            engine = CombatEngine(
                player=self.player_wrapper,
                monster=self.monster,
                player_skills=[],
                player_mp=50,
                player_class_id=1,
                stats_dict=stats_dict,
                action="defend" # Player chooses to DEFEND
            )

            # Mock RNG for damage formula
            with patch("random.random", return_value=0.5):
                with patch("random.uniform", return_value=1.0):
                    # We need to ensure DamageFormula returns a known damage value
                    # Mocking DamageFormula.monster_skill is easiest
                    with patch("game_systems.combat.damage_formula.DamageFormula.monster_skill") as mock_dmg:
                        # Return 100 damage, no crit, normal hit
                        mock_dmg.return_value = (100, False, "hit")

                        result = engine.run_combat_turn()

        # ASSERTIONS

        # 1. Damage should be 30 (100 * 0.3)
        self.assertEqual(result["turn_report"]["damage_taken"], 30, "Perfect Guard should reduce damage by 70%")

        # 2. MP should be restored
        # Gain 10% of Max MP (100) = 10 MP. Initial 50 + 5 (from normal defend) + 10 (perfect guard)?
        # Wait, normal defend logic in CombatEngine is:
        # if action == "defend": regen = 5% max_mp.
        # But here run_combat_turn processes Player Turn first, THEN Monster Turn.
        # Player Turn: +5 MP (50 -> 55).
        # Monster Turn (execute_charge): +10 MP (10% max).
        # Total should be 50 + 5 + 10 = 65.

        self.assertEqual(result["mp_current"], 65, "MP should recover by 5% (Base) + 10% (Perfect Guard)")

        # 3. Log verification
        log_str = " ".join(result["phrases"])
        self.assertIn("Perfect Guard!", log_str)

    def test_adventure_embed_warning(self):
        """
        Verify the Embed logic shows the new scary warning.
        """
        # Setup monster with charged skill
        self.monster["charged_skill"] = self.ultimate_skill

        embed = AdventureEmbeds.build_exploration_embed(
            location_id="test_loc",
            log=["Test Log"],
            player_stats=self.stats,
            vitals={"current_hp": 500, "current_mp": 100},
            active_monster=self.monster
        )

        # Inspect add_field calls on the mock object
        found_call = False
        for call in embed.add_field.call_args_list:
            name = call.kwargs.get('name', '')
            value = call.kwargs.get('value', '')
            if "VS. Void Lord" in name:
                found_call = True
                self.assertIn("DANGER: CHARGING ULTIMATE DOOM", value)
                self.assertIn("DEFEND NOW!", value)

        self.assertTrue(found_call, "Monster status field call not found")

if __name__ == "__main__":
    unittest.main()
