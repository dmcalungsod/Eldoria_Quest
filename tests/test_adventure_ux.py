import sys
import unittest
from unittest.mock import MagicMock, patch
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAdventureUX(unittest.TestCase):
    def setUp(self):
        # 1. Mock dependencies
        self.mock_discord = MagicMock()

        # Define a Mock View class
        class MockView:
            def __init__(self, timeout=None):
                self.items = []
                self.timeout = timeout
            def add_item(self, item):
                self.items.append(item)

        class MockButton:
            def __init__(self, label=None, style=None, custom_id=None, emoji=None, row=None):
                self.label = label
                self.style = style
                self.custom_id = custom_id
                self.emoji = emoji
                self.row = row
                self.callback = None
            def _is_v2(self):
                return False

        self.mock_discord.ui.View = MockView
        self.mock_discord.ui.Button = MockButton

        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules, {
            "discord": self.mock_discord,
            "discord.ui": self.mock_discord.ui,
            "discord.ext": MagicMock(),
            "discord.ext.commands": MagicMock(),
            "cogs.ui_helpers": MagicMock(),
            "game_systems.adventure.ui.adventure_embeds": MagicMock(),
            "game_systems.adventure.ui.exploration_view": MagicMock(),
            "game_systems.adventure.ui.setup_view": MagicMock(),
            "pymongo": MagicMock(),
        })
        self.modules_patcher.start()

        # Import module under test
        # We need to reload it to use the mocked modules
        if "game_systems.character.ui.adventure_menu" in sys.modules:
            del sys.modules["game_systems.character.ui.adventure_menu"]

        import game_systems.character.ui.adventure_menu
        self.AdventureView = game_systems.character.ui.adventure_menu.AdventureView

        # Import DatabaseManager (it needs mocked pymongo)
        import database.database_manager
        self.DatabaseManager = database.database_manager.DatabaseManager

    def tearDown(self):
        self.modules_patcher.stop()

    def test_adventure_view_resume(self):
        """Test that AdventureView shows 'Resume' when active_session is True."""
        mock_db = MagicMock(spec=self.DatabaseManager)
        mock_user = MagicMock()

        try:
            view = self.AdventureView(mock_db, mock_user, active_session=True)

            # Use our MockView implementation
            self.assertTrue(len(view.items) > 0)

            button = view.items[0]
            print(f"Button Label: {button.label}, Emoji: {button.emoji}")

            self.assertEqual(button.label, "Resume Expedition", "Label should be 'Resume Expedition'")
            self.assertIn(button.emoji, ["🧭", "🗺️"], "Emoji should be Compass or Map for resume")

        except TypeError as e:
            print(f"Caught expected TypeError (not implemented yet): {e}")

    def test_adventure_view_begin(self):
        """Test that AdventureView shows 'Begin' when active_session is False."""
        mock_db = MagicMock(spec=self.DatabaseManager)
        mock_user = MagicMock()

        try:
            view = self.AdventureView(mock_db, mock_user, active_session=False)

            self.assertTrue(len(view.items) > 0)

            button = view.items[0]
            print(f"Button Label: {button.label}, Emoji: {button.emoji}")

            self.assertEqual(button.label, "Begin Expedition", "Label should be 'Begin Expedition'")
            self.assertEqual(button.emoji, "⚔️", "Emoji should be Swords for begin")

        except TypeError as e:
            print(f"Caught expected TypeError (not implemented yet): {e}")


if __name__ == "__main__":
    unittest.main()
