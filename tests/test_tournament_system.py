import unittest
from unittest.mock import MagicMock, patch
import datetime
import sys
import os

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo before importing DatabaseManager
# This is required because the pytest environment does not have pymongo installed,
# and DatabaseManager imports it at the module level.
sys.modules["pymongo"] = MagicMock()

from game_systems.guild_system.tournament_system import TournamentSystem  # noqa: E402

class TestTournamentSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = TournamentSystem(self.mock_db)

    def test_start_weekly_tournament_creates_new(self):
        # Setup: No active tournament
        self.mock_db.get_active_tournament.return_value = None
        self.mock_db.create_tournament.return_value = 101

        # Execute
        t_id = self.system.start_weekly_tournament()

        # Verify
        self.assertEqual(t_id, 101)
        self.mock_db.create_tournament.assert_called_once()
        args = self.mock_db.create_tournament.call_args_list[0]
        # In python 3.8+ call_args is a tuple (args, kwargs) or just use .args
        # checking args
        created_type = args.kwargs.get('type')
        self.assertIn(created_type, self.system.TOURNAMENT_TYPES)

    def test_start_weekly_tournament_returns_existing(self):
        # Setup: Active tournament exists and is valid
        future_end = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
        self.mock_db.get_active_tournament.return_value = {
            "id": 50, "type": "monster_kills", "end_time": future_end
        }

        # Execute
        t_id = self.system.start_weekly_tournament()

        # Verify
        self.assertEqual(t_id, 50)
        self.mock_db.create_tournament.assert_not_called()

    def test_record_action_updates_score(self):
        # Setup: Active tournament matches action
        future_end = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
        self.mock_db.get_active_tournament.return_value = {
            "id": 50, "type": "monster_kills", "end_time": future_end
        }

        # Execute
        self.system.record_action(12345, "monster_kills", 5)

        # Verify
        self.mock_db.update_tournament_score.assert_called_once_with(12345, 50, 5)

    def test_record_action_ignores_mismatch(self):
        # Setup: Active tournament is quests, action is kills
        future_end = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
        self.mock_db.get_active_tournament.return_value = {
            "id": 50, "type": "quests_completed", "end_time": future_end
        }

        # Execute
        self.system.record_action(12345, "monster_kills", 1)

        # Verify
        self.mock_db.update_tournament_score.assert_not_called()

    def test_end_current_tournament_distributes_rewards(self):
        # Setup: Active tournament
        self.mock_db.get_active_tournament.return_value = {
            "id": 50, "type": "monster_kills"
        }
        # Mock leaderboard
        self.mock_db.get_tournament_leaderboard.return_value = [
            {"discord_id": 1, "score": 100, "name": "Player1"},
            {"discord_id": 2, "score": 80, "name": "Player2"},
        ]

        # Execute
        result = self.system.end_current_tournament()

        # Verify
        self.mock_db.increment_player_fields.assert_any_call(1, aurum=1000) # Rank 1
        self.mock_db.increment_player_fields.assert_any_call(2, aurum=500)  # Rank 2
        self.mock_db.add_title.assert_called_with(1, "Grand Champion")
        self.mock_db.end_active_tournament.assert_called_once()
        self.assertIn("Player1", result)

if __name__ == '__main__':
    unittest.main()
