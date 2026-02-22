
import pytest
from unittest.mock import AsyncMock, Mock
import discord
from discord.ext import commands

# Need to adjust import path for modules
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cogs.developer_cog import DeveloperCog  # noqa: E402


@pytest.mark.asyncio
async def test_dev_panel_access_denied_for_non_owner():
    """
    Verify that dev_panel denies access to non-owners.
    This test simulates calling the command handler directly, bypassing decorators.
    A secure implementation must perform the check INSIDE the handler.
    """
    # Setup Mock Bot
    bot = Mock(spec=commands.Bot)
    bot.is_owner = AsyncMock(return_value=False)

    # Setup Cog
    cog = DeveloperCog(bot)

    # Setup Mock Interaction
    interaction = Mock(spec=discord.Interaction)
    interaction.user = Mock(spec=discord.User)
    interaction.response = Mock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()

    # We need to mock db calls to avoid errors if it proceeds (i.e. fails check)
    cog.db = Mock()
    # In real code, these are sync methods called via to_thread, so use standard Mock
    cog.db.get_player = Mock(return_value=None)

    # Run Command Handler directly
    await cog.dev_panel.callback(cog, interaction)

    # Assertions for SECURE behavior
    # 1. bot.is_owner should be called
    bot.is_owner.assert_awaited_once_with(interaction.user)

    # 2. Should send denial message
    interaction.response.send_message.assert_awaited_with(
        "⛔ You are not the bot owner.", ephemeral=True
    )

    # 3. Should NOT defer (which implies successful start of command logic)
    interaction.response.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_dev_panel_access_granted_for_owner():
    """Verify that dev_panel grants access to owners."""
    bot = Mock(spec=commands.Bot)
    bot.is_owner = AsyncMock(return_value=True)

    cog = DeveloperCog(bot)
    cog.db = Mock()
    # Sync mocks for to_thread
    cog.db.get_player = Mock(
        return_value={
            "name": "Owner",
            "experience": 0,
            "aurum": 0,
            "vestige_pool": 0,
        }
    )
    cog.db.get_active_boosts = Mock(return_value=[])

    interaction = Mock(spec=discord.Interaction)
    interaction.user = Mock(spec=discord.User)
    interaction.response = Mock()
    interaction.response.defer = AsyncMock()
    interaction.followup = Mock()
    interaction.followup.send = AsyncMock()

    await cog.dev_panel.callback(cog, interaction)

    # Should check owner
    bot.is_owner.assert_awaited_once_with(interaction.user)

    # Should defer (indicating success)
    interaction.response.defer.assert_awaited_with(ephemeral=True)
