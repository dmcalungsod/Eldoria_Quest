import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.getcwd())


# --- MOCK DISCORD ---
class MockView:
    def __init__(self, timeout=180):
        pass

    def add_item(self, item):
        pass

    def clear_items(self):
        pass


# Capture Real Item if available
RealItem = object
if "discord.ui" in sys.modules:
    try:
        RealItem = sys.modules["discord.ui"].Item
    except AttributeError:
        pass


class MockButton(RealItem):
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.callback = None
        self.label = label

    def _is_v2(self):
        return False


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

# --- MOCK PYMONGO ---
pymongo = MagicMock()
pymongo.errors = MagicMock()
pymongo.errors.DuplicateKeyError = Exception
sys.modules["pymongo"] = pymongo
sys.modules["pymongo.errors"] = pymongo.errors

# --- IMPORT MODULE UNDER TEST ---
from cogs.infirmary_cog import InfirmaryView  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestInfirmaryStateIssue(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager
        self.mock_db = MagicMock(spec=DatabaseManager)

        # Setup User
        self.user = MagicMock()
        self.user.id = 12345

        # Initial Player Data (for View initialization)
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
        view = InfirmaryView(self.mock_db, self.user, self.initial_p_data, self.initial_stats)

        old_max_hp = self.initial_stats.max_hp  # 150
        new_max_hp = 200  # Simulated new Max HP in DB

        # 2. Simulate DB state where player has changed

        # Mock get_player_vitals (Current state)
        self.mock_db.get_player_vitals.return_value = {"current_hp": 50, "current_mp": 10}
        self.mock_db.get_player_field.return_value = 1000  # Aurum

        # Mock get_player_stats_json to return FRESH stats (Max HP 200)
        fresh_stats = PlayerStats(str_base=10, end_base=15)  # END 15 -> HP 200
        self.mock_db.get_player_stats_json.return_value = fresh_stats.to_dict()

        # 3. Call _execute_heal
        view._execute_heal()

        # 4. Verify execute_heal called with FRESH Max HP (200)
        self.mock_db.execute_heal.assert_called_with(self.user.id, new_max_hp, fresh_stats.max_mp, cost=0)

        # Also ensure it wasn't called with old HP
        args, _ = self.mock_db.execute_heal.call_args
        self.assertEqual(
            args[1], new_max_hp, f"Vulnerability: Healed to {args[1]} (Stale), expected {new_max_hp} (Fresh)"
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
