import unittest
from unittest.mock import AsyncMock, Mock, patch
import discord
import sys
import os
import importlib

# Need to adjust import path for modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import normally
try:
    from cogs.shop_cog import ShopView
except ImportError:
    ShopView = None


class TestSecurityShop(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Force reload cogs.shop_cog to ensure ShopView is the real class
        # and not a Mock object left over from previous tests.
        if "cogs.shop_cog" in sys.modules:
            importlib.reload(sys.modules["cogs.shop_cog"])

        # Re-import after reload
        from cogs.shop_cog import ShopView as SV

        self.ShopView = SV

    async def test_shop_callback_validation_success(self):
        """Verify that purchase_item_callback accepts valid input."""
        db = Mock()
        user = Mock(spec=discord.User)
        user.id = 12345

        # Use the fresh class
        view = self.ShopView(db, user, 1000)

        # Mock internal method to avoid DB calls
        view._execute_purchase = Mock(return_value=(True, {"name": "Potion"}, 900))

        # Mock Interaction with VALID data
        interaction = Mock(spec=discord.Interaction)
        interaction.user = user
        interaction.data = {"values": ["hp_potion_1:40"]}
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        with patch(
            "cogs.shop_cog.get_player_or_error",
            new=AsyncMock(return_value={"aurum": 1000}),
        ):
            # Mock db.get_player for the fresh fetch at the end
            db.get_player = Mock(return_value={"aurum": 900})

            await view.purchase_item_callback(interaction)

        # Should proceed
        interaction.response.defer.assert_awaited()
        view._execute_purchase.assert_called_with("hp_potion_1")

    async def test_shop_callback_validation_failure_empty(self):
        """Verify that purchase_item_callback rejects empty input."""
        db = Mock()
        user = Mock(spec=discord.User)
        view = self.ShopView(db, user, 1000)

        interaction = Mock(spec=discord.Interaction)
        interaction.user = user
        interaction.data = {"values": []}  # Empty
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        with patch(
            "cogs.shop_cog.get_player_or_error", new=AsyncMock(return_value=True)
        ):
            await view.purchase_item_callback(interaction)

        # Should NOT defer (or defer then send error)
        # My code defers first, then checks.
        interaction.response.defer.assert_awaited()

        # Should send error
        interaction.followup.send.assert_awaited_with(
            "❌ Invalid selection.", ephemeral=True
        )

    async def test_shop_callback_validation_failure_malformed(self):
        """Verify that purchase_item_callback rejects malformed input."""
        # My validation checks `values` presence.
        # `values[0]` checks truthiness.
        db = Mock()
        user = Mock(spec=discord.User)
        view = self.ShopView(db, user, 1000)

        interaction = Mock(spec=discord.Interaction)
        interaction.user = user
        interaction.data = {"values": [""]}  # Empty string in list
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        with patch(
            "cogs.shop_cog.get_player_or_error", new=AsyncMock(return_value=True)
        ):
            await view.purchase_item_callback(interaction)

        interaction.followup.send.assert_awaited_with(
            "❌ Invalid selection.", ephemeral=True
        )


if __name__ == "__main__":
    unittest.main()
