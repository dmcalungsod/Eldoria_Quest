import os
import sys
from unittest.mock import MagicMock

import pytest

# Fix path to include app root so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock database_manager if it attempts to import pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.items.consumable_manager import ConsumableManager  # noqa: E402


class TestFieldKit:
    def test_field_kit_duration_bonus(self):
        """Verify that having a Field Kit in inventory increases buff duration by 5%."""

        # Mock Dependencies
        mock_db = MagicMock()
        mock_inv = MagicMock()

        # Setup ConsumableManager
        manager = ConsumableManager(mock_db)
        # Mock internal InventoryManager manually since we can't inject it easily in __init__
        manager.inv_manager = mock_inv

        discord_id = 12345
        item_id = 999

        # Mock Inventory Item (Dragonblood Ale - 180s base duration)
        mock_db.get_inventory_item.return_value = {
            "item_key": "dragonblood_ale",
            "item_type": "consumable",
            "amount": 1,
        }

        # Mock Player Vitals & Stats
        mock_db.get_player_vitals.return_value = {"current_hp": 100, "current_mp": 50}
        mock_db.get_player_stats_json.return_value = {"STR": {"base": 10}, "HP": {"base": 100}, "MP": {"base": 50}}

        # Mock consume success
        mock_db.consume_item_atomic.return_value = True

        # Scenario 1: No Field Kit
        # ------------------------
        mock_db.get_active_adventure.return_value = None
        mock_inv.get_inventory.return_value = []  # Empty inventory

        success, msg = manager.use_item(discord_id, item_id)

        assert success
        # Verify Buff Duration in DB Call
        # add_active_buffs_bulk called with list of dicts.
        # Check duration_s for first buff. Base is 180s.
        args, _ = mock_db.add_active_buffs_bulk.call_args
        buffs = args[1]
        assert buffs[0]["duration_s"] == 180

        # Scenario 2: With Field Kit in Inventory
        # ---------------------------------------
        mock_inv.get_inventory.return_value = [{"item_key": "field_kit"}]

        success, msg = manager.use_item(discord_id, item_id)

        assert success
        args, _ = mock_db.add_active_buffs_bulk.call_args
        buffs = args[1]
        # 180 * 1.05 = 189
        assert buffs[0]["duration_s"] == 189
        assert "(Field Kit: Duration +5%)" in msg


if __name__ == "__main__":
    pytest.main([__file__])
