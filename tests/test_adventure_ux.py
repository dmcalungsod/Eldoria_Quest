import importlib
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper Mocks
class MockView:
    def __init__(self, timeout=None):
        self.items = []
        self.children = [] # Alias for items as some code uses children
        self.timeout = timeout

    def add_item(self, item):
        self.items.append(item)
        self.children.append(item)


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


class TestAdventureUX(unittest.IsolatedAsyncioTestCase):
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
        mock_discord.ButtonStyle.success = "success"
        mock_discord.ButtonStyle.grey = "grey"

        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_ui
        sys.modules["discord.ext"] = MagicMock()
        sys.modules["discord.ext.commands"] = MagicMock()

        # Mock dependencies
        sys.modules["cogs"] = MagicMock()
        sys.modules["cogs.utils.ui_helpers"] = MagicMock()

        # Mock specific modules used in adventure_menu.py
        if "game_systems.adventure.ui.adventure_embeds" not in sys.modules:
            sys.modules["game_systems.adventure.ui.adventure_embeds"] = MagicMock()
        if "game_systems.adventure.ui.setup_view" not in sys.modules:
            sys.modules["game_systems.adventure.ui.setup_view"] = MagicMock()
        if "game_systems.adventure.ui.status_view" not in sys.modules:
            sys.modules["game_systems.adventure.ui.status_view"] = MagicMock()

        # Import module under test
        import game_systems.character.ui.adventure_menu

        importlib.reload(game_systems.character.ui.adventure_menu)

        self.AdventureView = game_systems.character.ui.adventure_menu.AdventureView
        self.AdventureEmbeds = game_systems.character.ui.adventure_menu.AdventureEmbeds
        self.AdventureStatusView = game_systems.character.ui.adventure_menu.AdventureStatusView
        self.AdventureSetupView = game_systems.character.ui.adventure_menu.AdventureSetupView

        import database.database_manager
        importlib.reload(database.database_manager)
        self.DatabaseManager = database.database_manager.DatabaseManager

    def tearDown(self):
        self.modules_patcher.stop()

    def test_adventure_view_resume(self):
        """Test that AdventureView shows 'Resume' when active_session is True."""
        mock_db = MagicMock(spec=self.DatabaseManager)
        mock_user = MagicMock()

        view = self.AdventureView(mock_db, mock_user, active_session=True)
        button = view.items[0]
        self.assertEqual(button.label, "Resume Expedition")
        self.assertIn(button.emoji, ["🧭", "🗺️"])

    def test_adventure_view_begin(self):
        """Test that AdventureView shows 'Begin' when active_session is False."""
        mock_db = MagicMock(spec=self.DatabaseManager)
        mock_user = MagicMock()

        view = self.AdventureView(mock_db, mock_user, active_session=False)
        button = view.items[0]
        self.assertEqual(button.label, "Begin Expedition")
        self.assertEqual(button.emoji, "⚔️")

    async def test_start_adventure_callback_new(self):
        """Test start adventure callback for new adventure (SetupView)."""
        mock_db = MagicMock()
        mock_user = MagicMock()
        view = self.AdventureView(mock_db, mock_user, active_session=False)

        interaction = AsyncMock()
        interaction.user.id = mock_user.id

        # Mock Cog and Manager
        mock_cog = MagicMock()
        mock_manager = MagicMock()
        mock_cog.manager = mock_manager
        # interaction.client.get_cog is likely being awaited incorrectly in the test setup or source
        # but in source: adventure_cog = interaction.client.get_cog("AdventureCommands") is NOT awaited.
        # However, interaction is an AsyncMock, so methods are async by default.
        # We need to make get_cog synchronous for the mock.
        interaction.client.get_cog = MagicMock(return_value=mock_cog)

        # Mock active session -> None (New adventure)
        mock_manager.get_active_session = MagicMock(return_value=None)

        # Mock data fetching
        mock_db.get_guild_member_data = MagicMock(return_value={"rank": "F"})
        mock_db.get_player = MagicMock(return_value={"level": 1})
        mock_db.get_inventory_items = MagicMock(return_value=[])
        mock_db.calculate_inventory_limit = MagicMock(return_value=20)
        mock_db.get_inventory_slot_count = MagicMock(return_value=5)

        # Mock SetupView
        self.AdventureSetupView.return_value.back_btn = MagicMock()

        await view.start_adventure_callback(interaction)

        interaction.edit_original_response.assert_called()
        # Verify SetupView was used
        self.AdventureSetupView.assert_called()

    async def test_start_adventure_callback_resume_status(self):
        """Test start adventure callback resuming active session (StatusView)."""
        mock_db = MagicMock()
        mock_user = MagicMock()
        view = self.AdventureView(mock_db, mock_user, active_session=True)

        interaction = AsyncMock()
        interaction.user.id = mock_user.id

        # Mock Cog and Manager
        mock_cog = MagicMock()
        mock_manager = MagicMock()
        mock_cog.manager = mock_manager
        interaction.client.get_cog = MagicMock(return_value=mock_cog)

        # Mock active session
        session = {"status": "in_progress", "location_id": "forest"}
        mock_manager.get_active_session = MagicMock(return_value=session)

        # Mock Embeds
        self.AdventureEmbeds.build_adventure_status_embed.return_value = MagicMock()

        await view.start_adventure_callback(interaction)

        interaction.edit_original_response.assert_called()
        # Verify StatusView was used
        self.AdventureStatusView.assert_called()

    async def test_start_adventure_callback_resume_completed(self):
        """Test start adventure callback resuming completed session (Summary)."""
        mock_db = MagicMock()
        mock_user = MagicMock()
        view = self.AdventureView(mock_db, mock_user, active_session=True)

        interaction = AsyncMock()
        interaction.user.id = mock_user.id

        mock_cog = MagicMock()
        mock_manager = MagicMock()
        mock_cog.manager = mock_manager
        interaction.client.get_cog = MagicMock(return_value=mock_cog)

        # Mock active session -> Completed
        session = {"status": "completed", "location_id": "forest"}
        mock_manager.get_active_session = MagicMock(return_value=session)

        # Mock summary
        mock_manager.end_adventure = MagicMock(return_value={"xp": 100})
        self.AdventureEmbeds.build_summary_embed.return_value = MagicMock()

        await view.start_adventure_callback(interaction)

        interaction.edit_original_response.assert_called()
        # Should create a basic view with back button, not StatusView
        args, kwargs = interaction.edit_original_response.call_args
        # kwargs['view'] is a basic View
        # AdventureStatusView is a MagicMock object here because we mocked the module import
        # So we can't use isinstance against it directly if it's an instance of MagicMock.
        # But wait, self.AdventureStatusView IS the class mock.
        # However, assertNotIsInstance expects a type.
        # Let's check if it was instantiated.
        self.AdventureStatusView.assert_not_called()

if __name__ == "__main__":
    unittest.main()
