import asyncio
import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper Mocks
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


class MockSelectOption:
    def __init__(self, label=None, value=None, description=None, emoji=None, default=False):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default


class TestDoSPrevention(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to isolate imports
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Discord
        mock_discord = MagicMock()
        mock_discord.ButtonStyle.success = "success"
        mock_discord.ButtonStyle.danger = "danger"
        mock_discord.ButtonStyle.secondary = "secondary"
        mock_discord.ButtonStyle.primary = "primary"
        mock_discord.Color.dark_red.return_value = "dark_red"
        mock_discord.Color.dark_green.return_value = "dark_green"
        mock_discord.Color.dark_grey.return_value = "dark_grey"
        mock_discord.SelectOption = MockSelectOption

        sys.modules["discord"] = mock_discord

        # Mock Discord UI
        mock_ui = MagicMock()
        mock_ui.View = MockView
        mock_ui.Button = MockButton
        mock_ui.Select = MockSelect
        # Also need Item for inheritance if used
        mock_ui.Item = object

        sys.modules["discord.ui"] = mock_ui

        # Mock Dependencies
        sys.modules["pymongo"] = MagicMock()
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.ui_helpers"] = MagicMock()
        sys.modules["game_systems.adventure.ui.adventure_embeds"] = MagicMock()

        # Import module under test
        import game_systems.adventure.ui.exploration_view

        importlib.reload(game_systems.adventure.ui.exploration_view)

        self.ExplorationView = game_systems.adventure.ui.exploration_view.ExplorationView

        # Import PlayerStats
        from game_systems.player.player_stats import PlayerStats

        self.PlayerStats = PlayerStats

        # Setup test objects
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_stats = MagicMock(spec=self.PlayerStats)
        self.mock_stats.max_hp = 100

        # Setup manager
        self.mock_manager.simulate_adventure_step = MagicMock(return_value={})

        self.view = self.ExplorationView(
            db=self.mock_db,
            manager=self.mock_manager,
            location_id="test_loc",
            log=[],
            interaction_user=self.mock_user,
            player_stats=self.mock_stats,
            vitals={"current_hp": 100, "current_mp": 100},
            active_monster={"player_stance": "balanced"},
        )

    def tearDown(self):
        self.modules_patcher.stop()

    def test_huge_payload_stance_rejected(self):
        """Test sending a massive string as stance is REJECTED."""
        huge_string = "A" * 10_000  # 10KB string

        # Mock interaction
        interaction = AsyncMock()
        interaction.user.id = 12345
        interaction.data = {"values": [huge_string]}

        # Run async method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.view.action_stance(interaction))

            # Assert Manager was NOT called (Validation worked)
            self.mock_manager.simulate_adventure_step.assert_not_called()

            # Assert User got error message
            interaction.response.send_message.assert_called_with("Invalid action data.", ephemeral=True)
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
