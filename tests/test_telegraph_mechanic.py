import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies
sys.modules["pymongo"] = MagicMock()
sys.modules["discord"] = MagicMock()

from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.monsters.monster_actions import MonsterAI  # noqa: E402
from game_systems.player.level_up import LevelUpSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestTelegraphMechanic(unittest.TestCase):
    def setUp(self):
        self.stats = PlayerStats(str_base=10, end_base=10, dex_base=10, agi_base=10, mag_base=10)
        self.player_wrapper = MagicMock(spec=LevelUpSystem)
        self.player_wrapper.stats = self.stats
        self.player_wrapper.level = 1
        self.player_wrapper.hp_current = 500
        self.player_wrapper.hp_max = 500
        self.player_wrapper.add_exp = MagicMock(return_value=False)

        # High Power Skill
        self.high_power_skill = {
            "key_id": "annihilate",
            "name": "Annihilate",
            "power": 2.5,
            "mp_cost": 0,
            "type": "magical",
            "desc_key": "magic",
        }

        self.monster = {
            "name": "Void Dragon",
            "HP": 1000,
            "max_hp": 1000,
            "MP": 100,
            "ATK": 50,
            "DEF": 10,
            "level": 10,
            "tier": "Boss",
            "skills": [self.high_power_skill],
        }

    def test_telegraph_execution_flow(self):
        """
        Test the full flow: Telegraph -> No Damage -> Execute Charge -> Damage.
        """
        # 1. Test "Telegraph" Turn
        # We manually inject the action to test the ENGINE'S handling
        telegraph_action = {"type": "telegraph", "skill": self.high_power_skill}

        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value=telegraph_action):
            engine = CombatEngine(
                player=self.player_wrapper,
                monster=self.monster,
                player_skills=[],
                player_mp=100,
                player_class_id=1,
                stats_dict={"MP": 100, "HP": 500, "END": 10, "AGI": 10},
                action="defend",  # Player defends in anticipation
            )

            # Mock RNG
            with patch("random.random", return_value=0.5):
                with patch("random.uniform", return_value=1.0):
                    result = engine.run_combat_turn()

            # ASSERTIONS FOR TELEGRAPH
            # 1. No damage should be taken
            self.assertEqual(result["turn_report"]["damage_taken"], 0, "Telegraph turn should deal 0 damage")

            # 2. Monster should have charged_skill set
            self.assertIn("charged_skill", self.monster)
            self.assertEqual(self.monster["charged_skill"], self.high_power_skill)

            # 3. Log should contain warning
            log_str = " ".join(result["phrases"])
            # Updated to match new CombatPhrases
            self.assertTrue(
                "gathering dark energy" in log_str or "Dark energy gathers" in log_str or "INTERRUPT" in log_str
            )
            self.assertIn("Annihilate", log_str)

        # 2. Test "Execute Charge" Turn
        # Now the monster has "charged_skill" set.
        # We test that MonsterAI detects this and returns "execute_charge"

        # Verify MonsterAI.choose_action returns execute_charge
        action = MonsterAI.choose_action(self.monster, 1000, 100)
        self.assertEqual(
            action["type"], "execute_charge", "MonsterAI should choose execute_charge when charged_skill is present"
        )
        self.assertEqual(action["skill"], self.high_power_skill)

        # Now run the engine with this action
        with patch("game_systems.monsters.monster_actions.MonsterAI.choose_action", return_value=action):
            engine = CombatEngine(
                player=self.player_wrapper,
                monster=self.monster,
                player_skills=[],
                player_mp=100,
                player_class_id=1,
                stats_dict={"MP": 100, "HP": 500, "END": 10, "AGI": 10},
                action="defend",
            )

            with patch("random.random", return_value=0.5):
                with patch("random.uniform", return_value=1.0):
                    result = engine.run_combat_turn()

            # ASSERTIONS FOR EXECUTION
            # 1. Damage should be taken
            self.assertTrue(result["turn_report"]["damage_taken"] > 0, "Execute charge should deal damage")

            # 2. Monster should NO LONGER have charged_skill
            self.assertNotIn("charged_skill", self.monster)

            # 3. Log should contain unleash message
            log_str = " ".join(result["phrases"])
            self.assertIn("unleashes **Annihilate**", log_str)

    def test_monster_ai_telegraph_chance(self):
        """
        Test that MonsterAI *can* choose telegraph for high power skills.
        """
        # Force RNG to trigger telegraph (chance is 50%)
        # Logic: if power >= 1.8 -> Always telegraph
        # Logic: if power >= 1.4 -> 50% chance

        # We need to control random.randint calls.
        # 1. Skill chance (<= 70 for Boss) -> Let's say 1 (Success)
        # Note: Since power is 2.5, it auto-telegraphs without a second roll.

        with patch("random.randint", side_effect=[1]):
            # First call: Skill Chance (1 <= 70)

            # Note: random.choice is also called to pick skill.
            # We have only 1 skill, so it picks it.

            action = MonsterAI.choose_action(self.monster, 1000, 100)

            self.assertEqual(action["type"], "telegraph", "MonsterAI should choose telegraph with correct RNG")
            self.assertEqual(action["skill"], self.high_power_skill)


if __name__ == "__main__":
    unittest.main()
