import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDeveloperCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        mock_discord = MagicMock()
        mock_discord.app_commands = MagicMock()

        # Mock app_commands.command decorator
        def command_decorator(*args, **kwargs):
            def decorator(func):
                func.error = MagicMock()  # For @dev_panel.error
                return func

            return decorator

        mock_discord.app_commands.command = MagicMock(side_effect=command_decorator)

        # Mock discord.ui
        mock_discord.ui = MagicMock()

        # Mock button decorator
        def button_decorator(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        mock_discord.ui.button = MagicMock(side_effect=button_decorator)

        # Mock View
        class MockView:
            def __init__(self, timeout=None):
                pass

        mock_discord.ui.View = MockView

        # Mock Embed
        class MockEmbed:
            def __init__(self, **kwargs):
                self.title = kwargs.get("title")
                self.fields = []

            def add_field(self, **kwargs):
                self.fields.append(kwargs)

        mock_discord.Embed = MockEmbed

        # Mock ButtonStyle
        mock_discord.ButtonStyle = MagicMock()

        sys.modules["discord"] = mock_discord
        sys.modules["discord.app_commands"] = mock_discord.app_commands

        mock_ext = MagicMock()

        class DummyCog:
            pass

        mock_ext.commands.Cog = DummyCog
        sys.modules["discord.ext"] = mock_ext
        sys.modules["discord.ui"] = mock_discord.ui

        # Mock DatabaseManager
        mock_pymongo = MagicMock()
        sys.modules["pymongo"] = mock_pymongo
        sys.modules["pymongo.errors"] = MagicMock()

        # Import
        import cogs.developer_cog

        importlib = __import__("importlib")
        importlib.reload(cogs.developer_cog)

        self.DeveloperCog = cogs.developer_cog.DeveloperCog
        self.DevPanelView = cogs.developer_cog.DevPanelView

        self.bot = AsyncMock()
        # Ensure is_owner returns a boolean, not a mock that evaluates to True
        self.bot.is_owner.return_value = False

        # Mock DB
        self.mock_db_cls = MagicMock()
        with patch("cogs.developer_cog.DatabaseManager", return_value=self.mock_db_cls) as mock_db_cls:
            self.mock_db = mock_db_cls.return_value
            self.cog = self.DeveloperCog(self.bot)

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_dev_panel_not_owner(self):
        interaction = AsyncMock()
        self.bot.is_owner.return_value = False

        await self.cog.dev_panel(interaction)

        interaction.response.send_message.assert_called_once()
        self.assertIn("not the bot owner", interaction.response.send_message.call_args[0][0])

    async def test_dev_panel_no_character(self):
        interaction = AsyncMock()
        self.bot.is_owner.return_value = True

        # Mock db calls (asyncio.to_thread calls them)
        # We need to ensure that the synchronous DB calls return what we expect.
        self.cog.db.get_player.return_value = None

        await self.cog.dev_panel(interaction)

        interaction.followup.send.assert_called_once()
        self.assertIn("No character found", interaction.followup.send.call_args[0][0])

    async def test_dev_panel_success(self):
        interaction = AsyncMock()
        self.bot.is_owner.return_value = True

        self.cog.db.get_player.return_value = {"experience": 100}
        self.cog.db.get_active_boosts.return_value = []

        await self.cog.dev_panel(interaction)

        interaction.followup.send.assert_called_once()
        kwargs = interaction.followup.send.call_args.kwargs
        self.assertIsInstance(kwargs["view"], self.DevPanelView)

    async def test_view_interaction_check_success(self):
        user = MagicMock()
        user.id = 123
        view = self.DevPanelView(self.mock_db, user, {}, [])

        interaction = AsyncMock()
        interaction.user.id = 123

        result = await view.interaction_check(interaction)
        self.assertTrue(result)

    async def test_view_interaction_check_fail(self):
        user = MagicMock()
        user.id = 123
        view = self.DevPanelView(self.mock_db, user, {}, [])

        interaction = AsyncMock()
        interaction.user.id = 456

        result = await view.interaction_check(interaction)
        self.assertFalse(result)
        interaction.response.send_message.assert_called_once()

    async def test_view_buttons(self):
        # Test one button to verify logic (e.g. exp_btn)
        user = MagicMock()
        view = self.DevPanelView(self.mock_db, user, {}, [])

        interaction = AsyncMock()
        button = MagicMock()

        # Setup DB mocks for refresh
        view.db.get_player.return_value = {"experience": 100}
        view.db.get_active_boosts.return_value = []

        # Call exp_btn
        await view.exp_btn(interaction, button)

        view.db.admin_grant.assert_called_once()
        interaction.edit_original_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
