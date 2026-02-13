import sys
import os
import unittest
sys.path.append(os.getcwd())
from unittest.mock import MagicMock, patch
import json
import sqlite3

# --- MOCK DISCORD ---
class MockView:
    def __init__(self, timeout=180):
        pass
    def add_item(self, item):
        pass
    def clear_items(self):
        pass

class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.callback = None
        self.label = label

discord = MagicMock()
discord.ui.View = MockView
discord.ui.Button = MockButton
discord.ButtonStyle = MagicMock()
discord.User = MagicMock()
discord.Embed = MagicMock()
discord.Color = MagicMock()

sys.modules["discord"] = discord
sys.modules["discord.ui"] = discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# --- IMPORT MODULE UNDER TEST ---
from cogs.infirmary_cog import InfirmaryView
from game_systems.player.player_stats import PlayerStats

class TestInfirmaryStateIssue(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager
        self.db = MagicMock()
        self.conn = MagicMock()
        self.db.get_connection.return_value.__enter__.return_value = self.conn

        # Setup User
        self.user = MagicMock()
        self.user.id = 12345

        # Initial Player Data
        self.initial_p_data = {
            "current_hp": 50,
            "current_mp": 10,
            "aurum": 1000
        }

        # Initial Stats (Max HP 150 based on base stats logic in PlayerStats)
        # PlayerStats(str_base=10, end_base=10) -> HP = 50 + (10 * 10) = 150
        self.initial_stats = PlayerStats(str_base=10, end_base=10)

    def test_stale_stats_healing(self):
        """
        Scenario:
        1. View initialized with Max HP 150.
        2. Player changes gear/buffs, Max HP becomes 200 in DB (simulated).
        3. User clicks Heal.
        4. View SHOULD heal to 200 (Fresh), but due to bug heals to 150 (Stale).
        """

        # 1. Initialize View with initial stats (Max HP 150)
        view = InfirmaryView(self.db, self.user, self.initial_p_data, self.initial_stats)

        old_max_hp = self.initial_stats.max_hp # 150
        new_max_hp = 200 # Simulated new Max HP in DB

        print(f"View initialized with Max HP: {old_max_hp}")

        # 2. Simulate DB state where player has changed

        # Mock the fetchone for player vitals
        self.conn.execute.return_value.fetchone.side_effect = [
            # First call: fetch player vitals
            {
                "current_hp": 50,
                "current_mp": 10,
                "aurum": 1000
            },
            # Second call: fetch stats_json (THIS IS WHAT WE WILL ADD)
            {
                "stats_json": json.dumps({
                    "STR": {"base": 10, "bonus": 0},
                    "END": {"base": 15, "bonus": 0}, # Increased END -> Higher HP
                    # END 15 -> HP = 50 + (15 * 10) = 200
                })
            }
        ]

        # 3. Call _execute_heal
        # Currently, the code won't make the second call, so side_effect might raise StopIteration if called twice,
        # or just return the first one if called once.
        # But we mocked side_effect list. If the code only calls fetchone once, it consumes first item.

        view._execute_heal()

        # 4. Verify UPDATE
        args_list = self.conn.execute.call_args_list
        # We expect at least one UPDATE
        update_call = [call for call in args_list if "UPDATE players SET" in call[0][0]]

        self.assertTrue(update_call, "No UPDATE statement executed!")

        # call object is (args, kwargs)
        # args is (sql, params)
        args = update_call[0][0]
        sql = args[0]
        params = args[1]

        # params: (new_hp, new_mp, new_aurum, discord_id)
        # We expect new_hp to be new_max_hp (200)

        # If bug exists, params[0] == old_max_hp (150)
        # If fix works, params[0] == new_max_hp (200)

        self.assertEqual(params[0], new_max_hp,
            f"Vulnerability Found: Healed to {params[0]} (Stale), expected {new_max_hp} (Fresh DB State)")

def run_all_tests():
    """Run the infirmary security test suite manually."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInfirmaryStateIssue)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    unittest.main()
