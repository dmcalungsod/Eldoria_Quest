import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Add repo root to path
sys.path.append(os.getcwd())

# 1. Mock discord and pymongo modules BEFORE importing the cog
mock_discord = MagicMock()
mock_discord_ui = MagicMock()
mock_pymongo = MagicMock()

sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()


# Define a MockView that accepts init args and has methods used by StatusUpdateView
class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children = []


mock_discord_ui.View = MockView
mock_discord_ui.Button = MagicMock()

sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ui"] = mock_discord_ui

# 2. Now import the classes to test
# We need to ensure cogs.ui_helpers is importable or mocked if needed
# But since we are mocking discord, UI helpers might just work if they only use discord types
# However, cogs.status_update_cog imports .ui_helpers relative import
# This requires cogs to be a package.

# To avoid import errors with relative imports when running as script:
# We will patch cogs.ui_helpers if needed, but since we are running from root,
# `from .ui_helpers import ...` inside `cogs/status_update_cog.py` should resolve to `cogs/ui_helpers.py`.

# But we need to mock DatabaseManager too? No, we pass a mock instance.
# But the file imports it. It must exist.

try:
    from cogs.status_update_cog import StatusUpdateView
    from game_systems.player.player_stats import PlayerStats
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)


class TestOptimisticLocking(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Initial stats setup
        # PlayerStats expects a dict with keys like "STR": {"base": 10, ...}
        # But wait, PlayerStats.from_dict parses the JSON structure.
        # Let's verify PlayerStats structure from memory or file.
        # game_systems/player/player_stats.py

        # We need a valid stats dict structure for PlayerStats.from_dict to work without error
        # Assuming typical structure: {"STR": {"base": 10}, ...}
        self.stats_dict = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
        }
        self.stats_json_str = json.dumps(self.stats_dict)

        # We need to mock PlayerStats because StatusUpdateView uses it
        # Actually, we can use the real PlayerStats if it doesn't have external deps
        # It seems purely data-driven.

        self.real_stats = PlayerStats.from_dict(self.stats_dict)

        self.p_data = {"vestige_pool": 100, "class_id": 1}

        self.mock_stats_row = {"stats_json": self.stats_json_str}

        # Configure Mock DB
        self.mock_db.get_player_field.return_value = 100
        self.mock_db.get_player_stats_row.return_value = self.mock_stats_row
        self.mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}

        # Instantiate View
        # Note: StatusUpdateView calls self._get_class_starting_stats which uses CLASSES constant
        # We might need to mock game_systems.data.class_data if it causes issues, but it should be fine.

        self.view = StatusUpdateView(self.mock_db, self.mock_user, self.p_data, self.real_stats, self.mock_stats_row)

    def test_upgrade_success(self):
        """Verify successful upgrade flow."""
        # 1. Deduct Success
        self.mock_db.deduct_vestige.return_value = True
        # 2. Update Success
        self.mock_db.update_player_stats_optimistic.return_value = True

        success, msg, new_vestige = self.view._execute_upgrade("STR", 1)

        self.assertTrue(success)
        self.mock_db.deduct_vestige.assert_called_once()
        self.mock_db.update_player_stats_optimistic.assert_called_once()
        self.mock_db.refund_vestige.assert_not_called()
        self.mock_db.update_player_vitals.assert_called_once()

    def test_upgrade_insufficient_funds(self):
        """Verify behavior when funds are insufficient."""
        # 1. Deduct Fail
        self.mock_db.deduct_vestige.return_value = False

        success, msg, new_vestige = self.view._execute_upgrade("STR", 1)

        self.assertFalse(success)
        self.assertIn("Insufficient Vestige", msg)
        self.mock_db.deduct_vestige.assert_called_once()
        # Should NOT proceed
        self.mock_db.update_player_stats_optimistic.assert_not_called()
        self.mock_db.refund_vestige.assert_not_called()

    def test_upgrade_race_condition(self):
        """Verify rollback when optimistic lock fails."""
        # 1. Deduct Success
        self.mock_db.deduct_vestige.return_value = True
        # 2. Update Fail (Optimistic Lock)
        self.mock_db.update_player_stats_optimistic.return_value = False

        success, msg, new_vestige = self.view._execute_upgrade("STR", 1)

        self.assertFalse(success)
        self.assertIn("System busy", msg)

        self.mock_db.deduct_vestige.assert_called_once()
        self.mock_db.update_player_stats_optimistic.assert_called_once()

        # CRITICAL: Verify Refund
        self.mock_db.refund_vestige.assert_called_once()

        # Verify vitals not updated
        self.mock_db.update_player_vitals.assert_not_called()


if __name__ == "__main__":
    unittest.main()
