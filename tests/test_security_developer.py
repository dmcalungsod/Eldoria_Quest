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
from unittest.mock import AsyncMock, MagicMock, Mock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Minimal stand-in classes ────────────────────────────────────────────


class _Cog:
    """Minimal stand-in for discord.ext.commands.Cog."""

    def __init__(self, bot=None, *args, **kwargs):
        self.bot = bot

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


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

    def __init__(self, label=None, style=None, emoji=None, row=None, custom_id=None, disabled=False):
        self.label = label
        self.style = style
        self.disabled = disabled
        self.callback = None

    def _is_v2(self):
        return False


# ── Pollution-safe helpers ──────────────────────────────────────────────


def _is_mock(obj):
    return isinstance(obj, (Mock, MagicMock))


def _safe_mock(**kwargs):
    """Create a Mock, dropping ``spec`` when the target is itself a Mock."""
    spec = kwargs.get("spec")
    if spec is not None and _is_mock(spec):
        kwargs.pop("spec")
    return Mock(**kwargs)


def _transparent_command(*args, **kwargs):
    """Mimic ``@app_commands.command(...)`` — preserves the real async func."""

    def decorator(func):
        cmd = MagicMock()
        cmd.callback = func
        cmd.error = lambda f: f  # @dev_panel.error pass-through
        return cmd

    return decorator


def _load_developer_cog():
    """(Re-)import DeveloperCog with a safe discord mock environment.

    Ensures that even when ``sys.modules["discord"]`` is a MagicMock
    (test pollution from other files), the critical pieces—``commands.Cog``,
    ``app_commands.command``, ``ui.View``, ``ui.Button``—resolve to real
    classes / functions so that ``DeveloperCog`` becomes a proper class
    with an async ``dev_panel`` callback.
    """
    discord_mod = sys.modules.get("discord")

    if discord_mod is not None and _is_mock(discord_mod):
        # ── Patch commands.Cog ──
        ext = getattr(discord_mod, "ext", None)
        if ext is None or _is_mock(ext):
            discord_mod.ext = MagicMock()
            ext = discord_mod.ext
        cmds = getattr(ext, "commands", None)
        if cmds is None or _is_mock(cmds):
            ext.commands = MagicMock()
            cmds = ext.commands
        # Also register in sys.modules so `from discord.ext import commands` works
        sys.modules["discord.ext"] = ext
        sys.modules["discord.ext.commands"] = cmds
        cmds.Cog = _Cog

        # ── Patch app_commands.command ──
        ac = getattr(discord_mod, "app_commands", None)
        if ac is None or _is_mock(ac):
            discord_mod.app_commands = MagicMock()
            ac = discord_mod.app_commands
        ac.command = _transparent_command

        # ── Patch ui classes ──
        ui = getattr(discord_mod, "ui", None)
        if ui is None or _is_mock(ui):
            discord_mod.ui = MagicMock()
            ui = discord_mod.ui
        sys.modules["discord.ui"] = ui
        ui.View = _View
        ui.Button = _Button
        ui.button = lambda *a, **kw: lambda f: f

    # Purge stale cached module and reimport fresh
    sys.modules.pop("cogs.developer_cog", None)
    import cogs.developer_cog as mod

    return mod.DeveloperCog


def _get_callback(cog):
    """Extract the original ``async def dev_panel`` from the cog instance."""
    dev_panel = cog.dev_panel
    cb = getattr(dev_panel, "callback", None)

    if cb is not None and asyncio.iscoroutinefunction(cb):
        return cb
    if asyncio.iscoroutinefunction(dev_panel):
        return dev_panel

    raise TypeError(
        f"Could not extract async callback from dev_panel "
        f"(type={type(dev_panel).__name__}, "
        f"callback type={type(cb).__name__ if cb else 'None'})"
    )


# ── Tests ───────────────────────────────────────────────────────────────


class TestSecurityDeveloper(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.DeveloperCog = _load_developer_cog()

    async def test_dev_panel_access_denied_for_non_owner(self):
        """Verify that dev_panel denies access to non-owners."""
        bot = _safe_mock()
        bot.is_owner = AsyncMock(return_value=False)

        cog = self.DeveloperCog(bot)

        interaction = _safe_mock()
        interaction.user = _safe_mock()
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()

        cog.db = Mock()
        cog.db.get_player = Mock(return_value=None)

        callback = _get_callback(cog)
        await callback(cog, interaction)

        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.send_message.assert_awaited_with("⛔ You are not the bot owner.", ephemeral=True)
        interaction.response.defer.assert_not_awaited()

    async def test_dev_panel_access_granted_for_owner(self):
        """Verify that dev_panel grants access to owners."""
        bot = _safe_mock()
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

        interaction = _safe_mock()
        interaction.user = _safe_mock()
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        callback = _get_callback(cog)
        await callback(cog, interaction)

        bot.is_owner.assert_awaited_once_with(interaction.user)
        interaction.response.defer.assert_awaited_with(ephemeral=True)


if __name__ == "__main__":
    unittest.main()
