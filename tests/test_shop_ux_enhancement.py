import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Mock Discord
mock_discord = MagicMock()
sys.modules["discord"] = mock_discord
sys.modules["discord.ext"] = MagicMock()

# Mock discord.ui
mock_ui = MagicMock()

# Mock Select to capture options
class MockSelect:
    def __init__(self, placeholder=None, min_values=1, max_values=1, row=0):
        self.options = []
        self.placeholder = placeholder
        self.disabled = False
        self.callback = None

    def add_option(self, label, value, description=None, emoji=None):
        self.options.append({"label": label, "value": value, "description": description})

# Mock View to capture items
class MockView:
    def __init__(self, timeout=None):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

mock_ui.Select = MockSelect
mock_ui.View = MockView
sys.modules["discord.ui"] = mock_ui
mock_discord.ui = mock_ui

# Reload modules to apply mocks
if "cogs.shop_cog" in sys.modules:
    del sys.modules["cogs.shop_cog"]

from cogs.shop_cog import ShopView
from database.database_manager import DatabaseManager


class TestShopUXEnhancement(unittest.TestCase):
    def test_get_inventory_items_counts(self):
        db = DatabaseManager()
        # Mock aggregate
        mock_col = MagicMock()
        # Mock db[collection_name]
        db.db = MagicMock()
        db.db.__getitem__.return_value = mock_col

        # Mock aggregate result
        mock_col.aggregate.return_value = [
            {"_id": "hp_potion", "total": 5},
            {"_id": "mp_potion", "total": 2}
        ]

        counts = db.get_inventory_items_counts(12345, ["hp_potion", "mp_potion"])

        self.assertEqual(counts, {"hp_potion": 5, "mp_potion": 2})
        # Verify pipeline match
        args, _ = mock_col.aggregate.call_args
        pipeline = args[0]
        self.assertEqual(pipeline[0]["$match"]["discord_id"], 12345)
        self.assertEqual(pipeline[0]["$match"]["item_key"]["$in"], ["hp_potion", "mp_potion"])

    def test_shop_view_shows_owned_counts(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345

        inventory = {"hp_potion": 50, "sword": 100}
        owned_counts = {"hp_potion": 3, "sword": 0}

        # Mock CONSUMABLES lookup
        with patch("cogs.shop_cog.CONSUMABLES", {
            "hp_potion": {"name": "Health Potion", "description": "Heals HP"},
            "sword": {"name": "Iron Sword", "description": "Sharp"}
        }):
            view = ShopView(mock_db, mock_user, 1000, inventory=inventory, owned_counts=owned_counts)

            # Retrieve the MockSelect from items
            select = view.items[0]
            self.assertIsInstance(select, MockSelect)

            # Check options
            options = {opt["value"].split(":")[0]: opt["label"] for opt in select.options}

            self.assertIn("Health Potion — 50 G (Owned: 3)", options["hp_potion"])
            self.assertIn("Iron Sword — 100 G (Owned: 0)", options["sword"])

if __name__ == "__main__":
    unittest.main()
