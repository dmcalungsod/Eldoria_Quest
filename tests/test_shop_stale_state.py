import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Align sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies BEFORE importing ShopView
# We mock pymongo so DatabaseManager can be imported safely
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Mock discord and discord.ui
mock_discord = MagicMock()
mock_ui = MagicMock()


class MockView:
    def __init__(self, timeout=None):
        pass

    def add_item(self, item):
        pass


mock_ui.View = MockView
mock_ui.Select = MagicMock
mock_ui.Button = MagicMock

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

# DO NOT mock database.database_manager directly, as other tests need the real module.
# ShopView imports DatabaseManager class, so we let it import the real class (which uses mocked pymongo).


# Now import the class under test
# RELOAD to ensure ShopView uses the MockView defined above, not a stale one
if "cogs.shop_cog" in sys.modules:
    del sys.modules["cogs.shop_cog"]

import cogs.shop_cog as shop_cog  # noqa: E402
from cogs.shop_cog import ShopView  # noqa: E402


class TestShopStaleState(unittest.IsolatedAsyncioTestCase):
    async def test_stale_state_on_purchase_failure(self):
        # Setup
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345
        initial_aurum = 100

        # Create view with 100 aurum (stale state)
        # We pass a mock DB instance, so ShopView uses that instance.
        view = ShopView(mock_db, mock_user, initial_aurum)

        # Mock interaction
        mock_interaction = MagicMock()
        mock_interaction.user.id = 12345
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.edit_original_response = AsyncMock()
        # Simulate selecting an item (hp_potion_1 costs 40)
        # We assume the user has 5 aurum (insufficient) but view thinks 100.
        mock_interaction.data = {"values": ["hp_potion_1:40"]}

        # Mock DB purchase to fail (Insufficient Funds)
        # purchase_item returns (success, result, new_balance)
        # We expect purchase_item to return the actual balance (5) on failure.
        mock_db.purchase_item.return_value = (False, "Insufficient Aurum.", 5)

        # Mock get_player to return fresh data (5 Aurum)
        # This will only be called if we rely on get_player (which we plan to remove).
        mock_db.get_player.return_value = {"aurum": 5}

        # Mock inventory count fetching to avoid Asyncio MagicMock errors
        mock_db.get_inventory_items_counts = MagicMock(return_value={})
        mock_db.get_daily_shop_purchases = MagicMock(return_value={})

        # Mock get_player_or_error helper used in callback
        # Since we imported ShopView directly, we need to patch it where it's used in the module
        # Use patch.object to avoid import errors with string paths in some environments
        with patch.object(shop_cog, "get_player_or_error", new_callable=AsyncMock) as mock_get_player:
            mock_get_player.return_value = True

            # Execute callback
            await view.purchase_item_callback(mock_interaction)

        # Verification
        # Check what view was passed to edit_original_response
        args, kwargs = mock_interaction.edit_original_response.call_args
        new_view = kwargs.get("view")

        # The Bug: new_view.current_aurum is currently 100 (stale), but should be 5 (fresh)
        if hasattr(view, 'current_aurum'):
            print(f"Old View Aurum: {view.current_aurum}")
        if hasattr(new_view, 'current_aurum'):
            print(f"New View Aurum: {new_view.current_aurum}")

        # Assert that the new view reflects the fresh state (5), not the stale state (100)
        self.assertEqual(
            new_view.current_aurum,
            5,
            "Bug reproduced: View has stale aurum (100) instead of fresh (5)",
        )
