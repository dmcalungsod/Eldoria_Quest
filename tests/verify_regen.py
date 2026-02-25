import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure root dir is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager


class TestPassiveRegen(unittest.TestCase):
    def setUp(self):
        # Patch pymongo to avoid connection attempt in __init__
        with patch("pymongo.MongoClient"):
            self.db = DatabaseManager(db_name="test_db")

        # Mock the collection accessor
        self.db.db = MagicMock()
        self.players_col = MagicMock()
        self.db.db.__getitem__.return_value = self.players_col

        # Mock _col helper
        self.db._col = MagicMock(return_value=self.players_col)

    def test_apply_passive_regen(self):
        discord_id = 12345
        now = datetime.datetime(2023, 1, 1, 12, 0, 0)

        # Mock WorldTime.now to return fixed time
        with patch("game_systems.core.world_time.WorldTime.now", return_value=now):
            # Scenario: Player has 1 HP, 1 MP. Last regen was 2 hours ago.
            last_regen = now - datetime.timedelta(hours=2)

            player_data = {"current_hp": 1, "current_mp": 1, "last_regen_time": last_regen.isoformat()}

            # Mock find_one to return player
            self.players_col.find_one.return_value = player_data

            # Mock get_player_stats_json
            # Max HP 100, Max MP 50
            stats_json = {
                "STR": {"base": 10},
                "END": {"base": 10},
                "DEX": {"base": 10},
                "AGI": {"base": 10},
                "MAG": {"base": 10},
                "LCK": {"base": 10},
            }
            # Wait, PlayerStats calculates Max HP/MP based on stats.
            # END 10 -> Tier 1 bonus?
            # Let's mock PlayerStats.from_dict to return fixed max values to simplify test

            mock_stats = MagicMock()
            mock_stats.max_hp = 100
            mock_stats.max_mp = 50

            with patch("game_systems.player.player_stats.PlayerStats.from_dict", return_value=mock_stats):
                with patch.object(self.db, "get_player_stats_json", return_value=stats_json):
                    # Act
                    healed_hp, healed_mp = self.db.apply_passive_regen(discord_id)

                    # Assert
                    # 2 hours elapsed.
                    # HP Regen: 5% * 100 * 2 = 10 HP.
                    # MP Regen: 10% * 50 * 2 = 10 MP.

                    self.assertEqual(healed_hp, 10)
                    self.assertEqual(healed_mp, 10)

                    # Verify Update Call
                    # New HP: 1 + 10 = 11
                    # New MP: 1 + 10 = 11
                    self.players_col.update_one.assert_called()
                    call_args = self.players_col.update_one.call_args

                    # Args: (filter, update)
                    filter_arg = call_args[0][0]
                    update_arg = call_args[0][1]

                    self.assertEqual(filter_arg, {"discord_id": discord_id})
                    self.assertEqual(update_arg["$set"]["current_hp"], 11)
                    self.assertEqual(update_arg["$set"]["current_mp"], 11)
                    self.assertEqual(update_arg["$set"]["last_regen_time"], now.isoformat())

                    print(f"Verified Regen: +{healed_hp} HP, +{healed_mp} MP")


if __name__ == "__main__":
    unittest.main()
