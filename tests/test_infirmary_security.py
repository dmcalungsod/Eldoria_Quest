import os
import sys
import unittest

sys.path.append(os.getcwd())
import json
from unittest.mock import MagicMock


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
from cogs.infirmary_cog import InfirmaryView  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestInfirmaryStateIssue(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager
        self.db = MagicMock()
        # With new DatabaseManager, get_connection yields self
        self.db.get_connection.return_value.__enter__.return_value = self.db

        # Mock collection access
        self.players_col = MagicMock()
        self.stats_col = MagicMock()

        def mock_col(name):
            if name == "players":
                return self.players_col
            if name == "stats":
                return self.stats_col
            return MagicMock()

        self.db._col.side_effect = mock_col

        # Setup User
        self.user = MagicMock()
        self.user.id = 12345

        # Initial Player Data
        self.initial_p_data = {"current_hp": 50, "current_mp": 10, "aurum": 1000}

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

        old_max_hp = self.initial_stats.max_hp  # 150
        new_max_hp = 200  # Simulated new Max HP in DB

        print(f"View initialized with Max HP: {old_max_hp}")

        # 2. Simulate DB state where player has changed

        # Mock player fetch
        self.players_col.find_one.return_value = {"current_hp": 50, "current_mp": 10, "aurum": 1000}

        # Mock stats fetch
        self.stats_col.find_one.return_value = {
            "stats_json": json.dumps(
                {
                    "STR": {"base": 10, "bonus": 0},
                    "END": {"base": 15, "bonus": 0},  # Increased END -> Higher HP
                    # END 15 -> HP = 50 + (15 * 10) = 200
                }
            )
        }

        # 3. Call _execute_heal
        # Currently, the code won't make the second call, so side_effect might raise StopIteration if called twice,
        # or just return the first one if called once.
        # But we mocked side_effect list. If the code only calls fetchone once, it consumes first item.

        view._execute_heal()

        # 4. Verify UPDATE
        # Expect players_col.update_one call
        # args: (filter, update)
        update_calls = self.players_col.update_one.call_args_list
        self.assertTrue(update_calls, "No UPDATE executed!")

        # Get the update dict from the first call
        # update_one(filter, update_dict)
        update_arg = update_calls[0][0][1]
        set_dict = update_arg.get("$set", {})

        healed_hp = set_dict.get("current_hp")

        self.assertEqual(
            healed_hp,
            new_max_hp,
            f"Vulnerability Found: Healed to {healed_hp} (Stale), expected {new_max_hp} (Fresh DB State)",
        )


def run_all_tests():
    """Run the infirmary security test suite manually."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestInfirmaryStateIssue)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
