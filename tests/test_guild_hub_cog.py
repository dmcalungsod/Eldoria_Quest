import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGuildHubCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        # Mock discord and ext
        mock_discord = MagicMock()
        mock_ext = MagicMock()

        class DummyCog:
            pass

        mock_ext.commands.Cog = DummyCog
        sys.modules["discord"] = mock_discord
        sys.modules["discord.ext"] = mock_ext

        # Mock DatabaseManager
        mock_db_manager = MagicMock()
        sys.modules["database.database_manager"] = mock_db_manager

        # Mock SystemCache
        self.mock_system_cache = MagicMock()
        sys.modules["game_systems.guild_system.ui.components"] = self.mock_system_cache

        # Import cog
        from cogs.guild_hub_cog import GuildHubCog
        self.GuildHubCog = GuildHubCog

    def tearDown(self):
        self.modules_patcher.stop()

    def test_initialization(self):
        """Test GuildHubCog initializes correctly."""
        bot_mock = MagicMock()
        cog = self.GuildHubCog(bot_mock)
        self.assertEqual(cog.bot, bot_mock)

    def test_cog_unload(self):
        """Test cog_unload clears the SystemCache."""
        bot_mock = MagicMock()
        cog = self.GuildHubCog(bot_mock)
        cog.cog_unload()
        self.mock_system_cache.SystemCache.clear.assert_called_once()

    async def test_setup(self):
        """Test that setup adds the cog."""
        from cogs.guild_hub_cog import setup
        bot_mock = AsyncMock()
        await setup(bot_mock)
        bot_mock.add_cog.assert_called_once()
        self.assertIsInstance(bot_mock.add_cog.call_args[0][0], self.GuildHubCog)

if __name__ == '__main__':
    unittest.main()
