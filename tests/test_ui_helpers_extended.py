import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

# Configure sys.modules with mocks FIRST
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

mock_discord = MagicMock()
mock_discord.Color.dark_orange.return_value = "dark_orange"

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cogs.utils.ui_helpers  # noqa: E402

importlib.reload(cogs.utils.ui_helpers)
from cogs.utils.ui_helpers import (  # noqa: E402
    build_inventory_embed,
    get_health_status_emoji,
    get_player_or_error,
    get_profile_bundle_or_error,
    make_progress_bar,
)


class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value, "inline": inline})


class TestUIHelpersExtended(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        import cogs.utils.ui_helpers as ui_helpers

        ui_helpers.discord.Embed.side_effect = MockEmbed

    def test_get_health_status_emoji(self):
        # Green > 0.5
        self.assertEqual(get_health_status_emoji(60, 100), "🟢")
        # Yellow > 0.2
        self.assertEqual(get_health_status_emoji(30, 100), "🟡")
        # Red <= 0.2
        self.assertEqual(get_health_status_emoji(15, 100), "🔴")
        # Edge case: max_val = 0
        self.assertEqual(get_health_status_emoji(10, 0), "🔴")

    def test_make_progress_bar_edge_cases(self):
        # Current = 0
        self.assertEqual(make_progress_bar(0, 100, length=5, empty_char="E", filled_char="F"), "EEEEE")
        # Current = max
        self.assertEqual(make_progress_bar(100, 100, length=5, empty_char="E", filled_char="F"), "FFFFF")
        # Current > max (overflow)
        self.assertEqual(make_progress_bar(150, 100, length=5, empty_char="E", filled_char="F"), "FFFFF")
        # Max < 1 (prevent division by zero)
        self.assertEqual(make_progress_bar(10, 0, length=5, empty_char="E", filled_char="F"), "FFFFF")

    def test_build_inventory_embed_empty(self):
        embed = build_inventory_embed([], 20)
        self.assertIn("pack is light", embed.description)
        self.assertEqual(len(embed.fields), 0)

    def test_build_inventory_embed_truncation(self):
        # Generate 20 items of the same category
        items = []
        for i in range(20):
            items.append(
                {
                    "item_name": f"Material {i}",
                    "item_type": "material",
                    "count": 1,
                    "rarity": "Common",
                    "equipped": 0,
                }
            )

        embed = build_inventory_embed(items, 30)
        material_field = next((f for f in embed.fields if f["name"].lower() == "material"), None)

        self.assertIsNotNone(material_field)
        self.assertIn("...and 5 more", material_field["value"])

    def test_build_inventory_embed_misc_category(self):
        items = [
            {
                "item_name": "Strange Key",
                "item_type": "quest_item",  # Unknown type -> Misc
                "count": 1,
                "rarity": "Epic",
                "equipped": 0,
            }
        ]

        embed = build_inventory_embed(items, 10)
        misc_field = next((f for f in embed.fields if f["name"] == "Misc"), None)

        self.assertIsNotNone(misc_field)
        self.assertIn("Strange Key", misc_field["value"])

    async def test_get_player_or_error_success(self):
        interaction = AsyncMock()
        interaction.user.id = 123
        db = MagicMock()
        db.get_player.return_value = {"name": "Hero"}

        player = await get_player_or_error(interaction, db)
        self.assertEqual(player["name"], "Hero")
        interaction.response.send_message.assert_not_called()

    async def test_get_player_or_error_fail(self):
        interaction = AsyncMock()
        interaction.user.id = 123
        interaction.response.is_done = MagicMock(return_value=True)

        db = MagicMock()
        db.get_player.return_value = None

        player = await get_player_or_error(interaction, db)
        self.assertIsNone(player)
        interaction.followup.send.assert_called_with("Character record not found.", ephemeral=True)

    async def test_get_profile_bundle_or_error_success(self):
        interaction = AsyncMock()
        interaction.user.id = 123
        db = MagicMock()
        db.get_profile_bundle.return_value = {"player": {}, "stats": {}, "guild": {}}

        bundle = await get_profile_bundle_or_error(interaction, db)
        self.assertIsNotNone(bundle)
        interaction.response.send_message.assert_not_called()

    async def test_get_profile_bundle_or_error_fail(self):
        interaction = AsyncMock()
        interaction.user.id = 123
        interaction.response.is_done = MagicMock(return_value=True)

        db = MagicMock()
        db.get_profile_bundle.return_value = None

        bundle = await get_profile_bundle_or_error(interaction, db)
        self.assertIsNone(bundle)
        interaction.followup.send.assert_called_with("Character record not found.", ephemeral=True)


if __name__ == "__main__":
    unittest.main()
