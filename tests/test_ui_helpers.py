import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

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
    sys.modules["discord.ui"].View = type("MockView", (), {})
    sys.modules["discord.ui"].Button = type("MockButton", (), {})
    sys.modules["discord.ext"] = MagicMock()
    sys.modules["discord.ext.commands"] = MagicMock()

# Import the module to test
import cogs.utils.ui_helpers  # noqa: E402
from cogs.utils.ui_helpers import build_inventory_embed, make_progress_bar  # noqa: E402

# Import view modules so patch can resolve their names
import game_systems.character.ui.profile_view  # noqa: E402
import game_systems.guild_system.ui.lobby_view  # noqa: E402


class MockEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title = title or ""
        self.description = description or ""
        self.color = color
        self.fields = []

    def add_field(self, name, value, inline=False):
        self.fields.append({"name": name, "value": value, "inline": inline})

    def set_thumbnail(self, url):
        self.thumbnail_url = url


class TestUIHelpers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Retrieve the CURRENT global discord mock
        current_discord_mock = sys.modules["discord"]

        # Configure it
        current_discord_mock.Embed.side_effect = MockEmbed
        current_discord_mock.Color.dark_orange.return_value = "dark_orange"

        # Reload module to ensure it uses this mock (if it was holding an old one)
        global build_inventory_embed, make_progress_bar
        importlib.reload(cogs.utils.ui_helpers)
        build_inventory_embed = cogs.utils.ui_helpers.build_inventory_embed
        make_progress_bar = cogs.utils.ui_helpers.make_progress_bar

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

    @patch("game_systems.character.ui.profile_view.CharacterTabView", autospec=True)
    @patch("cogs.utils.ui_helpers.DatabaseManager", autospec=True)
    async def test_back_to_profile_callback_new_message(self, MockDB, MockCharacterTabView):
        from unittest.mock import AsyncMock
        import cogs.utils.ui_helpers as ui_helpers

        db_instance = MockDB.return_value
        # Mock get_profile_bundle
        bundle = {
            "player": {
                "name": "Hero",
                "class_id": 1,
                "level": 1,
                "experience": 0,
                "exp_to_next": 100,
                "current_hp": 100,
                "current_mp": 50,
            },
            "stats": {
                "strength": 10,
                "endurance": 10,
                "dexterity": 10,
                "agility": 10,
                "magic": 10,
                "luck": 10,
                "max_hp": 100,
                "max_mp": 50,
                "max_inventory_slots": 20,
            },
            "guild": {"rank": "F"},
        }
        db_instance.get_profile_bundle.return_value = bundle
        db_instance.get_class.return_value = {"name": "Warrior"}
        db_instance.get_inventory_slot_count.return_value = 5

        interaction = AsyncMock()
        interaction.user.id = 123
        interaction.response.is_done = MagicMock(return_value=False)
        await ui_helpers.back_to_profile_callback(interaction, is_new_message=False)
        interaction.response.defer.assert_called_once()
        interaction.edit_original_response.assert_called_once()

        # Test new message branch
        interaction2 = AsyncMock()
        interaction2.response.is_done = MagicMock(return_value=True)
        await ui_helpers.back_to_profile_callback(interaction2, is_new_message=True)
        interaction2.followup.send.assert_called_once()

    @patch("game_systems.guild_system.ui.lobby_view.GuildLobbyView", autospec=True)
    @patch("cogs.utils.ui_helpers.DatabaseManager", autospec=True)
    async def test_back_to_guild_hall_callback(self, MockDB, MockGuildLobbyView):
        from unittest.mock import AsyncMock
        import cogs.utils.ui_helpers as ui_helpers

        db_instance = MockDB.return_value
        db_instance.get_player.return_value = {"id": 123}
        db_instance.get_guild_card_data.return_value = {"name": "Hero", "rank": "F"}

        interaction = AsyncMock()
        interaction.user.id = 123
        interaction.response.is_done = MagicMock(return_value=False)

        await ui_helpers.back_to_guild_hall_callback(interaction)
        interaction.response.defer.assert_called_once()
        interaction.edit_original_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
