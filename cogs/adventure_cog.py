"""
cogs/adventure_cog.py

Discord Cog for the Adventure System.
Initializes the AdventureManager.
No slash commands are exposed; access is handled via UI buttons.
"""

from discord.ext import commands

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager


class AdventureCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)

    # The /adventure command has been removed to enforce the ONE UI Policy.
    # Players must start expeditions via the Character Profile buttons.


async def setup(bot: commands.Bot):
    await bot.add_cog(AdventureCommands(bot))
