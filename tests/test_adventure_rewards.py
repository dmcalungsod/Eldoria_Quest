"""
Adventure Rewards Tests
-----------------------
Tests the regression of reward distribution logic:
- Stat XP calculation formulas
- Skill XP calculation
- Loot and Quest processing
"""

import importlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAdventureRewards(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ext"] = MagicMock()

        # Import modules under test
        import database.database_manager

        importlib.reload(database.database_manager)
        self.DatabaseManager = database.database_manager.DatabaseManager

        import game_systems.adventure.adventure_rewards

        importlib.reload(game_systems.adventure.adventure_rewards)
        self.AdventureRewards = game_systems.adventure.adventure_rewards.AdventureRewards

        import game_systems.items.inventory_manager

        importlib.reload(game_systems.items.inventory_manager)
        self.InventoryManager = game_systems.items.inventory_manager.InventoryManager

        # Additional mocks needed for AdventureRewards
        self.mock_db = MagicMock(spec=self.DatabaseManager)
        self.discord_id = 12345
        self.rewards_system = self.AdventureRewards(self.mock_db, self.discord_id)

        # Mock internal systems
        self.rewards_system.rank_system = MagicMock()
        self.rewards_system.achievement_system = MagicMock()
        self.rewards_system.faction_system = MagicMock()
        self.rewards_system.faction_system.grant_reputation_for_kill.return_value = []
        self.rewards_system.achievement_system.check_kill_achievements.return_value = None
        self.rewards_system.achievement_system.check_group_achievements.return_value = None
        self.rewards_system.rank_system.finalize_promotion.return_value = (False, "")

    def tearDown(self):
        self.modules_patcher.stop()

    def test_process_victory_stat_xp(self):
        """
        Verify that stat XP is calculated correctly based on battle report.
        Formulas:
        - END: hits_taken + (damage_taken * 0.1)
        - LCK: 0.5 + (crit * 0.5) + (dodge * 0.5)
        - DEX: (dex_hits * 0.5) + (crit * 2.0)
        - AGI: dodge * 1.5
        - STR: str_hits * 0.5
        - MAG: mag_hits * 1.0
        """
        # Mock battle report
        battle_report = {
            "hits_taken": 10,
            "damage_taken": 100,
            "player_crit": 2,
            "player_dodge": 4,
            "dex_hits": 6,
            "str_hits": 8,
            "mag_hits": 5,
        }

        # Expected gains:
        # END: 10 + (100 * 0.1) = 20.0
        # LCK: 0.5 + (2 * 0.5) + (4 * 0.5) = 0.5 + 1.0 + 2.0 = 3.5
        # DEX: (6 * 0.5) + (2 * 2.0) = 3.0 + 4.0 = 7.0
        # AGI: 4 * 1.5 = 6.0
        # STR: 8 * 0.5 = 4.0
        # MAG: 5 * 1.0 = 5.0

        # Mock DB state
        # Initial stats
        stats_json = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
        }

        # Current XP (all 0)
        self.mock_db.get_stat_exp_row.return_value = {
            "stats_json": json.dumps(stats_json),
            "str_exp": 0,
            "end_exp": 0,
            "dex_exp": 0,
            "agi_exp": 0,
            "mag_exp": 0,
            "lck_exp": 0,
        }

        # Mock combat result and other args for process_victory
        combat_result = {
            "exp": 100,
            "monster_data": {"name": "Test Monster", "tier": "Normal"},
            "drops": [],
            "active_boosts": {},
        }
        quest_system = MagicMock()
        quest_system.get_player_quests.return_value = []
        inv_manager = MagicMock()
        session_loot = {}

        # Mock optimistic locking success
        self.mock_db.update_stat_exp.return_value = True

        # Run process_victory
        with patch(
            "game_systems.rewards.loot_calculator.LootCalculator.roll_drops",
            return_value=[],
        ):
            self.rewards_system.process_victory(
                battle_report,
                [],
                combat_result,
                quest_system,
                inv_manager,
                session_loot,
            )

        # Verify DB update call
        args = self.mock_db.update_stat_exp.call_args
        self.assertIsNotNone(args)

        # update_stat_exp(discord_id, old_stats_json, old_exps, stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp)
        call_args = args.args
        self.assertEqual(call_args[0], self.discord_id)

        # Verify old_stats_json passed (index 1)
        self.assertEqual(call_args[1], json.dumps(stats_json))

        # Verify old_exps passed (index 2)
        # We mocked get_stat_exp_row to return 0 for all exp values
        expected_old_exps = {
            "str_exp": 0, "end_exp": 0, "dex_exp": 0,
            "agi_exp": 0, "mag_exp": 0, "lck_exp": 0
        }
        self.assertEqual(call_args[2], expected_old_exps)

        # Check XP values (indices 4-9 correspond to str, end, dex, agi, mag, lck)
        self.assertEqual(call_args[4], 4.0, "STR XP mismatch")
        self.assertEqual(call_args[5], 20.0, "END XP mismatch")
        self.assertEqual(call_args[6], 7.0, "DEX XP mismatch")
        self.assertEqual(call_args[7], 6.0, "AGI XP mismatch")
        self.assertEqual(call_args[8], 5.0, "MAG XP mismatch")
        self.assertEqual(call_args[9], 3.5, "LCK XP mismatch")

    def test_process_victory_skill_xp(self):
        """Verify skill XP increments based on usage."""
        report_list = [
            {"skill_key_used": "slash"},
            {"skill_key_used": "slash"},
            {"skill_key_used": "fireball"},
        ]

        # Mock DB return for skills
        def get_skill_side_effect(discord_id, skill_key):
            if skill_key == "slash":
                return {"skill_level": 1, "skill_exp": 0, "name": "Slash"}
            if skill_key == "fireball":
                return {
                    "skill_level": 1,
                    "skill_exp": 99,
                    "name": "Fireball",
                }  # Nearly level up
            return None

        self.mock_db.get_skill_with_definition.side_effect = get_skill_side_effect

        # Mock other systems
        combat_result = {
            "exp": 100,
            "monster_data": {"name": "Test Monster", "tier": "Normal"},
            "drops": [],
        }
        quest_system = MagicMock()
        quest_system.get_player_quests.return_value = []
        inv_manager = MagicMock()
        session_loot = {}

        # We need to mock get_stat_exp_row to avoid errors in stat processing
        self.mock_db.get_stat_exp_row.return_value = None  # Skip stat processing

        with patch(
            "game_systems.rewards.loot_calculator.LootCalculator.roll_drops",
            return_value=[],
        ):
            self.rewards_system.process_victory({}, report_list, combat_result, quest_system, inv_manager, session_loot)

        # Verify Slash: used 2 times. 2 * 2.5 = 5.0 XP. No level up.
        # Verify Fireball: used 1 time. 1 * 2.5 = 2.5 XP. 99 + 2.5 = 101.5. Level up!

        # Check calls to update_player_skill
        calls = self.mock_db.update_player_skill.call_args_list

        slash_call = next((c for c in calls if c.args[1] == "slash"), None)
        fireball_call = next((c for c in calls if c.args[1] == "fireball"), None)

        self.assertIsNotNone(slash_call)
        self.assertEqual(slash_call.kwargs["skill_level"], 1)
        self.assertEqual(slash_call.kwargs["skill_exp"], 5.0)

        self.assertIsNotNone(fireball_call)
        # Threshold is 100. 101.5 - 100 = 1.5 exp. Level 1 -> 2.
        self.assertEqual(fireball_call.kwargs["skill_level"], 2)
        self.assertEqual(fireball_call.kwargs["skill_exp"], 1.5)

    def test_process_victory_loot_and_quests(self):
        """Verify loot is added and quests updated."""
        # Mock drops
        combat_result = {
            "exp": 100,
            "monster_data": {"name": "Goblin", "tier": "Normal"},
            "drops": [{"name": "Goblin Ear", "rate": 1.0}],
            "active_boosts": {},
        }

        # LootCalculator returns "Goblin Ear"
        with patch(
            "game_systems.rewards.loot_calculator.LootCalculator.roll_drops",
            return_value=["Goblin Ear"],
        ):
            with patch(
                "game_systems.adventure.adventure_rewards.MATERIALS",
                {"Goblin Ear": {"rarity": "Common", "name": "Goblin Ear"}},
            ):
                # Mock Inventory
                inv_manager = MagicMock()

                # Mock Quest
                quest_system = MagicMock()
                quest_system.get_player_quests.return_value = [
                    {
                        "id": "q1",
                        "title": "Hunt Goblins",
                        "objectives": {"defeat": ["Goblin"], "collect": ["Goblin Ear"]},
                    }
                ]

                # Mock DB
                self.mock_db.get_stat_exp_row.return_value = None
                self.mock_db.get_player_stats_json.return_value = {
                    "LUCK": 10
                }  # Needed for LootCalculator call in actual code

                session_loot = {}

                logs = self.rewards_system.process_victory(
                    {}, [], combat_result, quest_system, inv_manager, session_loot
                )

                # Verify Session Loot
                self.assertEqual(session_loot["exp"], 100)
                self.assertEqual(session_loot["Goblin Ear"], 1)

                # Verify Quest Updates
                # Should update for defeat
                quest_system.update_progress.assert_any_call(self.discord_id, "q1", "defeat", "Goblin")
                # Should update for collect
                quest_system.update_progress.assert_any_call(self.discord_id, "q1", "collect", "Goblin Ear")

                # Verify Logs contain loot
                self.assertTrue(any("Goblin Ear" in log for log in logs))


if __name__ == "__main__":
    unittest.main()
