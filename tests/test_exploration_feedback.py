import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

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
    def __init__(self, placeholder=None, min_values=1, max_values=1, options=None, row=None, custom_id=None):
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

# Apply patches before importing the module under test
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_ui
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["cogs"] = MagicMock()
sys.modules["cogs.ui_helpers"] = MagicMock()
# Mock AdventureEmbeds to return a simple mock
mock_embeds = MagicMock()
mock_embeds.AdventureEmbeds.build_exploration_embed.return_value = MagicMock()
sys.modules["game_systems.adventure.ui.adventure_embeds"] = mock_embeds

# Now import the module under test
from game_systems.adventure.ui.exploration_view import ExplorationView
from game_systems.player.player_stats import PlayerStats

class TestExplorationFeedback(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.stats = MagicMock(spec=PlayerStats)
        self.stats.max_hp = 100

    async def test_feedback_combat(self):
        """Verify footer updates during combat simulation."""
        # Setup manager mock to return a valid result with sequence
        self.mock_manager.simulate_adventure_step.return_value = {
            "sequence": [["Log entry 1"], ["Log entry 2"]],
            "dead": False,
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_stats": self.stats,
            "active_monster": None
        }

        active_monster = {"name": "Goblin", "hp": 50}
        view = ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=active_monster,
            class_id=1
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
        self.assertIn('embed', kwargs, "Embed should be updated in the first response edit")

        mock_embed.set_footer.assert_called_with(text="⚔️ Resolving combat...")

    async def test_feedback_exploration(self):
        """Verify footer updates during exploration simulation."""
        self.mock_manager.simulate_adventure_step.return_value = {
            "sequence": [["Log entry 1"], ["Log entry 2"]],
            "dead": False,
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_stats": self.stats,
            "active_monster": None
        }

        view = ExplorationView(
            self.mock_db,
            self.mock_manager,
            "loc_1",
            [],
            self.mock_user,
            self.stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster=None,
            class_id=1
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
        self.assertIn('embed', kwargs)

        mock_embed.set_footer.assert_called_with(text="🥾 Exploring...")
