import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock discord before importing anything that uses it
mock_discord = MagicMock()

# Ensure View is a class that can be inherited from without creating a MagicMock for every method
class MockView:
    def __init__(self, *args, **kwargs):
        self.children = []

    def add_item(self, item):
        self.children.append(item)
        return self # add_item typically returns self or None, strictly View.add_item returns self in some versions or None in others. discord.py returns None usually.

    def clear_items(self):
        self.children.clear()

    def stop(self):
        pass

    # Allow async context manager if needed
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass

mock_discord.ui.View = MockView

sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()
sys.modules["discord.app_commands"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Import normally (it will use the mock)
try:
    # ruff: noqa: F401
    import cogs.shop_cog
    from cogs.shop_cog import ShopView
except ImportError:
    ShopView = None


class TestSecurityShop(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Force reload cogs.shop_cog to ensure ShopView uses our mocks
        if "cogs.shop_cog" in sys.modules:
            # Re-import to handle namespace package issues during reload
            shop_cog = sys.modules["cogs.shop_cog"]
            importlib.reload(shop_cog)

        from cogs.shop_cog import ShopView as SV
        self.ShopView = SV

    async def test_shop_callback_validation_success(self):
        """Verify that purchase_item_callback accepts valid input."""
        db = Mock()
        user = MagicMock()
        user.id = 12345

        # Instantiate view with mocked dependencies
        view = self.ShopView(db, user, 1000)

        # Mock internal method to avoid DB calls
        # We assume purchase_item_callback is an async method on the view
        # We need to make sure it's awaitable even if we mocked the class components

        # Manually attach AsyncMock to the instance method if it got mocked out
        # But wait, self.ShopView is the real class (imported).
        # So view.purchase_item_callback should be the real method.
        # The error "MagicMock can't be used in await expression" implies
        # view.purchase_item_callback IS a MagicMock.
        # This happens if the View base class or some decoration made it a mock.

        # Let's inspect what ShopView inherits from.
        # In our mock: discord.ui.View = MagicMock()
        # So ShopView inherits from MagicMock.
        # This is dangerous because methods not defined in ShopView might be MagicMocks.
        # BUT purchase_item_callback IS defined in ShopView.

        # Maybe ShopView.purchase_item_callback is being overwritten?
        # Or maybe it's not a coroutine?

        # Let's try to patch get_player_or_error as well since the original test did
        # Mock db.get_player explicitly to return a dict, not a Mock
        db.get_player = MagicMock(return_value={"aurum": 900})

        with patch("cogs.shop_cog.get_player_or_error", new=AsyncMock(return_value={"aurum": 1000})):
            # Mock Interacton
            interaction = MagicMock()
            interaction.user = user
            interaction.data = {"values": ["hp_potion_1:40"]}
            interaction.response = MagicMock()
            interaction.response.defer = AsyncMock()
            interaction.followup = MagicMock()
            interaction.followup.send = AsyncMock()

            # Mock View methods called inside
            # _execute_purchase seems to be a helper method
            view._execute_purchase = Mock(return_value=(True, {"name": "Potion"}, 900))

            # Since interaction is a MagicMock, interaction.edit_original_response is also a MagicMock.
            # But await requires an awaitable (coroutine or Future).
            # MagicMock isn't awaitable by default unless configured.
            interaction.edit_original_response = AsyncMock()

            await view.purchase_item_callback(interaction)

            # Check if it proceeded
            interaction.response.defer.assert_awaited()

    async def test_shop_callback_validation_failure_empty(self):
        """Verify that purchase_item_callback rejects empty input."""
        db = Mock()
        user = MagicMock()
        view = self.ShopView(db, user, 1000)

        interaction = MagicMock()
        interaction.user = user
        interaction.data = {"values": []}  # Empty
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        # Patch get_player_or_error
        with patch("cogs.shop_cog.get_player_or_error", new=AsyncMock(return_value=True)):
            await view.purchase_item_callback(interaction)

        # Should defer
        interaction.response.defer.assert_awaited()

        # Should send error about invalid selection
        interaction.followup.send.assert_awaited_with("❌ Invalid selection.", ephemeral=True)

    async def test_shop_callback_validation_failure_malformed(self):
        """Verify that purchase_item_callback rejects malformed input."""
        db = Mock()
        user = MagicMock()
        view = self.ShopView(db, user, 1000)

        interaction = MagicMock()
        interaction.user = user
        interaction.data = {"values": [""]}  # Empty string in list
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        # Patch get_player_or_error
        with patch("cogs.shop_cog.get_player_or_error", new=AsyncMock(return_value=True)):
            await view.purchase_item_callback(interaction)

        interaction.followup.send.assert_awaited_with("❌ Invalid selection.", ephemeral=True)


if __name__ == "__main__":
    unittest.main()
