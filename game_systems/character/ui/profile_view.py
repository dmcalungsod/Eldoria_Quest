"""
game_systems/character/ui/profile_view.py
"""

import discord
import asyncio
import json
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# Modular imports
from .abilities_view import AbilitiesView
from .adventure_menu import AdventureView
from cogs.status_update_cog import StatusUpdateView

# Helper imports (careful: avoid circular dependencies)
import cogs.ui_helpers as ui_helpers


class CharacterTabView(View):
    """
    Main interface for an Adventurer's Character Profile.
    Provides access to abilities, expeditions, and vitals.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # --- Arcane Ledger ---
        btn_abilities = Button(
            label="Arcane Ledger",
            style=discord.ButtonStyle.primary,
            custom_id="abilities",
            emoji="📜",
            row=0
        )
        btn_abilities.callback = self.abilities_callback
        self.add_item(btn_abilities)

        # --- Expedition / Adventure ---
        btn_adventure = Button(
            label="Expeditions",
            style=discord.ButtonStyle.success,
            custom_id="adventure",
            emoji="🗺️",
            row=0
        )
        btn_adventure.callback = self.adventure_callback
        self.add_item(btn_adventure)

        # --- Status: Vestige & Vitals ---
        btn_status = Button(
            label="Vestige & Vitals",
            style=discord.ButtonStyle.secondary,
            custom_id="status",
            emoji=E.VESTIGE,
            row=1
        )
        btn_status.callback = self.status_callback
        self.add_item(btn_status)

    # ------------------------------------------------------------------
    # Interaction Permissions Check
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This profile does not belong to you.",
                ephemeral=True
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    async def abilities_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="📜 Arcane Ledger",
            description=(
                "*Your gathered knowledge, arms, and practiced arts.*\n"
                "Manage inventory, equipment, and skills."
            ),
            color=discord.Color.purple()
        )
        view = AbilitiesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def adventure_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="🗺️ Expeditions",
            description=(
                "*Beyond the city wards, the world grows darker.*\n"
                "Begin or resume an expedition into the wilds of Eldoria."
            ),
            color=discord.Color.dark_teal()
        )
        view = AdventureView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def status_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fetch player data and stats concurrently
        p_data, s_row = await asyncio.gather(
            asyncio.to_thread(self.db.get_player, self.interaction_user.id),
            asyncio.to_thread(self.db.get_player_stats_row, self.interaction_user.id)
        )

        stats = PlayerStats.from_dict(json.loads(s_row["stats_json"]))

        embed = StatusUpdateView.build_status_embed(p_data, stats, s_row)
        view = StatusUpdateView(self.db, self.interaction_user, p_data, stats, s_row)

        # Assign profile return callback
        view.back_button.callback = ui_helpers.back_to_profile_callback

        await interaction.edit_original_response(embed=embed, view=view)
