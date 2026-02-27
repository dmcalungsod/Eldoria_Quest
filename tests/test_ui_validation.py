import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUIValidation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules to mock discord and pymongo
        self.modules_patcher = patch.dict(
            sys.modules,
            {
                "discord": MagicMock(),
                "discord.ui": MagicMock(),
                "discord.ext": MagicMock(),
                "discord.ext.commands": MagicMock(),
                "pymongo": MagicMock(),
                "pymongo.errors": MagicMock(),
                "pymongo.MongoClient": MagicMock(),
            },
        )
        self.modules_patcher.start()

        # Import/Reload modules to ensure they use the mocks
        # We need to ensure database.database_manager is loaded/reloaded with mocked pymongo
        import database.database_manager

        importlib.reload(database.database_manager)

        # Now that cogs/__init__.py and cogs/utils/__init__.py exist, we can import normally
        import cogs.utils.ui_helpers
        importlib.reload(cogs.utils.ui_helpers)
        self.get_player_or_error = cogs.utils.ui_helpers.get_player_or_error
        self.DatabaseManager = database.database_manager.DatabaseManager

        self.mock_db = MagicMock(spec=self.DatabaseManager)
        self.interaction = MagicMock()
        self.interaction.user.id = 12345
        self.interaction.response = MagicMock()
        self.interaction.followup = MagicMock()

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_player_found(self):
        """Test validation when player exists."""
        # Mock get_player to return a dict
        self.mock_db.get_player.return_value = {"name": "TestPlayer"}

        result = await self.get_player_or_error(self.interaction, self.mock_db)

        self.assertEqual(result, {"name": "TestPlayer"})
        self.mock_db.get_player.assert_called_with(12345)
        # Verify that error messages were NOT sent
        self.interaction.response.send_message.assert_not_called()
        self.interaction.followup.send.assert_not_called()

    async def test_player_not_found_not_deferred(self):
        """Test validation when player missing and interaction NOT deferred."""
        self.mock_db.get_player.return_value = None
        self.interaction.response.is_done.return_value = False
        self.interaction.response.send_message = AsyncMock()

        result = await self.get_player_or_error(self.interaction, self.mock_db)

        self.assertIsNone(result)
        self.interaction.response.send_message.assert_called_with("Character record not found.", ephemeral=True)
        self.interaction.followup.send.assert_not_called()

    async def test_player_not_found_deferred(self):
        """Test validation when player missing and interaction deferred."""
        self.mock_db.get_player.return_value = None
        self.interaction.response.is_done.return_value = True
        self.interaction.followup.send = AsyncMock()

        result = await self.get_player_or_error(self.interaction, self.mock_db)

        self.assertIsNone(result)
        self.interaction.response.send_message.assert_not_called()
        self.interaction.followup.send.assert_called_with("Character record not found.", ephemeral=True)

    async def test_custom_message(self):
        """Test validation with custom error message."""
        self.mock_db.get_player.return_value = None
        self.interaction.response.is_done.return_value = False
        self.interaction.response.send_message = AsyncMock()

        result = await self.get_player_or_error(self.interaction, self.mock_db, content="Custom Error")

        self.assertIsNone(result)
        self.interaction.response.send_message.assert_called_with("Custom Error", ephemeral=True)


if __name__ == "__main__":
    unittest.main()
