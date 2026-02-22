import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to include the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Mock discord
mock_discord = MagicMock()
mock_discord.Color.dark_orange.return_value = "dark_orange"

class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value, "inline": inline})

mock_discord.Embed = MockEmbed
sys.modules["discord"] = mock_discord

from cogs.ui_helpers import build_inventory_embed, make_progress_bar  # noqa: E402
import game_systems.data.emojis as E  # noqa: E402

class TestUIHelpers(unittest.TestCase):
    def test_progress_bar_logic(self):
        """Test progress bar logic directly."""
        bar = make_progress_bar(5, 10, length=10, empty_char="-", filled_char="#")
        self.assertEqual(bar, "#####-----")

    def test_inventory_embed_content(self):
        """Test that inventory embed contains capacity info."""
        items = [{"item_name": "Test Item", "item_type": "consumable", "count": 1, "rarity": "Common"}]
        max_slots = 20

        embed = build_inventory_embed(items, max_slots)

        # Verify title
        self.assertIn("Backpack (1/20)", embed.title)

        # Verify description contains capacity bar
        self.assertIn("**Capacity:**", embed.description)
        self.assertIn("1/20", embed.description)

        # Verify fields
        # "Consumable" field should be present
        found_cat = False
        for f in embed.fields:
            if f["name"] == "Consumable":
                found_cat = True
                self.assertIn("Test Item", f["value"])
        self.assertTrue(found_cat, "Consumable category not found")

    def test_empty_inventory_embed(self):
        """Test empty inventory message."""
        items = []
        max_slots = 15

        embed = build_inventory_embed(items, max_slots)

        self.assertIn("Backpack (0/15)", embed.title)
        self.assertIn("**Capacity:**", embed.description)
        self.assertIn("0/15", embed.description)
        self.assertIn("Your pack is light", embed.description)

if __name__ == "__main__":
    unittest.main()
