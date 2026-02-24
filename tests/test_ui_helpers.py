import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock

# Adjust path to include the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo globally as it's a hard dependency for many imports
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.results"] = MagicMock()

# Ensure discord is mocked at module level so imports don't fail during collection
if "discord" not in sys.modules or not isinstance(sys.modules["discord"], MagicMock):
    mock_discord = MagicMock()
    sys.modules["discord"] = mock_discord
    sys.modules["discord.ui"] = MagicMock()

# Import the module to test
import cogs.ui_helpers  # noqa: E402
from cogs.ui_helpers import build_inventory_embed, make_progress_bar  # noqa: E402


class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value, "inline": inline})


class TestUIHelpers(unittest.TestCase):
    def setUp(self):
        # Retrieve the CURRENT global discord mock
        current_discord_mock = sys.modules["discord"]

        # Configure it
        current_discord_mock.Embed.side_effect = MockEmbed
        current_discord_mock.Color.dark_orange.return_value = "dark_orange"

        # Reload module to ensure it uses this mock (if it was holding an old one)
        global build_inventory_embed, make_progress_bar
        importlib.reload(cogs.ui_helpers)
        build_inventory_embed = cogs.ui_helpers.build_inventory_embed
        make_progress_bar = cogs.ui_helpers.make_progress_bar

    def test_progress_bar_logic(self):
        """Test progress bar logic directly."""
        bar = make_progress_bar(5, 10, length=10, empty_char="-", filled_char="#")
        self.assertEqual(bar, "#####-----")

    def test_inventory_embed_categorization(self):
        """Test that inventory embed categorizes equipped items."""
        items = [
            # Weapon
            {
                "item_name": "Sword of Testing",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Rare",
                "equipped": 1,
                "slot": "sword",
            },
            # Armor
            {
                "item_name": "Iron Plate",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Common",
                "equipped": 1,
                "slot": "heavy_armor",
            },
            # Accessory
            {
                "item_name": "Magic Ring",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Uncommon",
                "equipped": 1,
                "slot": "accessory",
            },
            # Off-Hand (Shield -> Armor)
            {
                "item_name": "Wooden Shield",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Common",
                "equipped": 1,
                "slot": "shield",
            },
            # Off-Hand (Orb -> Weapon)
            {
                "item_name": "Mystic Orb",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Epic",
                "equipped": 1,
                "slot": "orb",
            },
        ]
        max_slots = 20

        embed = build_inventory_embed(items, max_slots)

        # Verify Equipped Gear field exists
        equipped_field = next((f for f in embed.fields if "Equipped Gear" in f["name"]), None)
        self.assertIsNotNone(equipped_field)

        val = equipped_field["value"]

        # Check Weapons Section
        self.assertIn("**Weapons**", val)
        self.assertIn("Sword of Testing", val)
        self.assertIn("Mystic Orb", val)

        # Check Armor Section
        self.assertIn("**Armor**", val)
        self.assertIn("Iron Plate", val)
        self.assertIn("Wooden Shield", val)

        # Check Accessory Section
        # Updated to check for new format with capacity
        self.assertIn("**Accessories (1/2)**", val)
        self.assertIn("Magic Ring", val)

    def test_inventory_embed_unequipped(self):
        """Test unequipped items grouping."""
        items = [
            {
                "item_name": "Potion",
                "item_type": "consumable",
                "count": 5,
                "rarity": "Common",
                "equipped": 0,
            },
            {
                "item_name": "Spare Sword",
                "item_type": "equipment",
                "count": 1,
                "rarity": "Common",
                "equipped": 0,
            },
        ]

        embed = build_inventory_embed(items, 20)

        # Check Consumable Field
        cons_field = next((f for f in embed.fields if f["name"] == "Consumable"), None)
        self.assertIsNotNone(cons_field)
        self.assertIn("Potion (x5)", cons_field["value"])

        # Check Equipment Field (unequipped)
        eq_field = next((f for f in embed.fields if f["name"] == "Equipment"), None)
        self.assertIsNotNone(eq_field)
        self.assertIn("Spare Sword (x1)", eq_field["value"])


if __name__ == "__main__":
    unittest.main()
