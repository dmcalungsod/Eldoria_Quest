import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Discord
mock_discord = MagicMock()
mock_discord.ButtonStyle.success = "success"
mock_discord.ButtonStyle.danger = "danger"
mock_discord.ButtonStyle.secondary = "secondary"
mock_discord.ButtonStyle.primary = "primary"
mock_discord.Color.dark_red.return_value = "dark_red"
mock_discord.Color.dark_green.return_value = "dark_green"
mock_discord.Color.dark_grey.return_value = "dark_grey"


class MockSelectOption:
    def __init__(self, label=None, value=None, description=None, emoji=None, default=False):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default


mock_discord.SelectOption = MockSelectOption


# Mock Discord UI
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children.clear()


class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.emoji = emoji
        self.row = row
        self.callback = None
        self.disabled = False


class MockSelect:
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
        self.options = options
        self.row = row
        self.custom_id = custom_id
        self.callback = None
        self.disabled = False
        self.values = []


mock_ui = MagicMock()
mock_ui.View = MockView
mock_ui.Button = MockButton
mock_ui.Select = MockSelect
mock_ui.Item = object

# Now import the module under test
# We do NOT mock modules globally to avoid polluting other tests
# Instead we patch them in setUp or context managers if possible
# But imports need them to exist.
# Better pattern: Use patch.dict in setUp, but we need to import ExplorationView first.
# If ExplorationView imports cogs, cogs must exist.
# The real cogs package exists. Let's rely on that if possible, OR
# restore sys.modules in tearDownModule or similar.

# Actually, to prevent pollution, we should NOT set sys.modules['cogs'] = MagicMock() globally
# if we can avoid it.
# However, if ExplorationView imports cogs.utils.ui_helpers, and we want to mock it...

# Strategy: Use unittest.mock.patch.dict on sys.modules context manager around the import?
# No, the import persists.

# Better Strategy: Manually restore sys.modules at the end of the module execution?
# Or use setUp/tearDown to patch sys.modules.
# But we need to import the class to test it.

# If we mock sys.modules['cogs'], we must ensure it behaves like a package if others need it.
# A simple MagicMock is not a package.
# We can make it a package-like mock?
# mock_cogs = MagicMock()
# mock_cogs.__path__ = []

# But better: Just Don't Mock 'cogs' globally if it exists!
# The code imports `cogs.utils.ui_helpers`.
# Let's mock `cogs.utils.ui_helpers` specifically, NOT `cogs`.

# We defer imports to setUp to avoid global sys.modules pollution
# from game_systems.adventure.ui.exploration_view import ExplorationView
# from game_systems.player.player_stats import PlayerStats


class TestExplorationFeedback(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch sys.modules contextually
        self.modules_patcher = patch.dict(
            sys.modules,
            {
                "discord": mock_discord,
                "discord.ui": mock_ui,
                "pymongo": MagicMock(),
                "pymongo.errors": MagicMock(),
                "cogs.utils.ui_helpers": MagicMock(),
                "game_systems.adventure.ui.adventure_embeds": MagicMock(),
            },
        )
        self.modules_patcher.start()

        # Setup mocks for AdventureEmbeds return value
        sys.modules[
            "game_systems.adventure.ui.adventure_embeds"
        ].AdventureEmbeds.build_exploration_embed.return_value = MagicMock()

        # Import modules under test INSIDE the patched context
        # Reload to ensure they use our fresh mocks
        import importlib

        import game_systems.adventure.ui.exploration_view
        import game_systems.player.player_stats

        importlib.reload(game_systems.adventure.ui.exploration_view)

        self.ExplorationView = game_systems.adventure.ui.exploration_view.ExplorationView
        self.PlayerStats = game_systems.player.player_stats.PlayerStats

        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.stats = MagicMock(spec=self.PlayerStats)
        self.stats.max_hp = 100

    async def asyncTearDown(self):
        self.modules_patcher.stop()

    async def test_feedback_combat(self):
        """Verify footer updates during combat simulation."""
        # Setup manager mock to return a valid result with sequence
        self.mock_manager.simulate_adventure_step.return_value = {
            "sequence": [["Log entry 1"], ["Log entry 2"]],
            "dead": False,
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_stats": self.stats,
            "active_monster": None,
        }

        active_monster = {"name": "Goblin", "hp": 50}
        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=active_monster,
            class_id=1,
        )

        interaction = MagicMock()
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        # Mock message embed
        mock_embed = MagicMock()
        mock_embed.footer.text = "Old Footer"
        interaction.message.embeds = [mock_embed]

        # Execute
        await view._perform_simulation(interaction, action="attack")

        # Verify
        interaction.response.defer.assert_called_once()

        # We check the FIRST call to edit_original_response
        first_call = interaction.edit_original_response.await_args_list[0]
        kwargs = first_call.kwargs

        # Assert that 'embed' was passed and contains the new footer
        # Currently expected to fail
        self.assertIn("embed", kwargs, "Embed should be updated in the first response edit")

        mock_embed.set_footer.assert_called_with(text="⚔️ Resolving combat...")

    async def test_feedback_exploration(self):
        """Verify footer updates during exploration simulation."""
        self.mock_manager.simulate_adventure_step.return_value = {
            "sequence": [["Log entry 1"], ["Log entry 2"]],
            "dead": False,
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_stats": self.stats,
            "active_monster": None,
        }

        view = self.ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=None,
            class_id=1,
        )

        interaction = MagicMock()
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        mock_embed = MagicMock()
        mock_embed.footer.text = "Old Footer"
        interaction.message.embeds = [mock_embed]

        await view._perform_simulation(interaction, action=None)

        interaction.response.defer.assert_called_once()

        first_call = interaction.edit_original_response.await_args_list[0]
        kwargs = first_call.kwargs
        # Currently expected to fail
        self.assertIn("embed", kwargs)

        mock_embed.set_footer.assert_called_with(text="🥾 Exploring...")
