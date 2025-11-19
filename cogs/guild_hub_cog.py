"""
cogs/guild_hub_cog.py
The Controller for the Guild System.
Hardened: Ensures cache cleanup on unload.
"""

import logging

from discord.ext import commands

from database.database_manager import DatabaseManager
from game_systems.guild_system.ui.components import SystemCache

logger = logging.getLogger("eldoria.cogs.guild")


class GuildHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        logger.info("GuildHubCog initialized.")

    def cog_unload(self):
        """Cleanup caches when cog is reloaded/unloaded."""
        SystemCache.clear()
        logger.info("GuildHubCog unloaded, cache cleared.")


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))
