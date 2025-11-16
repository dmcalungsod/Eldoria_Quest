"""
cogs/infirmary_cog.py

Handles the Guild Infirmary UI where players
spend Aurum to restore their HP.
"""

import discord
from discord.ui import View, Button
from discord.ext import commands
import sqlite3
import asyncio
from typing import Tuple

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback

# --- Healing Cost ---
# 1 Aurum per 1 HP restored.
HEAL_COST_PER_HP = 1


class InfirmaryView(View):
    """
    The main UI for the Guild Infirmary.
    Shows HP, cost to heal, and a "Heal" button.
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

        self.current_hp = player_data["current_hp"]
        self.max_hp = player_stats.max_hp
        self.current_aurum = player_data["aurum"]

        self.hp_to_heal = self.max_hp - self.current_hp
        self.heal_cost = self.hp_to_heal * HEAL_COST_PER_HP

        # --- Add the Heal Button ---
        heal_button = Button(
            # FIX: Move E.AURUM from 'label' to 'emoji'
            label=f"Heal Wounds ({self.heal_cost})",
            style=discord.ButtonStyle.success,
            custom_id="infirmary_heal",
            emoji=discord.PartialEmoji.from_str(E.AURUM), # Use PartialEmoji
            row=0
        )

        if self.hp_to_heal <= 0:
            heal_button.label = "You are already at full health."
            heal_button.disabled = True
        elif self.current_aurum < self.heal_cost:
            # FIX: Remove emoji from disabled label
            heal_button.label = f"Not enough Aurum ({self.heal_cost})"
            heal_button.disabled = True
        
        heal_button.callback = self.heal_callback
        self.add_item(heal_button)

        # --- Add the back button ---
        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your guild.", ephemeral=True
            )
            return False
        return True

    # --- NEW HELPER FOR ASYNC ---
    def _execute_heal(self) -> Tuple[bool, str]:
        """
        Runs the blocking DB transaction for healing.
        Returns (success, message)
        """
        # Re-check everything inside the transaction
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT current_hp, aurum FROM players WHERE discord_id = ?",
                (self.interaction_user.id,)
            )
            player_data = cur.fetchone()
            
            stats_json = self.db.get_player_stats_json(self.interaction_user.id)
            player_stats = PlayerStats.from_dict(stats_json)

            hp_to_heal = player_stats.max_hp - player_data["current_hp"]
            cost = hp_to_heal * HEAL_COST_PER_HP

            if hp_to_heal <= 0:
                return (False, "You are already at full health.")
            if player_data["aurum"] < cost:
                return (False, f"You do not have enough Aurum. You need {cost} {E.AURUM}.")

            # --- Success: Perform the transaction ---
            new_aurum = player_data["aurum"] - cost
            new_hp = player_stats.max_hp
            
            cur.execute(
                "UPDATE players SET current_hp = ?, aurum = ? WHERE discord_id = ?",
                (new_hp, new_aurum, self.interaction_user.id)
            )
            
            return (True, f"You paid {cost} {E.AURUM} and your wounds have been fully treated. You are now at {new_hp} HP.")

    async def heal_callback(self, interaction: discord.Interaction):
        """Handles the logic for healing the player."""
        await interaction.response.defer()

        # --- ASYNC FIX ---
        success, message = await asyncio.to_thread(self._execute_heal)
        # --- END FIX ---

        if not success:
            await interaction.followup.send(f"{E.ERROR} {message}", ephemeral=True)
            return

        await interaction.followup.send(f"{E.CHECK} {message}", ephemeral=True)

        # --- Refresh the UI ---
        # We need to get the new player data and stats
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)
        
        new_embed = self.build_infirmary_embed(player_data, player_stats)
        new_view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        
        await interaction.edit_original_response(embed=new_embed, view=new_view)


    @staticmethod
    def build_infirmary_embed(player_data: sqlite3.Row, player_stats: PlayerStats) -> discord.Embed:
        """Builds the main embed for the Guild Infirmary."""
        
        current_hp = player_data["current_hp"]
        max_hp = player_stats.max_hp
        current_aurum = player_data["aurum"]
        
        hp_to_heal = max_hp - current_hp
        heal_cost = hp_to_heal * HEAL_COST_PER_HP

        description = (
            f"The air smells of antiseptic herbs. A Guild Healer offers you a cot.\n"
            f"'Wounds from the field, adventurer? We can treat those, for a donation.'\n\n"
            f"**Your Condition:**\n"
            f"> {E.HP} **HP:** {current_hp} / {max_hp}\n\n"
            f"**Your Funds:**\n"
            # FIX: Embeds can render custom emojis, so this is correct.
            f"> {E.AURUM} **Aurum:** {current_aurum}\n\n"
        )
        
        if hp_to_heal > 0:
            description += f"A full recovery will cost **{heal_cost} {E.AURUM}**."
        else:
            description += "You are in perfect health."

        embed = discord.Embed(
            title="Guild Infirmary",
            description=description,
            color=discord.Color.light_grey(),
        )
        return embed


# ======================================================================
# COG LOADER
# ======================================================================


class InfirmaryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(InfirmaryCog(bot))