import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper Mocks
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
        self,
        placeholder=None,
        min_values=1,
        max_values=1,
        options=None,
        disabled=False,
        row=None,
        custom_id=None,
    ):
        self.placeholder = placeholder
        self.options = options or []
        self.disabled = disabled
        self.row = row
        self.callback = None

    def add_option(self, label, value, description=None, emoji=None):
        self.options.append({"label": label, "value": value, "description": description, "emoji": emoji})


class TestCraftingUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.ButtonStyle.primary = "primary"
        mock_discord.ButtonStyle.secondary = "secondary"
        mock_discord.ButtonStyle.success = "success"
        mock_discord.ButtonStyle.danger = "danger"
        mock_discord.Color.purple.return_value = "purple"
        mock_discord.Color.green.return_value = "green"
        mock_discord.Color.red.return_value = "red"

        mock_ui = MagicMock()
        mock_ui.View = MockView
        mock_ui.Button = MockButton
        mock_ui.Select = MockSelect

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_ui

        # Mock other dependencies
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.utils.ui_helpers"] = MagicMock()
        sys.modules["game_systems.crafting.ui.experiment_view"] = MagicMock()

        # Import module under test
        import game_systems.crafting.ui.crafting_view

        importlib.reload(game_systems.crafting.ui.crafting_view)

        self.CraftingView = game_systems.crafting.ui.crafting_view.CraftingView

        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        # Mock CraftingSystem
        self.mock_crafting_system = MagicMock()

        # Mock recipes
        self.recipes = {
            "potion_1": {
                "name": "Health Potion",
                "cost": 10,
                "type": "consumable",
                "materials": {"herb": 1},
            },
            "sword_1": {
                "name": "Iron Sword",
                "cost": 50,
                "type": "equipment",
                "materials": {"iron": 2},
            },
        }

        # We need to make sure the instance returns these recipes
        self.mock_crafting_system.get_recipes.return_value = self.recipes
        self.mock_crafting_system.can_craft.return_value = (True, "Ready")

        # Patch CraftingSystem constructor
        patcher = unittest.mock.patch("game_systems.crafting.ui.crafting_view.CraftingSystem")
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

        # Check Experiment Button (Row 0, index 3)
        btn_exp = view.children[3]
        self.assertEqual(btn_exp.label, "Experiment")
        self.assertEqual(btn_exp.style, "success")

        # Check Select Menu (Row 1, index 4)
        select = view.children[4]
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
        select = view.children[4]
        self.assertIn("equipment", select.placeholder)

        # Should contain sword_1 but NOT potion_1
        labels = [opt["label"] for opt in select.options]
        self.assertTrue(any("Iron Sword" in lbl for lbl in labels))
        self.assertFalse(any("Health Potion" in lbl for lbl in labels))

    async def test_recipe_select_callback(self):
        """Test selecting a recipe to craft."""
        view = self.CraftingView(self.mock_db, self.mock_user)
        interaction = AsyncMock()
        interaction.data = {"values": ["potion_1"]}

        # Mock crafting logic
        self.mock_crafting_system.craft_item.return_value = (True, "Crafted successfully!", {})

        await view.recipe_select_callback(interaction)

        # Verify craft_item called
        self.mock_crafting_system.craft_item.assert_called_with(12345, "potion_1")

        # Verify response update
        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        self.assertIsInstance(kwargs["view"], self.CraftingView)
        self.assertEqual(kwargs["view"].status_msg, "Crafted successfully!")

    async def test_dismantle_select_callback(self):
        """Test selecting an item to dismantle."""
        # Setup view in dismantle mode
        view = self.CraftingView(self.mock_db, self.mock_user, category="dismantle")

        interaction = AsyncMock()
        interaction.data = {"values": ["999"]}  # Inventory ID

        # Mock dismantle logic
        self.mock_crafting_system.dismantle_item.return_value = (True, "Dismantled!", {"scrap": 1})

        await view.dismantle_select_callback(interaction)

        # Verify dismantle_item called
        self.mock_crafting_system.dismantle_item.assert_called_with(12345, 999)

        # Verify response update
        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        self.assertEqual(kwargs["view"].status_msg, "Dismantled!")

    async def test_category_experiment_callback(self):
        """Test switching to experiment view."""
        view = self.CraftingView(self.mock_db, self.mock_user)
        interaction = AsyncMock()

        # Mock ExperimentView
        MockExperimentView = sys.modules["game_systems.crafting.ui.experiment_view"].ExperimentView
        MockExperimentView.return_value.build_embed.return_value = MagicMock()

        await view.category_experiment_callback(interaction)

        interaction.edit_original_response.assert_called()
        # Ensure ExperimentView was instantiated
        MockExperimentView.assert_called()

    async def test_switch_category(self):
        """Test switching categories."""
        view = self.CraftingView(self.mock_db, self.mock_user, category="consumable")
        interaction = AsyncMock()

        await view.category_equip_callback(interaction)

        interaction.edit_original_response.assert_called()
        args, kwargs = interaction.edit_original_response.call_args
        new_view = kwargs["view"]
        self.assertEqual(new_view.category, "equipment")


if __name__ == "__main__":
    unittest.main()
