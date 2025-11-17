"""
cogs/adventure_cog.py

Discord Cog for the Adventure System.
Initializes the AdventureManager and registers the /adventure command.
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# Import our modular Views
from game_systems.adventure.ui.setup_view import AdventureSetupView
from game_systems.adventure.ui.exploration_view import ExplorationView
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds

class AdventureCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)

    # Note: This command is usually accessed via the "Begin Expedition" button 
    # in the Character Profile, but we keep a slash command for direct access/debug.
    @app_commands.command(name="adventure", description="Start or resume an expedition.")
    async def adventure(self, interaction: discord.Interaction):
        
        # 1. Check if player exists
        if not self.db.player_exists(interaction.user.id):
            await interaction.response.send_message("You must create a character first! Use `/start`.", ephemeral=True)
            return

        # 2. Check for existing active session
        active_session = await asyncio.to_thread(self.manager.get_active_session, interaction.user.id)

        if active_session:
            # --- RESUME EXISTING SESSION ---
            await interaction.response.defer()
            loc_id = active_session["location_id"]
            
            try:
                log = json.loads(active_session["logs"])
            except:
                log = []

            # --- FIX: Parse active monster ---
            active_monster = None
            if active_session["active_monster_json"]:
                try:
                    active_monster = json.loads(active_session["active_monster_json"])
                except:
                    pass
            # --- END FIX ---
            
            # Fetch current state
            stats_json = await asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
            player_stats = PlayerStats.from_dict(stats_json)
            vitals = await asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)

            # Rebuild Embed
            embed = AdventureEmbeds.build_exploration_embed(
                loc_id, log, player_stats, vitals, active_session
            )
            
            # Launch View
            view = ExplorationView(
                self.db, self.manager, loc_id, log, interaction.user, player_stats,
                active_monster=active_monster # <-- Pass monster
            )
            await interaction.followup.send(embed=embed, view=view)
            return

        # --- START NEW SESSION ---
        await interaction.response.defer()
        guild_member = await asyncio.to_thread(self.db.get_guild_member_data, interaction.user.id)
        rank = guild_member['rank'] if guild_member else 'F'

        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description="*The city gates stand heavy. Beyond lies the fractured world.*\n\nSelect a destination to begin.",
            color=discord.Color.dark_green()
        )
        
        view = AdventureSetupView(self.db, self.manager, interaction.user, rank)
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdventureCommands(bot))