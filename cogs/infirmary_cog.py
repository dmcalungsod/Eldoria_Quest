"""
cogs/infirmary_cog.py

Handles the Adventurer's Guild Infirmary UI where players
spend Aurum to restore their HP.

Healing policy: 0.5 Aurum per 1 HP (rounded up).
"""

import discord
from discord.ui import View, Button
from discord.ext import commands
import sqlite3
import asyncio
from typing import Tuple
import math

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback


# ---------------------------------------------------------------------
# Cost helper (0.5 Aurum per HP, rounded up; minimum 1 Aurum if any HP missing)
# ---------------------------------------------------------------------
def infirmary_cost(missing_hp: int) -> int:
    if missing_hp <= 0:
        return 0
    # 0.5 Aurum per HP -> multiply then round up
    return max(1, math.ceil(missing_hp * 0.5))


# =====================================================================
# Infirmary View
# =====================================================================
class InfirmaryView(View):
    """
    The main UI for the Adventurer's Guild Infirmary.
    Shows HP, cost to heal, and a 'Receive Treatment' button.
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

        # derived values
        self.current_hp = player_data["current_hp"]
        self.max_hp = player_stats.max_hp
        self.current_aurum = player_data.get("aurum", 0)

        self.missing_hp = max(0, self.max_hp - self.current_hp)
        self.heal_cost = infirmary_cost(self.missing_hp)

        # --- Treatment button ---
        # label includes cost if healing is required; otherwise indicates full health
        if self.missing_hp <= 0:
            heal_label = "You are already at full health."
            heal_disabled = True
        else:
            heal_label = f"Receive Treatment ({self.heal_cost} {E.AURUM})"
            heal_disabled = self.current_aurum < self.heal_cost

        heal_button = Button(
            label=heal_label,
            style=discord.ButtonStyle.primary if not heal_disabled else discord.ButtonStyle.secondary,
            custom_id="infirmary_heal",
            emoji=E.AURUM,
            row=0,
        )
        heal_button.disabled = heal_disabled
        heal_button.callback = self.heal_callback
        self.add_item(heal_button)

        # --- Back button ---
        self.back_button = Button(
            label="Return — Guild Hall",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def set_back_button(self, callback_function, label: str = "Back"):
        """Allow parent views to override the back button behavior/label."""
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your guild.", ephemeral=True)
            return False
        return True

    # -----------------------------------------------------------------
    # Blocking DB transaction executed in a thread
    # -----------------------------------------------------------------
    def _execute_heal_transaction(self) -> Tuple[bool, str]:
        """
        Runs the blocking DB transaction to validate and apply healing.
        Returns (success, message).
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Re-load authoritative values inside the transaction
            cur.execute(
                "SELECT current_hp, aurum FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            row = cur.fetchone()
            if not row:
                return False, "Player data not found."

            current_hp = row["current_hp"]
            aurum_on_hand = row["aurum"]

            # Recompute max HP from stats (pull fresh stats JSON)
            stats_json = self.db.get_player_stats_json(self.interaction_user.id)
            player_stats = PlayerStats.from_dict(stats_json)
            max_hp = player_stats.max_hp

            missing_hp = max(0, max_hp - current_hp)
            cost = infirmary_cost(missing_hp)

            if missing_hp <= 0:
                return False, "You are already at full health."
            if aurum_on_hand < cost:
                return False, f"You do not have enough Aurum. You need {cost} {E.AURUM}."

            # Perform update
            new_aurum = aurum_on_hand - cost
            new_hp = max_hp

            cur.execute(
                "UPDATE players SET current_hp = ?, aurum = ? WHERE discord_id = ?",
                (new_hp, new_aurum, self.interaction_user.id),
            )
            conn.commit()

            return True, f"You paid {cost} {E.AURUM}. Your wounds have been treated — HP restored to {new_hp}."

    # -----------------------------------------------------------------
    # Interaction callback (async) — wraps the blocking transaction
    # -----------------------------------------------------------------
    async def heal_callback(self, interaction: discord.Interaction):
        """
        Handles the 'Receive Treatment' action. Runs DB work in a background thread.
        """
        await interaction.response.defer()

        # Run the transaction in a thread to avoid blocking the event loop
        success, message = await asyncio.to_thread(self._execute_heal_transaction)

        if not success:
            await interaction.followup.send(f"{E.ERROR} {message}", ephemeral=True)
            return

        await interaction.followup.send(f"{E.CHECK} {message}", ephemeral=True)

        # Refresh player data & embed
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)

        new_embed = InfirmaryView.build_infirmary_embed(player_data, player_stats)
        new_view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        # preserve back button behavior
        new_view.back_button.callback = self.back_button.callback
        new_view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=new_embed, view=new_view)

    # -----------------------------------------------------------------
    # Embed builder
    # -----------------------------------------------------------------
    @staticmethod
    def build_infirmary_embed(player_data: sqlite3.Row, player_stats: PlayerStats) -> discord.Embed:
        """Builds the embed for the Adventurer's Guild Infirmary."""
        current_hp = player_data["current_hp"]
        max_hp = player_stats.max_hp
        current_aurum = player_data.get("aurum", 0)

        missing_hp = max(0, max_hp - current_hp)
        cost = infirmary_cost(missing_hp)

        description = (
            "The infirmary's lamps glow with muted green light. A Guild Healer offers a quiet, "
            "efficient nod — treatment here is pragmatic, not sentimental.\n\n"
            "**Condition:**\n"
            f"> {E.HP} **HP:** {current_hp} / {max_hp}\n\n"
            "**Funds:**\n"
            f"> {E.AURUM} **Aurum:** {current_aurum}\n\n"
        )

        if missing_hp > 0:
            description += f"A full course of treatment will cost **{cost} {E.AURUM}** (0.5 Aurum per missing HP, rounded up)."
        else:
            description += "You are in perfect health; no treatment required."

        embed = discord.Embed(
            title="🏥 Adventurer's Guild — Infirmary",
            description=description,
            color=discord.Color.dark_grey(),
        )

        embed.set_footer(text="Select 'Receive Treatment' to expend Aurum and restore HP.")
        return embed


# ======================================================================
# COG LOADER
# ======================================================================
class InfirmaryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @commands.Cog.listener()
    async def on_ready(self):
        # optional: log if desired
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(InfirmaryCog(bot))
