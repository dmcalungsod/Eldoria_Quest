import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGeneralCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord
        mock_discord = MagicMock()
        mock_discord.app_commands = MagicMock()

        # Mock app_commands.command decorator
        def command_decorator(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

        mock_discord.app_commands.command = command_decorator

        # Mock Embed
        class MockEmbed:
            def __init__(self, **kwargs):
                self.title = kwargs.get("title")
                self.description = kwargs.get("description")
                self.fields = []
                self.footer = None

            def add_field(self, **kwargs):
                self.fields.append(kwargs)

            def set_footer(self, **kwargs):
                self.footer = kwargs

        mock_discord.Embed = MockEmbed

        # Mock Color
        mock_discord.Color = MagicMock()

        sys.modules["discord"] = mock_discord
        sys.modules["discord.app_commands"] = mock_discord.app_commands

        mock_ext = MagicMock()
        class DummyCog:
            pass
        mock_ext.commands.Cog = DummyCog
        sys.modules["discord.ext"] = mock_ext

        # Import
        from cogs.general_cog import GeneralCog

        self.bot = MagicMock()
        self.cog = GeneralCog(self.bot)
        self.interaction = MagicMock()
        self.interaction.user = "TestUser"
        self.interaction.response = AsyncMock()
        self.discord = mock_discord

    def tearDown(self):
        self.modules_patcher.stop()

    async def test_ping_success(self):
        """Test ping command calculates latency and sends embed successfully."""
        self.bot.latency = 0.150  # 150ms

        await self.cog.ping(self.interaction)

        self.interaction.response.send_message.assert_called_once()
        call_args = self.interaction.response.send_message.call_args[1]

        self.assertIn("embed", call_args)
        embed = call_args["embed"]
        self.assertEqual(embed.title, "🏓 Pong!")
        self.assertTrue("150ms" in embed.description)
        self.assertTrue(call_args.get("ephemeral") is True)

    @patch("cogs.general_cog.logger.error")
    async def test_ping_exception(self, mock_logger_error):
        """Test ping command handles exceptions gracefully."""
        self.bot.latency = 0.150

        # When exception happens on the first call, we want the second call to succeed
        self.interaction.response.send_message.side_effect = [Exception("Send Error"), None]

        await self.cog.ping(self.interaction)

        mock_logger_error.assert_called_once()
        self.assertTrue(mock_logger_error.call_args[0][0].startswith("Ping command failed:"))

    @patch("cogs.general_cog.logger.error")
    async def test_ping_exception_fallback(self, mock_logger_error):
        """Test ping command exception logic when Embed creation fails."""
        # Cause an exception before send_message
        self.bot.latency = "not_a_number" # Will cause TypeError when calculating round()

        await self.cog.ping(self.interaction)

        mock_logger_error.assert_called_once()
        self.assertTrue(mock_logger_error.call_args[0][0].startswith("Ping command failed:"))

        self.interaction.response.send_message.assert_called_once_with(
            "Error calculating latency.", ephemeral=True
        )

    async def test_help_command_success(self):
        """Test help_command sends the guild handbook embed."""
        await self.cog.help_command(self.interaction)

        self.interaction.response.send_message.assert_called_once()
        call_args = self.interaction.response.send_message.call_args[1]

        self.assertIn("embed", call_args)
        embed = call_args["embed"]
        self.assertEqual(embed.title, "Guild Handbook")
        self.assertTrue("The pages are worn" in embed.description)
        self.assertTrue(call_args.get("ephemeral") is True)

        # Check that add_field was called 4 times
        self.assertEqual(len(embed.fields), 4)
        self.assertEqual(embed.footer["text"], "May your light hold against the darkness.")

    @patch("cogs.general_cog.logger.error")
    async def test_help_command_exception(self, mock_logger_error):
        """Test help_command handles exceptions gracefully."""
        # Cause exception
        self.interaction.response.send_message.side_effect = [Exception("Embed Error"), None]

        await self.cog.help_command(self.interaction)

        mock_logger_error.assert_called_once()
        self.assertTrue(mock_logger_error.call_args[0][0].startswith("Help command failed:"))

    async def test_setup(self):
        """Test that setup adds the cog."""
        from cogs.general_cog import setup
        bot_mock = AsyncMock()
        await setup(bot_mock)
        bot_mock.add_cog.assert_called_once()

if __name__ == '__main__':
    unittest.main()
