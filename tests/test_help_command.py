import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHelpCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord package structure
        mock_discord = MagicMock()
        mock_discord.ui = MagicMock()
        mock_discord.app_commands = MagicMock()

        # Mock app_commands.command decorator
        def command_decorator(*args, **kwargs):
            def wrapper(func):
                # Return a mock that acts like a Command object
                # We attach the original function to it so we can run it
                cmd = MagicMock()
                cmd.callback = func
                return cmd

            return wrapper

        mock_discord.app_commands.command = command_decorator

        # Mock discord.ext package
        mock_discord_ext = MagicMock()
        mock_discord_ext.commands = MagicMock()

        # Define Cog as a real class so GeneralCog doesn't inherit MagicMock behavior
        class MockCog:
            pass

        mock_discord_ext.commands.Cog = MockCog

        mock_discord.ext = mock_discord_ext

        # Ensure View and Select are mockable classes
        class MockView:
            def __init__(self, timeout=None):
                self.children = []

            def add_item(self, item):
                self.children.append(item)

        class MockSelect:
            def __init__(
                self, placeholder=None, min_values=1, max_values=1, options=None
            ):
                self.options = options or []
                self.values = []
                self.view = None

            async def callback(self, interaction):
                pass

        mock_discord.ui.View = MockView
        mock_discord.ui.Select = MockSelect
        mock_discord.SelectOption = MagicMock

        # Assign to sys.modules
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ui"] = mock_discord.ui
        sys.modules["discord.app_commands"] = mock_discord.app_commands
        sys.modules["discord.ext"] = mock_discord_ext
        sys.modules["discord.ext.commands"] = mock_discord.ext.commands

        # Import the module to test
        if "cogs.general_cog" in sys.modules:
            del sys.modules["cogs.general_cog"]

        import cogs.general_cog

        self.cogs_general = cogs.general_cog

        self.bot = MagicMock()
        self.cog = self.cogs_general.GeneralCog(self.bot)

        # We need to instantiate View/Select after import
        self.view = self.cogs_general.HelpView()
        self.select = self.cogs_general.HelpSelect()

    def tearDown(self):
        self.modules_patcher.stop()

    def test_help_view_init(self):
        """Test that HelpView initializes with the select menu."""
        self.assertEqual(len(self.view.children), 1)
        self.assertIsInstance(self.view.children[0], self.cogs_general.HelpSelect)

    async def test_help_select_callback(self):
        """Test the callback of HelpSelect."""
        interaction = AsyncMock()
        self.select.view = AsyncMock()
        self.select.values = ["overview"]

        await self.select.callback(interaction)

        self.select.view.update_embed.assert_called_once_with(interaction, "overview")

    async def test_view_update_embed(self):
        """Test update_embed method in HelpView."""
        interaction = AsyncMock()

        with patch.object(
            self.view, "_get_embed", return_value="MockEmbed"
        ) as mock_get_embed:
            await self.view.update_embed(interaction, "combat")

            mock_get_embed.assert_called_once_with("combat")
            interaction.response.edit_message.assert_called_once_with(
                embed="MockEmbed", view=self.view
            )

    def test_get_embed_content(self):
        """Test that _get_embed returns correct embeds for different categories."""
        with patch("cogs.general_cog.discord.Embed") as MockEmbed:
            MockEmbed.return_value = MagicMock()

            self.view._get_embed("overview")
            MockEmbed.assert_called_with(
                title="📜 The Adventurer's Guild Handbook",
                description=unittest.mock.ANY,
                color=sys.modules["discord"].Color.dark_gold(),
            )

    async def test_help_command(self):
        """Test the actual help command execution."""
        interaction = AsyncMock()

        # Patch HelpView constructor to return a mock or our view
        with patch("cogs.general_cog.HelpView") as MockViewCls:
            mock_view_instance = MockViewCls.return_value
            mock_view_instance._get_embed.return_value = "InitialEmbed"

            # The help_command attribute is the decorated command (MagicMock from our decorator)
            # Its callback is the original async method
            await self.cog.help_command.callback(self.cog, interaction)

            interaction.response.send_message.assert_called_once()
            call_args = interaction.response.send_message.call_args
            self.assertEqual(call_args.kwargs["embed"], "InitialEmbed")
            self.assertEqual(call_args.kwargs["view"], mock_view_instance)
            self.assertTrue(call_args.kwargs["ephemeral"])


if __name__ == "__main__":
    unittest.main()
