import unittest
from unittest.mock import AsyncMock, Mock, MagicMock
import discord
from discord.ext import commands
import sys
import os
import importlib

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure we import the module, but we will reload it in setUp if needed
try:
    from cogs.developer_cog import DeveloperCog
except ImportError:
    DeveloperCog = None


class TestSecurityDeveloper(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # 1. Check if 'discord' is currently a Mock (due to other tests)
        #    If so, we need to ensure app_commands.command works as a decorator
        #    that preserves the callback function.
        if isinstance(discord, (Mock, MagicMock)) or hasattr(discord, "call_args"):
            # Ensure app_commands exists on the mock
            if not getattr(discord, "app_commands", None):
                discord.app_commands = MagicMock()

            # Define side_effect to simulate @app_commands.command(...)
            def command_decorator_factory(*args, **kwargs):
                def decorator(func):
                    # Return a Mock representing the Command
                    cmd_mock = MagicMock()
                    # CRITICAL: Attach the original function as .callback
                    # so the test can await cog.dev_panel.callback(...)
                    cmd_mock.callback = func
                    return cmd_mock

                return decorator

            discord.app_commands.command.side_effect = command_decorator_factory

            # 2. Force reload cogs.developer_cog to apply this decorator logic
            if "cogs.developer_cog" in sys.modules:
                importlib.reload(sys.modules["cogs.developer_cog"])

        # 3. Import/Re-import class after potential reload
        from cogs.developer_cog import DeveloperCog as DC

        self.DeveloperCog = DC

    async def test_dev_panel_access_denied_for_non_owner(self):
        """
        Verify that dev_panel denies access to non-owners.
        """
        # Setup Mock Bot
        bot = Mock(spec=commands.Bot)
        bot.is_owner = AsyncMock(return_value=False)

        # Setup Cog using the class from setUp
        cog = self.DeveloperCog(bot)

        # Setup Mock Interaction
        interaction = Mock(spec=discord.Interaction)
        interaction.user = Mock(spec=discord.User)
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()

        # Mock db calls
        cog.db = Mock()
        cog.db.get_player = Mock(return_value=None)

        # Run Command Handler directly
        # If the environment is correct, .callback is the async function
        await cog.dev_panel.callback(cog, interaction)

        # Assertions
        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.send_message.assert_awaited_with(
            "⛔ You are not the bot owner.", ephemeral=True
        )
        interaction.response.defer.assert_not_awaited()

    async def test_dev_panel_access_granted_for_owner(self):
        """Verify that dev_panel grants access to owners."""
        bot = Mock(spec=commands.Bot)
        bot.is_owner = AsyncMock(return_value=True)

        cog = self.DeveloperCog(bot)
        cog.db = Mock()
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

        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.defer.assert_awaited_with(ephemeral=True)


if __name__ == "__main__":
    unittest.main()
