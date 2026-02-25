import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Helper Mocks
class MockView:
    def __init__(self, timeout=None):
        self.children = []
        self.timeout = timeout

    def add_item(self, item):
        self.children.append(item)

class MockButton:
    def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None, disabled=False):
        self.label = label
        self.style = style
        self.custom_id = custom_id
        self.emoji = emoji
        self.row = row
        self.disabled = disabled
        self.callback = None

class MockSelect:
    def __init__(self, placeholder=None, min_values=1, max_values=1, row=None, options=None):
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.row = row
        self.options = options or []
        self.callback = None
        self.values = []
        self.disabled = False

    def add_option(self, label, value, description=None, emoji=None):
        opt = MagicMock()
        opt.label = label
        opt.value = value
        opt.description = description
        opt.emoji = emoji
        self.options.append(opt)

class TestSetupView(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock Pymongo
        mock_pymongo = MagicMock()
        mock_pymongo.errors = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = mock_pymongo.errors

        # Mock Discord
        mock_discord = MagicMock()
        mock_ui = MagicMock()
        mock_ui.View = MockView
        mock_ui.Button = MockButton
        mock_ui.Select = MockSelect

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_ui
        sys.modules["discord.ext"] = MagicMock()

        # Mock dependencies
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.utils.ui_helpers"] = MagicMock()
        sys.modules["game_systems.adventure.ui.adventure_embeds"] = MagicMock()
        sys.modules["game_systems.adventure.ui.status_view"] = MagicMock()

        # Mock LOCATIONS
        self.mock_locations = {
            "forest": {"name": "Forest", "min_rank": "F", "level_req": 1}
        }

        with patch("game_systems.adventure.ui.setup_view.LOCATIONS", self.mock_locations):
            import game_systems.adventure.ui.setup_view
            importlib.reload(game_systems.adventure.ui.setup_view)
            self.AdventureSetupView = game_systems.adventure.ui.setup_view.AdventureSetupView

    def tearDown(self):
        self.modules_patcher.stop()

    def test_setup_view_supplies_max_values(self):
        """Test that max_values adjusts based on supply count."""
        mock_db = MagicMock()
        mock_manager = MagicMock()
        mock_user = MagicMock()

        # Case 1: 5 different supplies -> max 3
        supplies = [
            {"item_key": f"item_{i}", "item_name": f"Item {i}", "count": 1}
            for i in range(5)
        ]

        view = self.AdventureSetupView(
            mock_db, mock_manager, mock_user,
            player_rank="F", player_level=1, supplies=supplies
        )

        # Supply select is 3rd item (index 2)
        supply_select = view.children[2]
        self.assertEqual(supply_select.max_values, 3)
        self.assertEqual(len(supply_select.options), 5)

        # Case 2: 2 different supplies -> max 2
        supplies = [
            {"item_key": "item_1", "item_name": "Item 1", "count": 1},
            {"item_key": "item_2", "item_name": "Item 2", "count": 1}
        ]

        view = self.AdventureSetupView(
            mock_db, mock_manager, mock_user,
            player_rank="F", player_level=1, supplies=supplies
        )

        supply_select = view.children[2]
        self.assertEqual(supply_select.max_values, 2)
        self.assertEqual(len(supply_select.options), 2)

    def test_supply_callback_stores_list(self):
        """Test that supply callback stores values as list."""
        mock_db = MagicMock()
        mock_manager = MagicMock()
        mock_user = MagicMock()

        supplies = [{"item_key": "item_1", "item_name": "Item 1", "count": 1}]

        view = self.AdventureSetupView(
            mock_db, mock_manager, mock_user,
            player_rank="F", player_level=1, supplies=supplies
        )

        interaction = MagicMock()
        interaction.response = MagicMock()
        interaction.response.edit_message = AsyncMock()

        # Simulate selection
        view.supply_select.values = ["item_1"]

        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(view.supply_callback(interaction))
        loop.close()

        self.assertEqual(view.selected_supplies, ["item_1"])

    def test_start_callback_passes_supplies(self):
        """Test that start_callback passes supplies dictionary."""
        mock_db = MagicMock()
        mock_manager = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 12345

        supplies = [{"item_key": "item_1", "item_name": "Item 1", "count": 1}]

        view = self.AdventureSetupView(
            mock_db, mock_manager, mock_user,
            player_rank="F", player_level=1, supplies=supplies
        )

        view.selected_location = "forest"
        view.selected_duration = 30
        view.selected_supplies = ["item_1"]

        interaction = MagicMock()
        interaction.user.id = 12345
        interaction.response = MagicMock()
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        async def mock_get_player(*args, **kwargs):
            return True

        with patch("game_systems.adventure.ui.setup_view.get_player_or_error", side_effect=mock_get_player):
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(view.start_callback(interaction))
            loop.close()

            # Check manager.start_adventure call
            mock_manager.start_adventure.assert_called()
            args, kwargs = mock_manager.start_adventure.call_args
            # args: (user_id, loc, duration)
            # kwargs: supplies
            self.assertEqual(kwargs["supplies"], {"item_1": 1})

if __name__ == "__main__":
    unittest.main()
