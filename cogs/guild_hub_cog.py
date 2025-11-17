"""
cogs/guild_hub_cog.py
The Controller for the Guild System.
"""
import discord
from discord.ext import commands
from database.database_manager import DatabaseManager
from game_systems.guild_system.ui.components import SystemCache

# Note: We only need to import this for potential type checking or event listeners.
# The actual Views are now self-contained in game_systems/guild_system/ui/.

class GuildHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    def cog_unload(self):
        SystemCache.clear()

async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))