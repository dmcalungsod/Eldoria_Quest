import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGuildLobbyView(unittest.TestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Setup Mocks
        self.mock_discord = MagicMock()

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

    def test_advisor_button_logic(self):
        button_mock = self.mock_discord.ui.Button

        # Test Rank F
        button_mock.reset_mock()
        self.GuildLobbyView(self.mock_db, self.mock_user, rank="F")

        calls = button_mock.call_args_list
        has_advisor = any(c.kwargs.get("label") == "Advisor" for c in calls)
        self.assertTrue(has_advisor, "Advisor button should be created for Rank F")

        # Test Rank E
        button_mock.reset_mock()
        self.GuildLobbyView(self.mock_db, self.mock_user, rank="E")
        calls = button_mock.call_args_list
        has_advisor = any(c.kwargs.get("label") == "Advisor" for c in calls)
        self.assertTrue(has_advisor, "Advisor button should be created for Rank E")

        # Test Rank D (Too high)
        button_mock.reset_mock()
        self.GuildLobbyView(self.mock_db, self.mock_user, rank="D")
        calls = button_mock.call_args_list
        has_advisor = any(c.kwargs.get("label") == "Advisor" for c in calls)
        self.assertFalse(has_advisor, "Advisor button should NOT be created for Rank D")


if __name__ == "__main__":
    unittest.main()
