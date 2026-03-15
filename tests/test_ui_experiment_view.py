import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock pymongo globally
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Adjust path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Mocking Discord UI ---
class MockItem:
    def __init__(self, *args, **kwargs):
        self.label = kwargs.get("label")
        self.placeholder = kwargs.get("placeholder")
        self.custom_id = kwargs.get("custom_id")
        self.disabled = kwargs.get("disabled", False)
        self.options = kwargs.get("options", [])
        self.callback = None
        self.values = []  # For Select

    def add_option(self, label, value, **kwargs):
        self.options.append(MagicMock(label=label, value=str(value)))


class MockButton(MockItem):
    pass


class MockSelect(MockItem):
    pass


class MockView:
    def __init__(self, timeout=180):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children = []


# Mock discord module
mock_discord = MagicMock()
mock_discord.ButtonStyle = MagicMock()
mock_discord.Color = MagicMock()
mock_discord.ui.View = MockView
mock_discord.ui.Button = MockButton
mock_discord.ui.Select = MockSelect
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

from game_systems.crafting.ui.experiment_view import ExperimentView  # noqa: E402


class TestExperimentView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_interaction = AsyncMock()
        self.mock_interaction.user = self.mock_user
        self.mock_interaction.response = AsyncMock()
        self.mock_interaction.response.is_done.return_value = False

    def test_init_no_materials(self):
        """Test initialization with no materials."""
        self.mock_db.get_inventory_items.return_value = []

        view = ExperimentView(self.mock_db, self.mock_user)

        # Select (0) should be disabled
        self.assertTrue(view.children[0].disabled)
        self.assertEqual(view.children[0].options[0].value, "empty")

        # Mix button (1) should be disabled
        self.assertTrue(view.children[1].disabled)

    def test_init_few_materials(self):
        """Test initialization with fewer than 2 materials."""
        materials = [{"item_name": "Herb", "count": 5, "id": 1, "rarity": "Common"}]
        self.mock_db.get_inventory_items.return_value = materials

        view = ExperimentView(self.mock_db, self.mock_user)

        # Select (0) should be disabled
        self.assertTrue(view.children[0].disabled)
        self.assertIn("Not enough", view.children[0].placeholder)

    def test_init_valid_materials(self):
        """Test initialization with valid materials."""
        materials = [
            {"item_name": "Herb", "count": 5, "id": 1, "rarity": "Common"},
            {"item_name": "Stone", "count": 2, "id": 2, "rarity": "Common"},
        ]
        self.mock_db.get_inventory_items.return_value = materials

        view = ExperimentView(self.mock_db, self.mock_user)

        select = view.children[0]
        self.assertFalse(select.disabled)
        self.assertEqual(len(select.options), 2)

        # Mix button disabled initially
        mix_btn = view.children[1]
        self.assertTrue(mix_btn.disabled)

    async def test_material_select_callback(self):
        """Test selecting materials."""
        materials = [
            {"item_name": "Herb", "count": 5, "id": 1, "rarity": "Common"},
            {"item_name": "Stone", "count": 2, "id": 2, "rarity": "Common"},
        ]
        self.mock_db.get_inventory_items.return_value = materials
        view = ExperimentView(self.mock_db, self.mock_user)

        # Simulate selection via interaction.data['values'] as used in implementation
        self.mock_interaction.data = {"values": ["1", "2"]}

        await view.material_select_callback(self.mock_interaction)

        self.assertEqual(view.selected_materials, [1, 2])
        self.assertFalse(view.mix_btn.disabled)
        self.mock_interaction.response.edit_message.assert_called_with(view=view)

    @patch("game_systems.crafting.ui.experiment_view.CraftingSystem")
    async def test_mix_callback_success(self, MockCraftingSystem):
        """Test mixing success."""
        materials = [
            {"item_name": "Herb", "count": 5, "id": 1, "rarity": "Common"},
            {"item_name": "Stone", "count": 2, "id": 2, "rarity": "Common"},
        ]
        self.mock_db.get_inventory_items.return_value = materials

        mock_system = MockCraftingSystem.return_value
        mock_system.experiment.return_value = (True, "Success!", {"name": "Potion", "effect": {"hp": 10}})

        view = ExperimentView(self.mock_db, self.mock_user)
        view.selected_materials = [1, 2]  # Pre-select

        await view.mix_callback(self.mock_interaction)

        mock_system.experiment.assert_called_with(12345, [1, 2])
        self.mock_interaction.edit_original_response.assert_called()

        # Verify embed contains success info
        args, kwargs = self.mock_interaction.edit_original_response.call_args
        embed = kwargs["embed"]
        # Can verify embed fields if mock discord was more sophisticated, but generic mock is fine
        self.assertIn("Potion", str(embed.add_field.call_args_list))

    @patch("game_systems.crafting.ui.experiment_view.CraftingSystem")
    async def test_mix_callback_failure(self, MockCraftingSystem):
        """Test mixing failure."""
        materials = [
            {"item_name": "Herb", "count": 5, "id": 1, "rarity": "Common"},
            {"item_name": "Stone", "count": 2, "id": 2, "rarity": "Common"},
        ]
        self.mock_db.get_inventory_items.return_value = materials

        mock_system = MockCraftingSystem.return_value
        mock_system.experiment.return_value = (False, "Failed!", None)

        view = ExperimentView(self.mock_db, self.mock_user)
        view.selected_materials = [1, 2]

        await view.mix_callback(self.mock_interaction)

        mock_system.experiment.assert_called_with(12345, [1, 2])
        self.mock_interaction.edit_original_response.assert_called()


if __name__ == "__main__":
    unittest.main()
