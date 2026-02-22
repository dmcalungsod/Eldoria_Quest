import sys
import os
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create Mock classes for Discord UI
class MockSelect:
    def __init__(self, *args, **kwargs):
        self.values = []
        self.view = None

    async def callback(self, interaction):
        pass

class MockView:
    def __init__(self, *args, **kwargs):
        self.children = []

    def add_item(self, item):
        self.children.append(item)

    def clear_items(self):
        self.children = []

# Mock modules
mock_discord = MagicMock()
mock_discord.ui.Select = MockSelect
mock_discord.ui.View = MockView
sys.modules["discord"] = mock_discord
sys.modules["discord.ui"] = mock_discord.ui
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

import discord  # noqa: E402
from cogs.chronicle_cog import TitleSelect, ChroniclesView  # noqa: E402
from database.database_manager import DatabaseManager  # noqa: E402

class TestChronicleCog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_db = MagicMock()
        self.db_patcher = patch("cogs.chronicle_cog.DatabaseManager", return_value=self.mock_db)
        self.MockDB = self.db_patcher.start()

        # Mock Interaction
        self.interaction = MagicMock()
        self.interaction.user.id = 12345
        self.interaction.response = MagicMock()
        self.interaction.response.defer = AsyncMock()
        self.interaction.edit_original_response = AsyncMock()
        self.interaction.followup.send = AsyncMock()

        # Mock Message and Embed
        self.embed = MagicMock()
        field1 = MagicMock()
        field1.name = "Active Title"
        field1.value = "*None*"

        field2 = MagicMock()
        field2.name = "Other Field"
        field2.value = "Value"

        self.embed.fields = [field1, field2]
        self.interaction.message.embeds = [self.embed]

        # Mock View
        self.view = MagicMock()
        self.view.titles = ["Title A", "Title B"]
        self.view.active_title = None

    async def asyncTearDown(self):
        self.db_patcher.stop()

    async def test_callback_updates_embed_and_view(self):
        # Setup Select
        select = TitleSelect(titles=["Title A", "Title B"], current_active=None)
        select.view = self.view
        select.values = ["Title A"]

        # Mock DB success
        self.mock_db.set_active_title = MagicMock(return_value=True)

        # Run callback
        await select.callback(self.interaction)

        # Verify DB called
        self.mock_db.set_active_title.assert_called_with(12345, "Title A")

        # Verify Embed Updated
        # Check that set_field_at was called on index 0 (Active Title)
        self.embed.set_field_at.assert_called()
        args = self.embed.set_field_at.call_args
        self.assertEqual(args[0][0], 0) # Index 0
        self.assertEqual(args[1]['name'], "Active Title")
        self.assertEqual(args[1]['value'], "**Title A**")

        # Verify View Updated
        self.assertEqual(self.view.active_title, "Title A")
        self.view.clear_items.assert_called()
        self.view.add_item.assert_called()

        # Verify ONE UI: edit_original_response called
        self.interaction.edit_original_response.assert_called()
        self.interaction.followup.send.assert_not_called()

    async def test_callback_failure_sends_ephemeral(self):
        # Setup Select
        select = TitleSelect(titles=["Title A"], current_active=None)
        select.view = self.view
        select.values = ["Title A"]

        # Mock DB failure
        self.mock_db.set_active_title = MagicMock(return_value=False)

        # Run callback
        await select.callback(self.interaction)

        # Verify edit NOT called
        self.interaction.edit_original_response.assert_not_called()

        # Verify error message sent
        self.interaction.followup.send.assert_called_with("Failed to set title.", ephemeral=True)

if __name__ == "__main__":
    unittest.main()
