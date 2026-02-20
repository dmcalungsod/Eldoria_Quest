import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCraftingUI(unittest.TestCase):
    def setUp(self):
        # 1. Mock dependencies
        self.mock_discord = MagicMock()
        self.mock_discord.ButtonStyle.primary = "primary"
        self.mock_discord.ButtonStyle.secondary = "secondary"
        self.mock_discord.ButtonStyle.success = "success"
        self.mock_discord.ButtonStyle.danger = "danger"
        self.mock_discord.Color.purple.return_value = "purple"
        self.mock_discord.Color.green.return_value = "green"
        self.mock_discord.Color.red.return_value = "red"

        # Mock UI Components
        class MockView:
            def __init__(self, timeout=None):
                self.children = []
                self.timeout = timeout
            def add_item(self, item):
                self.children.append(item)

        class MockButton:
            def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None):
                self.label = label
                self.style = style
                self.custom_id = custom_id
                self.emoji = emoji
                self.row = row
                self.callback = None
                self.disabled = False
            def _is_v2(self):
                return False

        class MockSelect:
            def __init__(
                self, placeholder=None, min_values=1, max_values=1, options=None, disabled=False, row=None, custom_id=None
            ):
                self.placeholder = placeholder
                self.options = options or []
                self.disabled = disabled
                self.row = row
                self.callback = None
            def add_option(self, label, value, description=None, emoji=None):
                self.options.append({"label": label, "value": value, "description": description, "emoji": emoji})

        self.mock_ui = MagicMock()
        self.mock_ui.View = MockView
        self.mock_ui.Button = MockButton
        self.mock_ui.Select = MockSelect

        # Patch modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_ui,
            "pymongo": MagicMock(),
            "cogs.ui_helpers": MagicMock(),
        })
        self.modules_patcher.start()

        # Import module under test
        if "game_systems.crafting.ui.crafting_view" in sys.modules:
            del sys.modules["game_systems.crafting.ui.crafting_view"]

        import game_systems.crafting.ui.crafting_view
        self.CraftingView = game_systems.crafting.ui.crafting_view.CraftingView

        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Mock CraftingSystem
        self.mock_crafting_system = MagicMock()

        # Mock recipes
        self.recipes = {
            "potion_1": {"name": "Health Potion", "cost": 10, "type": "consumable", "materials": {"herb": 1}},
            "sword_1": {"name": "Iron Sword", "cost": 50, "type": "equipment", "materials": {"iron": 2}},
        }

        # We need to make sure the instance returns these recipes
        self.mock_crafting_system.get_recipes.return_value = self.recipes
        self.mock_crafting_system.can_craft.return_value = (True, "Ready")

        # Patch CraftingSystem constructor in the imported module
        # Note: patch needs to target where CraftingSystem is imported/used in crafting_view.py
        patcher = patch("game_systems.crafting.ui.crafting_view.CraftingSystem")
        self.MockCraftingSystemClass = patcher.start()
        self.MockCraftingSystemClass.return_value = self.mock_crafting_system
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.modules_patcher.stop()

    def test_default_category_consumable(self):
        """Test that default view shows consumable recipes only."""
        view = self.CraftingView(self.mock_db, self.mock_user)

        # Check Buttons (Row 0)
        btn_cons = view.children[0]
        btn_equip = view.children[1]

        self.assertEqual(btn_cons.label, "Consumables")
        self.assertEqual(btn_cons.style, "primary")  # Active

        self.assertEqual(btn_equip.label, "Equipment")
        self.assertEqual(btn_equip.style, "secondary")  # Inactive

        # Check Select Menu (Row 1)
        select = view.children[3]
        # self.assertIsInstance(select, MockSelect) # MagicMock class check might fail, check attributes
        self.assertTrue(hasattr(select, "options"))
        self.assertIn("consumable", select.placeholder)

        # Should contain potion_1 but NOT sword_1
        labels = [opt["label"] for opt in select.options]
        # "Health Potion (10 G)"
        self.assertTrue(any("Health Potion" in lbl for lbl in labels))
        self.assertFalse(any("Iron Sword" in lbl for lbl in labels))

    def test_category_equipment(self):
        """Test initialization with equipment category."""
        view = self.CraftingView(self.mock_db, self.mock_user, category="equipment")

        # Check Buttons
        btn_cons = view.children[0]
        btn_equip = view.children[1]

        self.assertEqual(btn_cons.style, "secondary")
        self.assertEqual(btn_equip.style, "primary")  # Active

        # Check Select Menu
        select = view.children[3]
        self.assertIn("equipment", select.placeholder)

        # Should contain sword_1 but NOT potion_1
        labels = [opt["label"] for opt in select.options]
        self.assertTrue(any("Iron Sword" in lbl for lbl in labels))
        self.assertFalse(any("Health Potion" in lbl for lbl in labels))


if __name__ == "__main__":
    unittest.main()
