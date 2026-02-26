import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Configure sys.modules with mocks FIRST
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

mock_discord = MagicMock()
mock_discord.ButtonStyle.primary = "primary"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.danger = "danger"
mock_discord.ButtonStyle.success = "success"
mock_discord.Color.purple.return_value = "purple"
mock_discord.Color.green.return_value = "green"
mock_discord.Color.red.return_value = "red"

mock_ui = MagicMock()


class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)


mock_ui.View = MockView


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, row=None, emoji=None):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.row = row
        self.emoji = emoji
        self.callback = None


mock_ui.Button = MockButton


class MockSelect:
    def __init__(self, placeholder=None, min_values=1, max_values=1, row=None, disabled=False):
        self.placeholder = placeholder
        self.disabled = disabled
        self.row = row
        self.options = []
        self.callback = None

    def add_option(self, label, value, description=None, emoji=None):
        self.options.append({"label": label, "value": value})


mock_ui.Select = MockSelect

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import game_systems.crafting.ui.crafting_view  # noqa: E402

importlib.reload(game_systems.crafting.ui.crafting_view)
from game_systems.crafting.ui.crafting_view import CraftingView  # noqa: E402


class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def set_footer(self, text=None):
        pass

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value})


# This global assignment is removed as per the instruction to patch in setUp


class TestCraftingViewExtended(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

        import game_systems.crafting.ui.crafting_view
        game_systems.crafting.ui.crafting_view.discord.Embed.side_effect = MockEmbed

        # Patch CraftingSystem
        self.patcher = patch("game_systems.crafting.ui.crafting_view.CraftingSystem")
        self.mock_craft_sys_class = self.patcher.start()
        self.mock_craft_sys = self.mock_craft_sys_class.return_value

        self.mock_craft_sys.get_recipes.return_value = {}

    def tearDown(self):
        self.patcher.stop()

    def test_setup_dismantle_select_with_items(self):
        # Mock inventory items
        items = [
            {"id": "inv_1", "item_name": "Rusted Sword", "rarity": "Common", "count": 1},
            {"id": "inv_2", "item_name": "Magic Ring", "rarity": "Rare", "count": 1},
        ]
        self.mock_db.get_inventory_items.return_value = items

        # Category dismantle will trigger _setup_dismantle_select
        view = CraftingView(self.mock_db, self.mock_user, category="dismantle")

        select = next((i for i in view.children if hasattr(i, "options")), None)
        self.assertIsNotNone(select)
        self.assertEqual(len(select.options), 2)
        # Should be sorted: Common first, then Rare (due to rarity_rank)
        self.assertEqual(select.options[0]["value"], "inv_1")
        self.assertEqual(select.options[1]["value"], "inv_2")

    def test_setup_dismantle_select_no_items(self):
        self.mock_db.get_inventory_items.return_value = []

        view = CraftingView(self.mock_db, self.mock_user, category="dismantle")

        select = next((i for i in view.children if hasattr(i, "options")), None)
        self.assertIsNotNone(select)
        self.assertTrue(select.disabled)
        self.assertIn("No equipment", select.placeholder)

    def test_build_embed(self):
        view = CraftingView(self.mock_db, self.mock_user, category="consumable", status_msg="Potion Brewed!")
        view.last_success = True

        embed = view.build_embed()
        self.assertEqual(embed.color, "green")
        self.assertIn("Consumables", embed.title)
        field = embed.fields[0]
        self.assertEqual(field["name"], "Result")
        self.assertIn("Potion Brewed!", field["value"])

    def test_build_embed_error(self):
        view = CraftingView(self.mock_db, self.mock_user, category="equipment", status_msg="Not enough materials.")
        view.last_success = False

        embed = view.build_embed()
        self.assertEqual(embed.color, "red")
        self.assertIn("Equipment", embed.title)

    def test_set_back_button(self):
        view = CraftingView(self.mock_db, self.mock_user)

        def dummy_cb():
            pass

        view.set_back_button(dummy_cb, "Go Back")

        back_btn = next((b for b in view.children if getattr(b, "custom_id", None) == "back_crafting"), None)
        self.assertIsNotNone(back_btn)
        self.assertEqual(back_btn.label, "Go Back")
        self.assertEqual(back_btn.callback, dummy_cb)

    async def test_dismantle_select_callback(self):
        view = CraftingView(self.mock_db, self.mock_user, category="dismantle")

        interaction = AsyncMock()
        interaction.data = {"values": ["10"]}  # ID of item to dismantle

        # Mock the system's response
        self.mock_craft_sys.dismantle_item.return_value = (True, "Dismantled!", {"iron": 2})

        await view.dismantle_select_callback(interaction)

        self.mock_craft_sys.dismantle_item.assert_called_with(12345, 10)
        interaction.edit_original_response.assert_called_once()
        args, kwargs = interaction.edit_original_response.call_args

        new_view = kwargs["view"]
        self.assertEqual(new_view.status_msg, "Dismantled!")
        self.assertTrue(new_view.last_success)

    async def test_dismantle_select_callback_invalid_id(self):
        view = CraftingView(self.mock_db, self.mock_user, category="dismantle")

        interaction = AsyncMock()
        interaction.data = {"values": ["invalid_str"]}

        await view.dismantle_select_callback(interaction)

        interaction.followup.send.assert_called_with("Invalid selection.", ephemeral=True)
        self.mock_craft_sys.dismantle_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
