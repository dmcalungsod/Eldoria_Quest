"""
cogs/character_cog.py
Controller for the Character UI system.
No slash commands here; pure UI logic.
"""

from discord.ext import commands

from database.database_manager import DatabaseManager


class CharacterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCog(bot))
