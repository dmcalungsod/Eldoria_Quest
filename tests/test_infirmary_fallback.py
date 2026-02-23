import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Fix path to include repo root
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

    def _is_v2(self):
        return False


class TestInfirmaryFallbackExploit(unittest.TestCase):
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

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_discord.ui
        sys.modules["discord.ext"] = MagicMock()
        sys.modules["discord.ext.commands"] = MagicMock()

        # Mock Pymongo
        sys.modules["pymongo"] = MagicMock()
        sys.modules["pymongo.errors"] = MagicMock()

        # Import modules under test
        import cogs.infirmary_cog

        importlib.reload(cogs.infirmary_cog)

        self.InfirmaryView = cogs.infirmary_cog.InfirmaryView

        from game_systems.player.player_stats import PlayerStats

        self.PlayerStats = PlayerStats

        self.mock_db = MagicMock()
        self.mock_db.calculate_heal_cost.return_value = 100
        self.user = MagicMock()
        self.user.id = 12345
        self.initial_p_data = {"current_hp": 10, "current_mp": 10, "aurum": 1000}

        # Initial stats: Max HP 100
        self.stale_stats = self.PlayerStats(str_base=1, end_base=5)
        # Check max_hp
        assert self.stale_stats.max_hp == 100, f"Setup error: Expected 100 HP, got {self.stale_stats.max_hp}"

    def tearDown(self):
        self.modules_patcher.stop()

    def test_fallback_vulnerability(self):
        """
        Scenario:
        1. View created with stale stats (Max HP 100).
        2. Player actually has Max HP 50 in reality (e.g. unequipped items).
        3. DB fetch for fresh stats FAILS (returns None/Empty).
        4. Vulnerability: View falls back to stale stats (100) and heals player to 100.
           Result: Player has 50 extra HP they shouldn't have.
        """

        # 1. Create View with stale stats
        view = self.InfirmaryView(self.mock_db, self.user, self.initial_p_data, self.stale_stats)

        # 2. Simulate DB failure for stats
        self.mock_db.get_player_stats_json.return_value = None
        self.mock_db.execute_heal.return_value = (True, "Healed")

        # 3. Execute Heal
        success, msg = view._execute_heal()

        # 4. Assert Fix
        self.assertFalse(success, "Heal should fail if stats cannot be fetched")
        self.assertIn("System error", msg, "Should return an error message")

        # Ensure execute_heal was NOT called
        self.mock_db.execute_heal.assert_not_called()
        print("\nSUCCESS: Vulnerability patched. Heal rejected on missing stats.")


if __name__ == "__main__":
    unittest.main()
