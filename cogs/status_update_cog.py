"""
status_update_cog.py

Handles the "Status Update" UI where players
spend Vestige to increase their base stats,
in the style of Danmachi.
"""

import discord
from discord.ui import View, Button, Select
from discord.ext import commands
import json
import sqlite3
import asyncio # <-- IMPORT ASYNCIO
from typing import Tuple

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback

# --- Stat Costs ---
# Define the base cost to increase a stat by 1
# We can make this scale later if we want!
STAT_COSTS = {
    "STR": 10,
    "END": 10,
    "DEX": 10,
    "AGI": 12,
    "MAG": 12,
    "LCK": 20,
}


class StatusUpdateView(View):
    """
    The main UI for the Status Update.
    Displays spendable Vestige and buttons to increase stats.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: sqlite3.Row,
        player_stats: PlayerStats,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.player_data = player_data
        self.player_stats = player_stats
        self.vestige_pool = player_data["vestige_pool"]

        # Add the stat buttons
        self.add_stat_buttons()

        # Add the back button
        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_profile",
            row=2,  # Place it on the third row
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your status.", ephemeral=True
            )
            return False
        return True

    def add_stat_buttons(self):
        """Creates a button for each stat."""

        # Row 0: STR, END, DEX
        str_button = Button(
            label=f"+1 STR ({STAT_COSTS['STR']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_STR",
            disabled=self.vestige_pool < STAT_COSTS["STR"],
            row=0,
        )
        str_button.callback = self.stat_button_callback
        self.add_item(str_button)

        end_button = Button(
            label=f"+1 END ({STAT_COSTS['END']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_END",
            disabled=self.vestige_pool < STAT_COSTS["END"],
            row=0,
        )
        end_button.callback = self.stat_button_callback
        self.add_item(end_button)

        dex_button = Button(
            label=f"+1 DEX ({STAT_COSTS['DEX']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_DEX",
            disabled=self.vestige_pool < STAT_COSTS["DEX"],
            row=0,
        )
        dex_button.callback = self.stat_button_callback
        self.add_item(dex_button)

        # Row 1: AGI, MAG, LCK
        agi_button = Button(
            label=f"+1 AGI ({STAT_COSTS['AGI']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_AGI",
            disabled=self.vestige_pool < STAT_COSTS["AGI"],
            row=1,
        )
        agi_button.callback = self.stat_button_callback
        self.add_item(agi_button)

        mag_button = Button(
            label=f"+1 MAG ({STAT_COSTS['MAG']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_MAG",
            disabled=self.vestige_pool < STAT_COSTS["MAG"],
            row=1,
        )
        mag_button.callback = self.stat_button_callback
        self.add_item(mag_button)

        lck_button = Button(
            label=f"+1 LCK ({STAT_COSTS['LCK']} V)",
            style=discord.ButtonStyle.secondary,
            custom_id="increase_stat_LCK",
            disabled=self.vestige_pool < STAT_COSTS["LCK"],
            row=1,
        )
        lck_button.callback = self.stat_button_callback
        self.add_item(lck_button)

    # --- THIS FUNCTION CONTAINS THE FIX ---
    def _execute_stat_increase(self, stat_to_increase: str, cost: int) -> Tuple[bool, str, int]:
        """Returns (success, error_message, new_vestige)"""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT vestige_pool FROM players WHERE discord_id = ?", (self.interaction_user.id,))
            player_data = cur.fetchone()
            
            current_vestige = player_data["vestige_pool"]

            if current_vestige < cost:
                return (False, "You do not have enough Vestige for this.", 0)

            # --- START OF FIX ---
            # 1. Apply the stat change *in memory* first
            self.player_stats.add_base_stat(stat_to_increase, 1)
            
            # 2. Get the NEW max vitals from the updated stats object
            new_max_hp = self.player_stats.max_hp
            new_max_mp = self.player_stats.max_mp
            # --- END OF FIX ---

            new_vestige_pool = current_vestige - cost

            # Update Vestige pool AND set current HP/MP to their new max
            cur.execute(
                """
                UPDATE players 
                SET vestige_pool = ?,
                    current_hp = ?,
                    current_mp = ?
                WHERE discord_id = ?
                """,
                (new_vestige_pool, new_max_hp, new_max_mp, self.interaction_user.id),
            )
            
            # Update base stats in the stats table
            cur.execute(
                "UPDATE stats SET stats_json = ? WHERE discord_id = ?",
                (json.dumps(self.player_stats.to_dict()), self.interaction_user.id),
            )
            return (True, "", new_vestige_pool)
    # --- END HELPER ---

    async def stat_button_callback(self, interaction: discord.Interaction):
        """
        Handles the logic for purchasing a single stat point.
        """
        await interaction.response.defer()

        stat_to_increase = interaction.data["custom_id"].split("_")[-1]  # e.g., "STR"
        cost = STAT_COSTS[stat_to_increase]

        # --- ASYNC FIX ---
        success, error_msg, new_vestige = await asyncio.to_thread(
            self._execute_stat_increase, stat_to_increase, cost
        )
        # --- END FIX ---

        if not success:
            await interaction.followup.send(f"{E.ERROR} {error_msg}", ephemeral=True)
            return

        # Refresh the UI
        # We can just update the player_data dict with the new vestige pool
        # This is safe because it's only used for display
        self.player_data['vestige_pool'] = new_vestige 
        
        new_embed = self.build_status_embed(self.player_data, self.player_stats)
        new_view = StatusUpdateView(
            self.db, self.interaction_user, self.player_data, self.player_stats
        )

        await interaction.edit_original_response(embed=new_embed, view=new_view)
        await interaction.followup.send(
            f"{E.CHECK} Your **{stat_to_increase}** has increased! Your vitals have been refreshed.", ephemeral=True
        )

    @staticmethod
    def build_status_embed(player_data, player_stats):
        """Builds the main embed for the Status Update."""
        embed = discord.Embed(
            title="Status Update",
            description=f"You focus on the energy within you.\nSpend your **{player_data['vestige_pool']} Vestige** to increase your abilities.",
            color=discord.Color.purple(),
        )

        stats_dict = player_stats.get_base_stats_dict()
        stat_block = (
            f"`STR: {stats_dict['STR']:<4}` `END: {stats_dict['END']:<4}` `DEX: {stats_dict['DEX']:<4}`\n"
            f"`AGI: {stats_dict['AGI']:<4}` `MAG: {stats_dict['MAG']:<4}` `LCK: {stats_dict['LCK']:<4}`"
        )
        embed.add_field(name="Base Abilities", value=stat_block, inline=False)
        embed.set_footer(
            text="Your stats will be updated on your profile when you go back."
        )
        return embed


# ======================================================================
# COG LOADER
# ======================================================================


class StatusUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusUpdateCog(bot))