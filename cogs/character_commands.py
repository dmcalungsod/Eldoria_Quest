"""
Character Commands Cog
This cog is now a placeholder.
All functionality has been moved to the button callbacks in guild_hub_cog.py
to create a button-only UI flow.
"""

import discord
from discord import app_commands
from discord.ext import commands
from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E


class CharacterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.inventory = InventoryManager(self.db)

    # --- NO COMMANDS ---
    # The /status and /inventory commands have been removed.
    # Their logic is now handled by buttons in GuildHubCog:
    # - "View Profile" button -> view_profile_callback
    # - "Inventory" button -> view_inventory_callback


async def setup(bot):
    await bot.add_cog(CharacterCommands(bot))
