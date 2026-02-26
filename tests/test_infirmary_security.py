import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper Mocks
class MockView:
    def __init__(self, timeout=180):
        pass

    def add_item(self, item):
        pass

    def clear_items(self):
        pass


class MockButton:
    def __init__(
        self,
        label=None,
        style=None,
        custom_id=None,
        emoji=None,
        row=None,
        disabled=False,
    ):
        self.callback = None
        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.row = row
        self.emoji = emoji
        self.disabled = disabled

    def _is_v2(self):
        return False


class TestInfirmaryStateIssue(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.ui.View = MockView
        mock_discord.ui.Button = MockButton
        mock_discord.ButtonStyle = MagicMock()
        mock_discord.User = MagicMock()
        mock_discord.Embed = MagicMock()
        mock_discord.Color = MagicMock()

        mock_discord.ButtonStyle.primary = "primary"
        mock_discord.ButtonStyle.secondary = "secondary"
        mock_discord.ButtonStyle.success = "success"
        mock_discord.Color.green.return_value = "green"
        mock_discord.Color.red.return_value = "red"
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_discord.ui
        sys.modules["discord.ext"] = MagicMock()
        sys.modules["discord.ext.commands"] = MagicMock()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        mock_pymongo.errors.DuplicateKeyError = Exception  # Preserve original mock behavior

        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Import module under test
        import cogs.infirmary_cog

        importlib.reload(cogs.infirmary_cog)
        self.InfirmaryView = cogs.infirmary_cog.InfirmaryView

        from database.database_manager import DatabaseManager

        self.DatabaseManager = DatabaseManager

        from game_systems.player.player_stats import PlayerStats

        self.PlayerStats = PlayerStats

        # Setup test objects
        self.mock_db = MagicMock(spec=self.DatabaseManager)
        self.mock_db.calculate_heal_cost.return_value = 100
        self.user = MagicMock()
        self.user.id = 12345

        # Initial Player Data (for View initialization)
        self.initial_p_data = {"current_hp": 50, "current_mp": 10, "aurum": 1000}

        # Initial Stats (Max HP 150 based on base stats logic in PlayerStats)
        # PlayerStats(str_base=10, end_base=10) -> HP = 50 + (10 * 10) = 150
        self.initial_stats = self.PlayerStats(str_base=10, end_base=10)

    def tearDown(self):
        self.modules_patcher.stop()

    def test_stale_stats_healing(self):
        """
        Scenario:
        1. View initialized with Max HP 150.
        2. Player changes gear/buffs, Max HP becomes 200 in DB (simulated).
        3. User clicks Heal.
        4. View SHOULD heal to 200 (Fresh), but due to bug heals to 150 (Stale).
        """

        # 1. Initialize View with initial stats (Max HP 150)
        view = self.InfirmaryView(self.mock_db, self.user, self.initial_p_data, self.initial_stats)

        old_max_hp = self.initial_stats.max_hp  # 150
        new_max_hp = 200  # Simulated new Max HP in DB

        # 2. Simulate DB state where player has changed

        # Mock get_player_vitals (Current state)
        self.mock_db.get_player_vitals.return_value = {
            "current_hp": 50,
            "current_mp": 10,
        }
        self.mock_db.get_player_field.return_value = 1000  # Aurum

        # Mock get_player_stats_json to return FRESH stats (Max HP 200)
        fresh_stats = self.PlayerStats(str_base=10, end_base=15)  # END 15 -> HP 200
        self.mock_db.get_player_stats_json.return_value = fresh_stats.to_dict()

        # 3. Call _execute_heal
        view._execute_heal()

        # 4. Verify execute_heal called with FRESH Max HP (200)
        self.mock_db.execute_heal.assert_called_with(self.user.id, new_max_hp, fresh_stats.max_mp)

        # Also ensure it wasn't called with old HP
        args, _ = self.mock_db.execute_heal.call_args
        self.assertEqual(
            args[1],
            new_max_hp,
            f"Vulnerability: Healed to {args[1]} (Stale), expected {new_max_hp} (Fresh)",
        )


if __name__ == "__main__":
    unittest.main()
