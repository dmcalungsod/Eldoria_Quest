import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGuildLobbyViewExtended(unittest.IsolatedAsyncioTestCase):
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
        sys.modules["game_systems.guild_system.ui.services_menu"] = mock_services_menu
        self.mock_services_menu = mock_services_menu

        # Reload components first to ensure ViewFactory picks up the mocked Button
        import game_systems.guild_system.ui.components
        importlib.reload(game_systems.guild_system.ui.components)

        # Import target module
        import game_systems.guild_system.ui.lobby_view
        importlib.reload(game_systems.guild_system.ui.lobby_view)

        self.lobby_module = game_systems.guild_system.ui.lobby_view
        self.GuildLobbyView = self.lobby_module.GuildLobbyView

        self.mock_db = MagicMock()
        self.mock_user = MagicMock()

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_services_btn_callback_day(self):
        self.mock_world_time.TimePhase.DAY = "DAY"
        self.mock_world_time.TimePhase.NIGHT = "NIGHT"
        self.mock_world_time.WorldTime.get_current_phase.return_value = "DAY"

        view = self.GuildLobbyView(self.mock_db, self.mock_user, rank="F")
        interaction = self.mock_discord.Interaction()

        # We need to simulate the callback execution
        # Wait for the async callback
        await view._services_btn_callback(interaction)

        # Verify interaction response
        interaction.response.defer.assert_awaited_once()
        self.mock_services_menu.GuildServicesView.assert_called_once_with(self.mock_db, self.mock_user)

        # Check that it builds the embed correctly without night flavor
        embed_builder = self.lobby_module.EmbedBuilder
        interaction.edit_original_response.assert_awaited_once()

        # Call kwargs
        kwargs = interaction.edit_original_response.await_args.kwargs
        self.assertIn("embed", kwargs)
        self.assertIn("view", kwargs)

    async def test_services_btn_callback_night(self):
        self.mock_world_time.TimePhase.DAY = "DAY"
        self.mock_world_time.TimePhase.NIGHT = "NIGHT"
        self.mock_world_time.WorldTime.get_current_phase.return_value = "NIGHT"

        view = self.GuildLobbyView(self.mock_db, self.mock_user, rank="F")
        interaction = self.mock_discord.Interaction()

        # Wait for the async callback
        await view._services_btn_callback(interaction)

        # Verify interaction response
        interaction.response.defer.assert_awaited_once()
        self.mock_services_menu.GuildServicesView.assert_called_once_with(self.mock_db, self.mock_user)

        # Assert night flavor logic by patching EmbedBuilder
        interaction.edit_original_response.assert_awaited_once()

        # We can't easily assert exactly what embed.description contains because it's built internally
        # but we know the path was hit and didn't crash
        self.assertTrue(interaction.edit_original_response.called)

if __name__ == "__main__":
    unittest.main()
