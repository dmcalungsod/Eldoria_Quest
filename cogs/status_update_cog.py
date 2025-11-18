"""
cogs/status_update_cog.py

Handles the "Status Update" UI where players
spend Vestige to increase their base stats,
in the style of Danmachi.
"""

import asyncio
import json
import math  # <-- NEW IMPORT
import sqlite3
from typing import Tuple

import discord
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback

# --- Stat Costs ---
STAT_COSTS = {
    "STR": 10,
    "END": 10,
    "DEX": 10,
    "AGI": 12,
    "MAG": 12,
    "LCK": 20,
}

# --- NEW: STAT EXP THRESHOLD ---
STAT_EXP_THRESHOLD = 100
# --- END NEW ---


# --- NEW HELPER FUNCTION ---
def _make_progress_bar(current: float, max_val: int, bar_length: int = 10) -> str:
    """Generates a text-based progress bar."""
    current = min(current, max_val)
    percentage = current / max_val
    filled_length = int(percentage * bar_length)
    bar = "█" * filled_length + "─" * (bar_length - filled_length)
    return f"[{bar}] {math.floor(current)}/{max_val}"


# --- END NEW HELPER FUNCTION ---


# ==========================================================
# STATUS UPDATE VIEW
# ==========================================================
class StatusUpdateView(View):
    """
    UI for the Status Update system.
    Players spend Vestige to increase stats.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: sqlite3.Row,
        player_stats: PlayerStats,
        stats_row: sqlite3.Row,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Convert sqlite Row → dict so we can safely mutate values
        self.player_data = dict(player_data)
        self.player_stats = player_stats
        self.stats_row = stats_row
        self.vestige_pool = self.player_data["vestige_pool"]

        # Add stat buttons
        self.add_stat_buttons()

        # Back button
        self.back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_profile",
            row=2,
        )
        self.back_button.callback = back_to_profile_callback
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your status.", ephemeral=True)
            return False
        return True

    def add_stat_buttons(self):
        """Create one button per stat."""

        def make_btn(stat: str, row: int):
            return Button(
                label=f"+1 {stat} ({STAT_COSTS[stat]} {E.VESTIGE})",
                style=discord.ButtonStyle.secondary,
                custom_id=f"increase_stat_{stat}",
                disabled=self.vestige_pool < STAT_COSTS[stat],
                emoji=None,
                row=row,
            )

        # Row 0
        for stat in ["STR", "END", "DEX"]:
            btn = make_btn(stat, row=0)
            btn.callback = self.stat_button_callback
            self.add_item(btn)

        # Row 1
        for stat in ["AGI", "MAG", "LCK"]:
            btn = make_btn(stat, row=1)
            btn.callback = self.stat_button_callback
            self.add_item(btn)

    # ==========================================================
    # DATABASE THREAD WRAPPER
    # ==========================================================
    def _execute_stat_increase(self, stat: str, cost: int) -> Tuple[bool, str, int]:
        """Runs the stat update + HP/MP refresh in a DB thread."""

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT vestige_pool FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            pdata = cur.fetchone()
            current_vestige = pdata["vestige_pool"]

            if current_vestige < cost:
                return (False, "You do not have enough Vestige for this.", 0)

            # Apply stat increase in memory
            self.player_stats.add_base_stat(stat, 1)

            # Compute new max vitals
            new_max_hp = self.player_stats.max_hp
            new_max_mp = self.player_stats.max_mp

            new_vestige_pool = current_vestige - cost

            # Update player table
            cur.execute(
                """
                UPDATE players
                SET vestige_pool = ?, current_hp = ?, current_mp = ?
                WHERE discord_id = ?
                """,
                (new_vestige_pool, new_max_hp, new_max_mp, self.interaction_user.id),
            )

            # Update stats JSON
            cur.execute(
                "UPDATE stats SET stats_json = ? WHERE discord_id = ?",
                (json.dumps(self.player_stats.to_dict()), self.interaction_user.id),
            )

            return (True, "", new_vestige_pool)

    # ==========================================================
    # BUTTON CALLBACK
    # ==========================================================
    async def stat_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        stat = interaction.data["custom_id"].split("_")[-1]
        cost = STAT_COSTS[stat]

        success, error_msg, new_vestige = await asyncio.to_thread(self._execute_stat_increase, stat, cost)

        if not success:
            await interaction.followup.send(f"{E.ERROR} {error_msg}", ephemeral=True)
            return

        # Update local Vestige pool
        self.player_data["vestige_pool"] = new_vestige

        # --- Re-fetch stats_row for updated JSON ---
        new_stats_row = await asyncio.to_thread(self.db.get_player_stats_row, self.interaction_user.id)

        # Rebuild UI
        new_embed = self.build_status_embed(self.player_data, self.player_stats, new_stats_row)
        new_view = StatusUpdateView(self.db, self.interaction_user, self.player_data, self.player_stats, new_stats_row)

        # Preserve callback on back button
        new_view.back_button.callback = self.back_button.callback
        new_view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=new_embed, view=new_view)

    # ==========================================================
    # EMBED
    # ==========================================================
    @staticmethod
    def build_status_embed(player_data, player_stats, stats_row):
        embed = discord.Embed(
            title="🜁 Attribute Awakening",
            description=(
                "*You stand before an ancient monolith etched with runes that pulse faintly "
                "at your presence. Each glyph resonates with the essence of your growing power.*\n\n"
                "Here, you may channel Vestige to refine the core attributes that shape your fate.\n\n"
                f"**Current Vestige:** {player_data['vestige_pool']} {E.VESTIGE}"
            ),
            color=discord.Color.purple(),
        )

        stats = player_stats.get_base_stats_dict()

        formatted_stats = (
            f"`STR: {stats['STR']:<4}` `END: {stats['END']:<4}` `DEX: {stats['DEX']:<4}`\n"
            f"`AGI: {stats['AGI']:<4}` `MAG: {stats['MAG']:<4}` `LCK: {stats['LCK']:<4}`"
        )

        embed.add_field(
            name="Current Attributes",
            value=formatted_stats,
            inline=False,
        )

        # --- NEW: Practice EXP Bars ---
        practice_bars = (
            f"`STR:` {_make_progress_bar(stats_row['str_exp'], STAT_EXP_THRESHOLD)}\n"
            f"`END:` {_make_progress_bar(stats_row['end_exp'], STAT_EXP_THRESHOLD)}\n"
            f"`DEX:` {_make_progress_bar(stats_row['dex_exp'], STAT_EXP_THRESHOLD)}\n"
            f"`AGI:` {_make_progress_bar(stats_row['agi_exp'], STAT_EXP_THRESHOLD)}\n"
            f"`MAG:` {_make_progress_bar(stats_row['mag_exp'], STAT_EXP_THRESHOLD)}\n"
            f"`LCK:` {_make_progress_bar(stats_row['lck_exp'], STAT_EXP_THRESHOLD)}"
        )

        embed.add_field(
            name="Attribute Practice",
            value=practice_bars,
            inline=False,
        )

        embed.set_footer(text="Each attribute point reshapes the spirit. Choose wisely.")
        return embed


# ==========================================================
# COG LOADER
# ==========================================================
class StatusUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusUpdateCog(bot))
