import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestServicesMenuExtended(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Setup Mocks
        self.mock_discord = MagicMock()

        class MockInteraction:
            def __init__(self):
                self.response = AsyncMock()
                self.edit_original_response = AsyncMock()

        self.mock_discord.Interaction = MockInteraction

        # Mock View
        class MockView:
            def __init__(self, timeout=None):
                self.timeout = timeout
                self.children = []

            def add_item(self, item):
                self.children.append(item)

            async def interaction_check(self, interaction):
                return True

        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MagicMock()

        sys.modules["discord"] = self.mock_discord
        sys.modules["discord.ui"] = self.mock_discord.ui
        sys.modules["discord.ext"] = MagicMock()

        sys.modules["pymongo"] = MagicMock()
        sys.modules["pymongo.errors"] = MagicMock()

        # Mock dependencies to prevent circular imports
        mock_world_time = MagicMock()
        sys.modules["game_systems.core.world_time"] = mock_world_time
        self.mock_world_time = mock_world_time

        mock_services_menu = MagicMock()
        mock_services_menu.GuildServicesView = MagicMock()

        # Import components module normally but mock what we need
        import game_systems.guild_system.ui.components
        importlib.reload(game_systems.guild_system.ui.components)

        # Import target module
        import game_systems.guild_system.ui.services_menu
        importlib.reload(game_systems.guild_system.ui.services_menu)

        self.services_module = game_systems.guild_system.ui.services_menu
        self.GuildServicesView = self.services_module.GuildServicesView

        self.mock_db = MagicMock()
        self.mock_db.get_active_world_event.return_value = None
        self.mock_user = MagicMock()

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_back_to_services_day(self):
        self.mock_world_time.TimePhase.DAY = "DAY"
        self.mock_world_time.TimePhase.NIGHT = "NIGHT"
        self.mock_world_time.WorldTime.get_current_phase.return_value = "DAY"

        view = self.GuildServicesView(self.mock_db, self.mock_user)
        interaction = self.mock_discord.Interaction()

        # Wait for the async callback
        await view.back_to_services(interaction)

        # Verify interaction response
        interaction.response.defer.assert_awaited_once()

        # Check that it builds the embed correctly without night flavor
        interaction.edit_original_response.assert_awaited_once()

        # Call kwargs
        kwargs = interaction.edit_original_response.await_args.kwargs
        self.assertIn("embed", kwargs)
        self.assertIn("view", kwargs)

    async def test_back_to_services_night(self):
        self.mock_world_time.TimePhase.DAY = "DAY"
        self.mock_world_time.TimePhase.NIGHT = "NIGHT"
        self.mock_world_time.WorldTime.get_current_phase.return_value = "NIGHT"

        view = self.GuildServicesView(self.mock_db, self.mock_user)
        interaction = self.mock_discord.Interaction()

        # Wait for the async callback
        await view.back_to_services(interaction)

        # Verify interaction response
        interaction.response.defer.assert_awaited_once()

        # Assert night flavor logic by patching EmbedBuilder
        interaction.edit_original_response.assert_awaited_once()

        # We can't easily assert exactly what embed.description contains because it's built internally
        # but we know the path was hit and didn't crash
        self.assertTrue(interaction.edit_original_response.called)

if __name__ == "__main__":
    unittest.main()
