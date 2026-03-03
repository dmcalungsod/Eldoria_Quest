import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestShopUXEnhancement(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_discord = MagicMock()
        self.mock_ui = MagicMock()

        # Mock Select
        class MockSelect:
            def __init__(self, placeholder=None, min_values=1, max_values=1, row=0):
                self.options = []
                self.placeholder = placeholder
                self.disabled = False
                self.callback = None

            def add_option(self, label, value, description=None, emoji=None):
                self.options.append({"label": label, "value": value, "description": description})

        # Mock View
        class MockView:
            def __init__(self, timeout=None):
                self.items = []

            def add_item(self, item):
                self.items.append(item)

        self.mock_ui.Select = MockSelect
        self.mock_ui.View = MockView
        self.mock_discord.ui = self.mock_ui

        # Prepare patches
        self.modules_patcher = patch.dict(
            sys.modules,
            {
                "discord": self.mock_discord,
                "discord.ui": self.mock_ui,
                "discord.ext": MagicMock(),
                "pymongo": MagicMock(),
                "pymongo.errors": MagicMock(),
            },
        )
        self.modules_patcher.start()

        # Import under test (must happen after patching)
        if "cogs.shop_cog" in sys.modules:
            del sys.modules["cogs.shop_cog"]
        import cogs.shop_cog

        self.shop_module = cogs.shop_cog
        self.ShopView = self.shop_module.ShopView

        # Import DatabaseManager (it uses pymongo which is now mocked)
        if "database.database_manager" in sys.modules:
            del sys.modules["database.database_manager"]
        import database.database_manager

        self.db_module = database.database_manager
        self.DatabaseManager = self.db_module.DatabaseManager

    def tearDown(self):
        self.modules_patcher.stop()
        # Clean up imported modules to avoid polluting other tests
        if "cogs.shop_cog" in sys.modules:
            del sys.modules["cogs.shop_cog"]
        if "database.database_manager" in sys.modules:
            del sys.modules["database.database_manager"]

    def test_get_inventory_items_counts(self):
        db = self.DatabaseManager()
        # Mock aggregate
        mock_col = MagicMock()
        # Mock db[collection_name]
        db.db = MagicMock()
        db.db.__getitem__.return_value = mock_col

        # Mock aggregate result
        mock_col.aggregate.return_value = [{"_id": "hp_potion", "total": 5}, {"_id": "mp_potion", "total": 2}]

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

        # Mock CONSUMABLES lookup within the patched module
        with patch.dict(
            self.shop_module.CONSUMABLES,
            {
                "hp_potion": {"name": "Health Potion", "description": "Heals HP"},
                "sword": {"name": "Iron Sword", "description": "Sharp"},
            },
            clear=True,
        ):
            view = self.ShopView(mock_db, mock_user, 1000, inventory=inventory, owned_counts=owned_counts)

            # Retrieve the MockSelect from items
            select = view.items[0]
            # Verify type against the class defined in setUp
            self.assertIsInstance(select, self.mock_ui.Select)

            # Check options
            options = {opt["value"].split(":")[0]: opt["label"] for opt in select.options}

            self.assertIn("Health Potion — 50 G (Owned: 3)", options["hp_potion"])
            self.assertIn("Iron Sword — 100 G (Owned: 0)", options["sword"])


if __name__ == "__main__":
    unittest.main()
