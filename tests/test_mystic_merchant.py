import sys
import os
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Mocking dependencies before imports ---

# Mock Discord and UI
mock_discord = MagicMock()
mock_discord.ButtonStyle.primary = 1
mock_discord.ButtonStyle.secondary = 2
mock_discord.ButtonStyle.success = 3
mock_discord.ButtonStyle.grey = 4
mock_discord.Color.purple.return_value = "purple"
mock_discord.Color.green.return_value = "green"

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()

# Mock PyMongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Mock cogs.shop_cog
mock_shop_cog = MagicMock()
sys.modules["cogs.shop_cog"] = mock_shop_cog

# Mock button and view
class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.label = label
        self.custom_id = custom_id
        self.callback = None

sys.modules["discord.ui"].Button = MockButton

class MockView:
    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)

sys.modules["discord.ui"].View = MockView

# Now import the modules under test
from game_systems.guild_system.ui.services_menu import GuildServicesView  # noqa: E402
from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402
from game_systems.data.shop_data import MYSTIC_MERCHANT_INVENTORY  # noqa: E402

class TestMysticMerchantEvent(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345

    def test_button_appears_when_event_active(self):
        # Setup active event
        event_data = {
            "type": WorldEventSystem.MYSTIC_MERCHANT,
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2099-01-01T00:00:00"
        }
        self.mock_db.get_active_world_event.return_value = event_data

        view = GuildServicesView(self.mock_db, self.mock_user)

        # Check if Mystic Merchant button is in children
        mystic_btn = None
        for item in view.children:
            if isinstance(item, MockButton) and item.custom_id == "g_mystic":
                mystic_btn = item
                break

        self.assertIsNotNone(mystic_btn, "Mystic Merchant button should be present")
        self.assertEqual(mystic_btn.label, "Mystic Merchant")

    def test_button_missing_when_no_event(self):
        self.mock_db.get_active_world_event.return_value = None

        view = GuildServicesView(self.mock_db, self.mock_user)

        mystic_btn = None
        for item in view.children:
            if isinstance(item, MockButton) and item.custom_id == "g_mystic":
                mystic_btn = item
                break

        self.assertIsNone(mystic_btn, "Mystic Merchant button should NOT be present")

    def test_mystic_merchant_callback_opens_shop(self):
        # Setup the mock class inside the mocked module
        MockShopViewClass = MagicMock()
        mock_shop_cog.ShopView = MockShopViewClass

        # Ensure __init__ doesn't crash on event check
        self.mock_db.get_active_world_event.return_value = None

        view = GuildServicesView(self.mock_db, self.mock_user)

        # Prepare interaction
        mock_interaction = MagicMock()
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.edit_original_response = AsyncMock()

        # Mock player data
        self.mock_db.get_player.return_value = {"aurum": 500}

        # Call the callback
        asyncio.run(view.mystic_merchant_callback(mock_interaction))

        # Verify ShopView was initialized with MYSTIC_MERCHANT_INVENTORY
        MockShopViewClass.assert_called_once()
        args, kwargs = MockShopViewClass.call_args

        # Signature: ShopView(db, user, aurum, inventory=...)
        self.assertEqual(args[0], self.mock_db)
        self.assertEqual(args[1], self.mock_user)
        self.assertEqual(args[2], 500)
        self.assertEqual(kwargs.get("inventory"), MYSTIC_MERCHANT_INVENTORY)

if __name__ == "__main__":
    unittest.main()
