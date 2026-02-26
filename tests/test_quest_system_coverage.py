import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.data.emojis import ERROR, WARNING  # noqa: E402
from game_systems.guild_system.quest_system import QuestSystem  # noqa: E402


class TestQuestSystemCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()

        # Patch RewardSystem and TournamentSystem internally used by QuestSystem
        import game_systems.guild_system.quest_system

        patcher_reward = patch.object(game_systems.guild_system.quest_system, "RewardSystem")
        self.mock_reward_sys_class = patcher_reward.start()
        self.mock_reward_sys = self.mock_reward_sys_class.return_value
        self.addCleanup(patcher_reward.stop)

        patcher_tournament = patch.object(game_systems.guild_system.quest_system, "TournamentSystem")
        self.mock_tournament_sys_class = patcher_tournament.start()
        self.mock_tournament_sys = self.mock_tournament_sys_class.return_value
        self.addCleanup(patcher_tournament.stop)

        self.quest_system = QuestSystem(self.mock_db)
        self.user_id = 999
        self.mock_col = MagicMock()
        self.mock_db._col.return_value = self.mock_col

    # --- test get_available_quests ---
    def test_get_available_quests_no_rank(self):
        self.mock_db.get_guild_member_field.return_value = None
        self.assertEqual(self.quest_system.get_available_quests(self.user_id), [])

    def test_get_available_quests_unknown_rank(self):
        # Rank not in the predefined list
        self.mock_db.get_guild_member_field.return_value = "Z_RANK"
        self.mock_db.get_player_quest_ids.return_value = []

        self.mock_col.find.side_effect = [
            [
                {
                    "id": 1,
                    "tier": "Z_RANK",
                    "summary": "Unknown tier quest",
                    "exclusive_group": None,
                    "prerequisites": None,
                }
            ],  # Quests collection
            [],  # Player quests collection
        ]

        available = self.quest_system.get_available_quests(self.user_id)
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]["id"], 1)

    def test_get_available_quests_single_int_prereq_unmet(self):
        self.mock_db.get_guild_member_field.return_value = "F"
        self.mock_db.get_player_quest_ids.return_value = []

        self.mock_col.find.side_effect = [
            [{"id": 2, "tier": "F", "summary": "...", "exclusive_group": None, "prerequisites": 1}],
            [],  # Player has 0 completed quests
        ]

        available = self.quest_system.get_available_quests(self.user_id)
        self.assertEqual(len(available), 0)  # Misses prerequisite

    def test_get_available_quests_exception(self):
        self.mock_db.get_guild_member_field.side_effect = Exception("DB Down")
        self.assertEqual(self.quest_system.get_available_quests(self.user_id), [])

    # --- test get_quest_details ---
    def test_get_quest_details_found_dict_objectives(self):
        self.mock_col.find_one.return_value = {
            "id": 10,
            "objectives": {"slay": {"Bat": 5}},  # Already a dict
            "rewards": {"gold": 100},  # Already a dict
        }
        details = self.quest_system.get_quest_details(10)
        self.assertEqual(details["objectives"]["slay"]["Bat"], 5)
        self.assertEqual(details["rewards"]["gold"], 100)

    def test_get_quest_details_not_found(self):
        self.mock_col.find_one.return_value = None
        self.assertIsNone(self.quest_system.get_quest_details(99))

    def test_get_quest_details_malformed_json(self):
        self.mock_col.find_one.return_value = {"id": 11, "objectives": "{bad_json", "rewards": "bad_json}"}
        details = self.quest_system.get_quest_details(11)
        self.assertEqual(details["objectives"], {})
        self.assertEqual(details["rewards"], {})

    def test_get_quest_details_exception(self):
        self.mock_col.find_one.side_effect = Exception("DB Down")
        self.assertIsNone(self.quest_system.get_quest_details(10))

    # --- test get_player_quests ---
    def test_get_player_quests_success(self):
        self.mock_col.find.return_value = [
            {"quest_id": 15, "status": "in_progress", "progress": '{"slay": {"Bat": 2}}'}
        ]
        # find_one is called inside the loop for each quest
        self.mock_col.find_one.return_value = {"id": 15, "title": "Bat Hunt", "objectives": '{"slay": {"Bat": 5}}'}

        quests = self.quest_system.get_player_quests(self.user_id)
        self.assertEqual(len(quests), 1)
        self.assertEqual(quests[0]["id"], 15)
        self.assertEqual(quests[0]["progress"], {"slay": {"Bat": 2}})
        self.assertEqual(quests[0]["objectives"], {"slay": {"Bat": 5}})

    def test_get_player_quests_missing_quest_def(self):
        self.mock_col.find.return_value = [{"quest_id": 16, "status": "in_progress", "progress": "{}"}]
        self.mock_col.find_one.return_value = None  # Quest definition deleted?

        quests = self.quest_system.get_player_quests(self.user_id)
        self.assertEqual(quests, [])

    def test_get_player_quests_malformed_json(self):
        self.mock_col.find.return_value = [{"quest_id": 17, "status": "in_progress", "progress": "{bad"}]
        self.mock_col.find_one.return_value = {"id": 17, "title": "Test", "objectives": "also bad}"}

        quests = self.quest_system.get_player_quests(self.user_id)
        self.assertEqual(len(quests), 1)
        self.assertEqual(quests[0]["progress"], {})
        self.assertEqual(quests[0]["objectives"], {})

    def test_get_player_quests_exception(self):
        self.mock_col.find.side_effect = Exception("Query Failed")
        self.assertEqual(self.quest_system.get_player_quests(self.user_id), [])

    # --- test update_progress ---
    def test_update_progress_success(self):
        self.mock_col.find_one.return_value = {"progress": '{"slay": {"Wolf": 1}}'}

        res = self.quest_system.update_progress(self.user_id, 20, "slay", "Wolf", 2)
        self.assertTrue(res)
        self.mock_col.update_one.assert_called_once()
        args, kwargs = self.mock_col.update_one.call_args

        # Check what was passed to update_one
        passed_update = kwargs.get("update") or (args[1] if len(args) > 1 else {})
        set_op = passed_update.get("$set", {})
        progress_str = set_op.get("progress", "")

        # Should be updated to 3
        self.assertIn('"Wolf": 3', progress_str)

    def test_update_progress_not_found(self):
        self.mock_col.find_one.return_value = None
        self.assertFalse(self.quest_system.update_progress(self.user_id, 20, "slay", "Wolf"))

    def test_update_progress_bad_json(self):
        self.mock_col.find_one.return_value = {"progress": "{bad"}
        self.assertFalse(self.quest_system.update_progress(self.user_id, 20, "slay", "Wolf"))

    def test_update_progress_target_not_present(self):
        self.mock_col.find_one.return_value = {"progress": '{"slay": {"Bear": 0}}'}
        # Trying to update "Wolf" when progress tracks "Bear"
        self.assertFalse(self.quest_system.update_progress(self.user_id, 20, "slay", "Wolf"))

    def test_update_progress_exception(self):
        self.mock_col.find_one.side_effect = Exception("DB")
        self.assertFalse(self.quest_system.update_progress(self.user_id, 20, "slay", "Wolf"))

    # --- test complete_quest ---
    def test_complete_quest_success(self):
        # 1. Active Quest found
        # 2. Quest definition found
        self.mock_col.find_one.side_effect = [
            {"progress": '{"slay": {"Wolf": 5}}'},
            {"objectives": '{"slay": {"Wolf": 5}}', "rewards": '{"gold": 10}'},
        ]

        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_col.update_one.return_value = mock_result

        self.mock_reward_sys.grant_rewards.return_value = "Rewards granted"

        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertTrue(success)
        self.assertNotIn("error", msg.lower())
        self.mock_tournament_sys.record_action.assert_called_with(self.user_id, "quests_completed", 1)

    def test_complete_quest_not_active(self):
        self.mock_col.find_one.return_value = None
        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertFalse(success)
        self.assertIn(ERROR, msg)

    def test_complete_quest_missing_def(self):
        self.mock_col.find_one.side_effect = [{"progress": '{"slay": {"Wolf": 5}}'}, None]
        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertFalse(success)
        self.assertIn("definition not found", msg)

    def test_complete_quest_objectives_not_met(self):
        self.mock_col.find_one.side_effect = [
            {"progress": '{"slay": {"Wolf": 4}}'},  # Only 4/5
            {"objectives": '{"slay": {"Wolf": 5}}', "rewards": '{"gold": 10}'},
        ]
        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertFalse(success)
        self.assertIn(WARNING, msg)
        self.assertIn("not met", msg)

    def test_complete_quest_race_condition(self):
        self.mock_col.find_one.side_effect = [
            {"progress": '{"slay": {"Wolf": 5}}'},
            {"objectives": '{"slay": {"Wolf": 5}}', "rewards": '{"gold": 10}'},
        ]
        # Simulate update_one modifying 0 documents (e.g. status changed in meantime)
        mock_result = MagicMock()
        mock_result.modified_count = 0
        self.mock_col.update_one.return_value = mock_result

        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertFalse(success)
        self.assertIn("already completed", msg)

    def test_complete_quest_tournament_error_caught(self):
        self.mock_col.find_one.side_effect = [
            {"progress": '{"slay": {"Wolf": 5}}'},
            {"objectives": '{"slay": {"Wolf": 5}}', "rewards": '{"gold": 10}'},
        ]
        mock_result = MagicMock()
        mock_result.modified_count = 1
        self.mock_col.update_one.return_value = mock_result
        self.mock_reward_sys.grant_rewards.return_value = "Rewards"

        # Tournament throws error
        self.mock_tournament_sys.record_action.side_effect = Exception("Tournament down")

        # Should still succeed
        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertTrue(success)

    def test_complete_quest_exception(self):
        self.mock_col.find_one.side_effect = Exception("DB Fail")
        success, msg = self.quest_system.complete_quest(self.user_id, 30)
        self.assertFalse(success)
        self.assertIn("System error", msg)

    # --- test check_completion ---
    def test_check_completion_scalar_objective(self):
        # Testing the `else:` branch where tasks is not a dict
        progress = {"explore": {"Cavern": 1}}
        objectives = {"explore": "Cavern"}  # String instead of dict

        self.assertTrue(self.quest_system.check_completion(progress, objectives))

        progress_incomplete = {"explore": {"Cavern": 0}}
        self.assertFalse(self.quest_system.check_completion(progress_incomplete, objectives))

        progress_missing = {}
        self.assertFalse(self.quest_system.check_completion(progress_missing, objectives))


if __name__ == "__main__":
    unittest.main()
