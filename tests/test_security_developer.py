"""
Security tests for developer_cog.py — verifies owner-only access to dev_panel.

Handles test pollution: other test files mock ``discord`` at module level
during pytest collection.  This module patches the critical parts of the
mocked discord (Cog base class, app_commands.command decorator, ui classes)
to be real objects, then reimports ``cogs.developer_cog`` in a clean state.
"""

import asyncio
import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Minimal stand-in classes ────────────────────────────────────────────


class _Cog:
    """Minimal stand-in for discord.ext.commands.Cog."""

    def __init__(self, bot=None, *args, **kwargs):
        self.bot = bot


class _View:
    """Minimal stand-in for discord.ui.View."""

    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children.clear()


class _Button:
    """Minimal stand-in for discord.ui.Button."""

    def __init__(
        self,
        label=None,
        style=None,
        emoji=None,
        row=None,
        custom_id=None,
        disabled=False,
    ):
        self.label = label
        self.style = style
        self.disabled = disabled
        self.callback = None

    def _is_v2(self):
        return False


# ── Helper to load cog with patched dependencies ───────────────────────


def _load_developer_cog():
    """Load DeveloperCog with mocked dependencies in a clean environment."""

    # Create fresh mocks for discord and pymongo
    mock_discord = MagicMock()
    mock_discord.ext.commands.Cog = _Cog
    mock_discord.ui.View = _View
    mock_discord.ui.Button = _Button

    # Mock app_commands.command decorator
    def command_decorator(*args, **kwargs):
        def decorator(func):
            # Attach the callback directly to the function wrapper
            func.callback = func
            # Mock the .error decorator
            func.error = lambda f: f
            return func

        return decorator

    mock_discord.app_commands.command = command_decorator

    # Create module dictionary to patch
    modules_to_patch = {
        "discord": mock_discord,
        "discord.ext": mock_discord.ext,
        "discord.ext.commands": mock_discord.ext.commands,
        "discord.app_commands": mock_discord.app_commands,
        "discord.ui": mock_discord.ui,
        "pymongo": MagicMock(),
        "pymongo.errors": MagicMock(),
        "database.database_manager": MagicMock(),  # Mock DB manager
    }

    # Apply patches and import the cog
    with patch.dict(sys.modules, modules_to_patch):
        # Force reload to pick up the patched modules
        if "cogs.developer_cog" in sys.modules:
            del sys.modules["cogs.developer_cog"]

        import cogs.developer_cog

        importlib.reload(cogs.developer_cog)
        return cogs.developer_cog.DeveloperCog


# ── Tests ───────────────────────────────────────────────────────────────


class TestSecurityDeveloper(unittest.IsolatedAsyncioTestCase):

    async def test_dev_panel_access_denied_for_non_owner(self):
        """Verify that dev_panel denies access to non-owners."""
        DeveloperCog = _load_developer_cog()

        bot = MagicMock()
        bot.is_owner = AsyncMock(return_value=False)

        cog = DeveloperCog(bot)

        # Mock DB interaction in the cog
        cog.db = MagicMock()

        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()

        # Execute the command callback
        # Since we mocked the decorator to return the function, cog.dev_panel is the bound method.
        await cog.dev_panel(interaction)

        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.send_message.assert_awaited_with(
            "⛔ You are not the bot owner.", ephemeral=True
        )
        interaction.response.defer.assert_not_awaited()

    async def test_dev_panel_access_granted_for_owner(self):
        """Verify that dev_panel grants access to owners."""
        DeveloperCog = _load_developer_cog()

        bot = MagicMock()
        bot.is_owner = AsyncMock(return_value=True)

        cog = DeveloperCog(bot)

        # Mock DB data
        cog.db = MagicMock()
        cog.db.get_player.return_value = {
            "name": "Owner",
            "experience": 0,
            "aurum": 0,
            "vestige_pool": 0,
        }
        cog.db.get_active_boosts.return_value = []

        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()

        await cog.dev_panel(interaction)

        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.defer.assert_awaited_with(ephemeral=True)


if __name__ == "__main__":
    unittest.main()
