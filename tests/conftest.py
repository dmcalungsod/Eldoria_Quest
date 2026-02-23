"""
Shared test fixtures — Eldoria Quest
-------------------------------------
Resolves order-dependent test failures caused by test files that replace
sys.modules["pymongo"] and sys.modules["discord"] with plain MagicMocks at
module level.

Strategy:
  - ``pytest_runtest_setup`` runs before *every* test and patches production
    module namespaces so that pymongo.errors.DuplicateKeyError is a real
    Exception subclass and discord.ui.{View,Button,Select} are concrete
    classes (not exhaustible MagicMocks with side_effect iterators).
"""

import sys


# ──────────────────────────────────────────────────────────────
# Real classes that replace problematic MagicMock bindings
# ──────────────────────────────────────────────────────────────
class _DuplicateKeyError(Exception):
    """Real Exception subclass so ``except DuplicateKeyError`` works."""


class _View:
    """Minimal stand-in for discord.ui.View."""

    def __init__(self, timeout=None):
        self.children = []

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children.clear()


_Item = object


class _Button(_Item):
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
        self.emoji = emoji
        self.row = row
        self.custom_id = custom_id
        self.disabled = disabled
        self.callback = None

    def _is_v2(self):
        return False


class _Select(_Item):
    """Minimal stand-in for discord.ui.Select."""

    def __init__(
        self,
        placeholder=None,
        min_values=1,
        max_values=1,
        options=None,
        row=None,
        custom_id=None,
    ):
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.options = options or []
        self.row = row
        self.custom_id = custom_id
        self.callback = None
        self.disabled = False

    def add_option(self, label=None, value=None, description=None, emoji=None):
        self.options.append({"label": label, "value": value})

    def _is_v2(self):
        return False


class _SelectOption:
    """Minimal stand-in for discord.SelectOption."""

    def __init__(self, label=None, value=None, description=None, emoji=None):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji


# ──────────────────────────────────────────────────────────────
# Patch helpers
# ──────────────────────────────────────────────────────────────


def _is_real_exc(obj):
    """Return True if *obj* is a real Exception class."""
    return isinstance(obj, type) and issubclass(obj, BaseException)


def _patch_duplicate_key_error():
    """Ensure DuplicateKeyError is a real Exception everywhere it matters."""

    # 1. Patch pymongo.errors in sys.modules (both the stand-alone entry
    #    AND the attribute on the pymongo parent mock).
    for key in ("pymongo.errors", "pymongo"):
        mod = sys.modules.get(key)
        if mod is None:
            continue
        target = mod if key == "pymongo.errors" else getattr(mod, "errors", None)
        if target is not None and not _is_real_exc(
            getattr(target, "DuplicateKeyError", None)
        ):
            target.DuplicateKeyError = _DuplicateKeyError

    # 2. Patch the locally-bound reference inside production modules.
    for mod_name in ("database.database_manager",):
        mod = sys.modules.get(mod_name)
        if mod is not None and not _is_real_exc(
            getattr(mod, "DuplicateKeyError", None)
        ):
            mod.DuplicateKeyError = _DuplicateKeyError

    # 3. Patch equipment_manager's pymongo reference.
    em = sys.modules.get("game_systems.items.equipment_manager")
    if em is not None:
        pymongo_ref = getattr(em, "pymongo", None)
        if pymongo_ref is not None:
            errors_ref = getattr(pymongo_ref, "errors", None)
            if errors_ref is not None and not _is_real_exc(
                getattr(errors_ref, "DuplicateKeyError", None)
            ):
                errors_ref.DuplicateKeyError = _DuplicateKeyError


def _patch_discord_ui():
    """Ensure discord.ui.{View,Button,Select} are real classes."""

    # Patch sys.modules["discord.ui"]
    discord_ui = sys.modules.get("discord.ui")
    if discord_ui is not None:
        if not isinstance(getattr(discord_ui, "View", None), type):
            discord_ui.View = _View
        if not isinstance(getattr(discord_ui, "Button", None), type):
            discord_ui.Button = _Button
        if not isinstance(getattr(discord_ui, "Select", None), type):
            discord_ui.Select = _Select
        if not isinstance(getattr(discord_ui, "Item", None), type):
            discord_ui.Item = _Item

    # Also patch the discord mock's ui attribute
    discord_mod = sys.modules.get("discord")
    if discord_mod is not None:
        ui = getattr(discord_mod, "ui", None)
        if ui is not None:
            if not isinstance(getattr(ui, "View", None), type):
                ui.View = _View
            if not isinstance(getattr(ui, "Button", None), type):
                ui.Button = _Button
            if not isinstance(getattr(ui, "Select", None), type):
                ui.Select = _Select
            if not isinstance(getattr(ui, "Item", None), type):
                ui.Item = _Item
        if not isinstance(getattr(discord_mod, "SelectOption", None), type):
            discord_mod.SelectOption = _SelectOption

    # Patch production modules that cached discord.ui.* at import time
    for mod_name in (
        "game_systems.adventure.ui.exploration_view",
        "cogs.skill_trainer_cog",
    ):
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        if not isinstance(getattr(mod, "Button", None), type):
            mod.Button = _Button
        if not isinstance(getattr(mod, "Select", None), type):
            mod.Select = _Select
        if not isinstance(getattr(mod, "View", None), type):
            mod.View = _View


def _patch_app_commands():
    """Ensure cogs that use @app_commands.command have real async callbacks.

    When discord is mocked at module level by other tests, the decorator
    wraps methods in MagicMock objects.  Purge and reimport affected modules
    so decorators resolve against the current (real or properly mocked)
    discord module.
    """
    import asyncio
    import importlib

    for mod_name, class_name, method_name in (
        ("cogs.developer_cog", "DeveloperCog", "dev_panel"),
    ):
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        cls = getattr(mod, class_name, None)
        if cls is None:
            continue
        method = getattr(cls, method_name, None)
        if method is None:
            continue
        cb = getattr(method, "callback", None)
        if cb is not None and asyncio.iscoroutinefunction(cb):
            continue  # Already valid
        if asyncio.iscoroutinefunction(method):
            continue  # Already valid
        # Stale MagicMock decorator — purge and reimport
        del sys.modules[mod_name]
        importlib.import_module(mod_name)


def _patch_all():
    _patch_duplicate_key_error()
    _patch_discord_ui()
    _patch_app_commands()


# ──────────────────────────────────────────────────────────────
# Hooks
# ──────────────────────────────────────────────────────────────


def pytest_collection_modifyitems(config, items):
    """Re-patch after all test modules have been collected."""
    _patch_all()


def pytest_runtest_setup(item):
    """Re-patch before EVERY test to catch late sys.modules clobbers."""
    _patch_all()
