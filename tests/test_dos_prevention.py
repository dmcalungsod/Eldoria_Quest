
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_systems.player.player_stats import PlayerStats


class TestDoSPrevention(unittest.TestCase):
    def setUp(self):
        # 1. Mock dependencies
        self.mock_discord = MagicMock()
        self.mock_discord.ButtonStyle.success = "success"
        self.mock_discord.ButtonStyle.danger = "danger"
        self.mock_discord.ButtonStyle.secondary = "secondary"
        self.mock_discord.ButtonStyle.primary = "primary"
        self.mock_discord.Color.dark_red.return_value = "dark_red"
        self.mock_discord.Color.dark_green.return_value = "dark_green"
        self.mock_discord.Color.dark_grey.return_value = "dark_grey"

        # Mock View/Button logic
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

        class MockSelectOption:
            def __init__(self, label=None, value=None, description=None, emoji=None, default=False):
                self.label = label
                self.value = value
                self.description = description
                self.emoji = emoji
                self.default = default

        self.mock_discord.SelectOption = MockSelectOption
        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MockButton
        self.mock_discord.ui.Select = MockSelect

        # Patch modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord.ui,
            "pymongo": MagicMock(),
            "cogs.ui_helpers": MagicMock(),
            "game_systems.adventure.ui.adventure_embeds": MagicMock(),
        })
        self.modules_patcher.start()

        # Import module under test (reloading if necessary)
        if "game_systems.adventure.ui.exploration_view" in sys.modules:
            del sys.modules["game_systems.adventure.ui.exploration_view"]

        import game_systems.adventure.ui.exploration_view
        self.ExplorationView = game_systems.adventure.ui.exploration_view.ExplorationView

        # Test setup
        self.mock_db = MagicMock()
        self.mock_manager = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 12345
        self.mock_stats = MagicMock(spec=PlayerStats)
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
            active_monster={"player_stance": "balanced"}
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

        loop.run_until_complete(self.view.action_stance(interaction))

        # Assert Manager was NOT called (Validation worked)
        self.mock_manager.simulate_adventure_step.assert_not_called()

        # Assert User got error message
        interaction.response.send_message.assert_called_with("Invalid action data.", ephemeral=True)

        loop.close()

if __name__ == "__main__":
    unittest.main()
