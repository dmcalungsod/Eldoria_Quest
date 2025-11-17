"""
cogs/infirmary_cog.py

Handles the Adventurer's Guild Infirmary UI where adventurers
spend Aurum to restore HP and MP.

Healing rate:
    • 0.5 Aurum per missing HP (rounded up)
    • Minimum cost: 1 Aurum if any HP is missing
    • MP restoration is included in the treatment cost (currently free bonus)

Refactored to follow the one-UI policy (no ephemeral messages).
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
# Healing cost: 0.5 Aurum per HP (rounded up, min 1 if missing > 0)
# ---------------------------------------------------------------------
def infirmary_cost(missing_hp: int) -> int:
    if missing_hp <= 0:
        return 0
    return max(1, math.ceil(missing_hp * 0.5))


# =====================================================================
# Infirmary View
# =====================================================================
class InfirmaryView(View):
    """
    The Adventurer’s Guild Infirmary interface.
    Displays HP, MP, treatment cost, and offers paid healing.
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

        # Derived state
        self.current_hp = player_data["current_hp"]
        self.current_mp = player_data["current_mp"]  # Added MP
        self.max_hp = player_stats.max_hp
        self.max_mp = player_stats.max_mp            # Added Max MP
        self.current_aurum = player_data["aurum"]

        self.missing_hp = max(0, self.max_hp - self.current_hp)
        self.missing_mp = max(0, self.max_mp - self.current_mp) # Calculate missing MP
        
        # Cost is based on HP loss, but healing restores both
        self.heal_cost = infirmary_cost(self.missing_hp)

        # --------------------------------------------------------------
        # Treatment Button
        # --------------------------------------------------------------
        # Enable healing if either HP or MP is missing
        if self.missing_hp <= 0 and self.missing_mp <= 0:
            heal_label = "You are already in full condition."
            heal_disabled = True
            heal_style = discord.ButtonStyle.secondary
        else:
            # --- FIX: Removed {E.AURUM} from label, replaced with text ---
            heal_label = f"Receive Treatment ({self.heal_cost} Aurum)"
            heal_disabled = self.current_aurum < self.heal_cost
            heal_style = discord.ButtonStyle.primary

        heal_button = Button(
            label=heal_label,
            style=heal_style,
            custom_id="infirmary_heal",
            emoji=E.AURUM,
            row=0,
            disabled=heal_disabled,
        )
        heal_button.callback = self.heal_callback
        self.add_item(heal_button)

        # --------------------------------------------------------------
        # Back Button
        # --------------------------------------------------------------
        self.back_button = Button(
            label="Return — Guild Hall",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def set_back_button(self, callback_function, label: str = "Back"):
        """Allow parent views to override the 'Return' button."""
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "These halls serve another adventurer.",
                ephemeral=True
            )
            return False
        return True

    # -----------------------------------------------------------------
    # Blocking DB Transaction
    # -----------------------------------------------------------------
    def _execute_heal_transaction(self) -> Tuple[bool, str]:
        """
        Conducts the DB transaction verifying and applying treatment.
        Returns: (success, status_message)
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # Reload authoritative record
            cur.execute(
                "SELECT current_hp, current_mp, aurum FROM players WHERE discord_id = ?",
                (self.interaction_user.id,)
            )
            row = cur.fetchone()
            if not row:
                return False, "Adventurer record could not be located."

            current_hp = row["current_hp"]
            current_mp = row["current_mp"] # Fetch current MP
            aurum = row["aurum"]

            # Load fresh stats for true max HP/MP
            stats_json = self.db.get_player_stats_json(self.interaction_user.id)
            player_stats = PlayerStats.from_dict(stats_json)
            max_hp = player_stats.max_hp
            max_mp = player_stats.max_mp # Fetch max MP

            missing_hp = max(0, max_hp - current_hp)
            missing_mp = max(0, max_mp - current_mp)
            
            cost = infirmary_cost(missing_hp)

            if missing_hp <= 0 and missing_mp <= 0:
                return False, "You are already fully restored."
            if aurum < cost:
                return False, f"Insufficient Aurum. Treatment requires {cost} {E.AURUM}."

            # Apply healing (Restore both HP and MP)
            new_hp = max_hp
            new_mp = max_mp
            new_aurum = aurum - cost

            cur.execute(
                "UPDATE players SET current_hp = ?, current_mp = ?, aurum = ? WHERE discord_id = ?",
                (new_hp, new_mp, new_aurum, self.interaction_user.id),
            )
            conn.commit()

            return True, (
                f"You paid {cost} {E.AURUM}. "
                f"Your condition has been treated — HP & MP fully restored."
            )

    # -----------------------------------------------------------------
    # Heal Button Callback
    # -----------------------------------------------------------------
    async def heal_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Run DB transaction off-thread
        success, message = await asyncio.to_thread(self._execute_heal_transaction)

        # Reload fresh data for UI state
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)

        embed = InfirmaryView.build_infirmary_embed(
            player_data,
            player_stats,
            status_message=message,
            success=success
        )

        new_view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)

        # Preserve custom back-behavior from parent view
        new_view.back_button.callback = self.back_button.callback
        new_view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=embed, view=new_view)

    # -----------------------------------------------------------------
    # Embed Builder
    # -----------------------------------------------------------------
    @staticmethod
    def build_infirmary_embed(
        player_data: sqlite3.Row,
        player_stats: PlayerStats,
        status_message: str = None,
        success: bool = True
    ) -> discord.Embed:

        current_hp = player_data["current_hp"]
        current_mp = player_data["current_mp"] # Added MP
        max_hp = player_stats.max_hp
        max_mp = player_stats.max_mp # Added Max MP
        current_aurum = player_data["aurum"]

        missing_hp = max(0, max_hp - current_hp)
        missing_mp = max(0, max_mp - current_mp) # Calculate missing MP
        
        cost = infirmary_cost(missing_hp)

        description = (
            "Soft green lanternlight fills the chamber as a Guild Healer works calmly among "
            "rows of treated bandages and tinctures. Their craft is precise — compassion measured, "
            "but genuine.\n\n"
            "**Condition**\n"
            f"> {E.HP} **HP:** {current_hp} / {max_hp}\n"
            f"> {E.MP} **MP:** {current_mp} / {max_mp}\n\n"
            "**Purse**\n"
            f"> {E.AURUM} **Aurum:** {current_aurum}\n\n"
        )

        if missing_hp > 0 or missing_mp > 0:
            description += (
                f"A full course of treatment will cost **{cost} {E.AURUM}** "
                f"(0.5 Aurum per missing HP, rounded up)."
            )
        else:
            description += "You stand in peak condition; no treatment is required."

        embed = discord.Embed(
            title="🏥 Adventurer’s Guild — Infirmary",
            description=description,
            color=discord.Color.dark_grey(),
        )

        if status_message:
            icon = E.CHECK if success else E.ERROR
            field_title = "Treatment Complete" if success else "Treatment Declined"
            embed.add_field(name=field_title, value=f"{icon} {status_message}", inline=False)
            embed.color = discord.Color.green() if success else discord.Color.red()

        embed.set_footer(text="Select 'Receive Treatment' to spend Aurum and restore HP & MP.")

        return embed


# =====================================================================
# COG LOADER
# =====================================================================
class InfirmaryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @commands.Cog.listener()
    async def on_ready(self):
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(InfirmaryCog(bot))