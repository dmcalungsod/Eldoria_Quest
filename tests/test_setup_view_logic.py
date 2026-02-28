
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib

# Add project root to path for local execution
sys.path.append(os.getcwd())

# Define dummy classes
class DummyView:
    def __init__(self, timeout=180):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

class DummySelect:
    def __init__(self, placeholder=None, min_values=1, max_values=1, row=None, options=None):
        self.options = options or []
        self.min_values = min_values
        self.max_values = max_values
        self.placeholder = placeholder
        self.disabled = False

    def add_option(self, label, value, description=None, emoji=None):
        self.options.append({"label": label, "value": value})

class TestAdventureSetupViewLogic(unittest.TestCase):
    def setUp(self):
        # Prepare mocks
        self.mock_discord = MagicMock()
        self.mock_discord_ui = MagicMock()
        self.mock_discord_ui.View = DummyView
        self.mock_discord_ui.Select = DummySelect
        self.mock_discord_ui.Button = MagicMock()

        # Modules to patch - ensure we mock EVERYTHING setup_view imports that might depend on discord
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord_ui,
            "discord.ext": MagicMock(),
            "discord.ext.commands": MagicMock(),

            # Mock cogs utils
            "cogs": MagicMock(),
            "cogs.utils": MagicMock(),
            "cogs.utils.ui_helpers": MagicMock(),

            # Mock Database
            "pymongo": MagicMock(),
            "pymongo.errors": MagicMock(),
            "database": MagicMock(),
            "database.database_manager": MagicMock(),

            # Mock internal game systems that setup_view imports
            "game_systems.adventure.adventure_manager": MagicMock(),
            "game_systems.adventure.ui.adventure_embeds": MagicMock(),
            "game_systems.adventure.ui.status_view": MagicMock(),

            # We can let data modules load if they are pure data
            # "game_systems.data.adventure_locations": ...
            # "game_systems.data.consumables": ...
        })
        self.modules_patcher.start()

        # Ensure we import a fresh version of the module using the mocks
        self.module_name = "game_systems.adventure.ui.setup_view"
        if self.module_name in sys.modules:
            del sys.modules[self.module_name]

        # Import the module
        import game_systems.adventure.ui.setup_view
        self.module = game_systems.adventure.ui.setup_view
        self.AdventureSetupView = self.module.AdventureSetupView

        # Setup common test data
        self.db = MagicMock()
        self.manager = MagicMock()
        self.user = MagicMock()
        self.user.id = 12345

    def tearDown(self):
        self.modules_patcher.stop()
        # Clean up the module from sys.modules so subsequent tests don't use the mocked version
        if self.module_name in sys.modules:
            del sys.modules[self.module_name]

    def test_supply_limit(self):
        # Create 30 different supplies
        supplies = []
        for i in range(30):
            supplies.append({
                "item_key": f"supply_{i}",
                "item_name": f"Supply {i}",
                "count": 1,
                "type": "supply"
            })

        view = self.AdventureSetupView(self.db, self.manager, self.user, "F", 1, supplies, (10, 20))

        # Check supply_select options count
        self.assertLessEqual(len(view.supply_select.options), 25, "Supply options should not exceed 25")

    def test_max_values_constraint(self):
        # Case 1: 1 supply
        supplies = [{"item_key": "s1", "item_name": "S1", "count": 1}]
        view = self.AdventureSetupView(self.db, self.manager, self.user, "F", 1, supplies, (10, 20))

        # max_values must be <= len(options)
        self.assertLessEqual(view.supply_select.max_values, len(view.supply_select.options), "max_values must be <= options count (1 supply)")

        # Case 2: 2 supplies
        supplies = [
            {"item_key": "s1", "item_name": "S1", "count": 1},
            {"item_key": "s2", "item_name": "S2", "count": 1}
        ]
        view = self.AdventureSetupView(self.db, self.manager, self.user, "F", 1, supplies, (10, 20))
        self.assertLessEqual(view.supply_select.max_values, len(view.supply_select.options), "max_values must be <= options count (2 supplies)")

        # Case 3: 0 supplies (No Supplies placeholder)
        supplies = []
        view = self.AdventureSetupView(self.db, self.manager, self.user, "F", 1, supplies, (10, 20))
        # Should have "No Supplies" option
        self.assertEqual(len(view.supply_select.options), 1)
        self.assertEqual(view.supply_select.options[0]["value"], "none")
        # max_values should be 1
        self.assertEqual(view.supply_select.max_values, 1, "max_values must be 1 for No Supplies placeholder")

if __name__ == '__main__':
    unittest.main()
