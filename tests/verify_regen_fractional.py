import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure root dir is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager


class TestPassiveRegenFractional(unittest.TestCase):
    def setUp(self):
        with patch("pymongo.MongoClient"):
            self.db = DatabaseManager(db_name="test_db")

        self.db.db = MagicMock()
        self.players_col = MagicMock()
        self.db.db.__getitem__.return_value = self.players_col
        self.db._col = MagicMock(return_value=self.players_col)

    def test_fractional_regen_does_not_reset_timer(self):
        discord_id = 12345
        now = datetime.datetime(2023, 1, 1, 12, 0, 0)

        with patch("game_systems.core.world_time.WorldTime.now", return_value=now):
            # Scenario: 5 minutes elapsed.
            # Max HP 100.
            # 5 minutes = 5/60 hours = 0.0833 hours.
            # Regen = 100 * 0.05 * 0.0833 = 0.41 HP -> 0 HP (int).

            last_regen = now - datetime.timedelta(minutes=5)

            player_data = {"current_hp": 50, "current_mp": 50, "last_regen_time": last_regen.isoformat()}

            self.players_col.find_one.return_value = player_data

            mock_stats = MagicMock()
            mock_stats.max_hp = 100
            mock_stats.max_mp = 100

            stats_json = {}

            with patch("game_systems.player.player_stats.PlayerStats.from_dict", return_value=mock_stats):
                with patch.object(self.db, "get_player_stats_json", return_value=stats_json):
                    # Act
                    healed_hp, healed_mp = self.db.apply_passive_regen(discord_id)

                    # Assert
                    self.assertEqual(healed_hp, 0, "Should not heal fractional HP")

                    # Verify update_one was NOT called
                    self.players_col.update_one.assert_not_called()

                    print("Verified: Fractional regen did not reset timer.")


if __name__ == "__main__":
    unittest.main()
