"""
game_systems/character/ui/adventure_menu.py

Primary entry menu for the Adventure System.
Allows players to begin new expeditions or resume ongoing ones.
"""

import discord
import asyncio
import json
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.data.adventure_locations import LOCATIONS
import game_systems.data.emojis as E

# Modular imports
from cogs.ui_helpers import (
    back_to_profile_callback,
    back_to_guild_hall_callback
)
from game_systems.adventure.ui.setup_view import AdventureSetupView
from game_systems.adventure.ui.exploration_view import ExplorationView
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds


# ============================================================
# Adventure Menu View
# ============================================================

class AdventureView(View):
    """Character Menu → Adventure Menu."""

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Begin Expedition
        btn_start = Button(
            label="Begin Expedition",
            style=discord.ButtonStyle.success,
            custom_id="start_adv",
            emoji="⚔️",
            row=0
        )
        btn_start.callback = self.start_adventure_callback
        self.add_item(btn_start)

        # Guild Hall
        btn_guild = Button(
            label="Guild Hall",
            style=discord.ButtonStyle.primary,
            custom_id="gh_link",
            emoji="🏦",
            row=1
        )
        btn_guild.callback = self.guild_hall_callback
        self.add_item(btn_guild)

        # Return to Character Menu
        btn_back = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_prof",
            row=2
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    # ------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Restricts interaction to the original user.
        """
        return interaction.user.id == self.interaction_user.id

    # ------------------------------------------------------------
    # Begin or Resume Adventure
    # ------------------------------------------------------------

    async def start_adventure_callback(self, interaction: discord.Interaction):
        """
        Handles both:
        - Starting a new adventure
        - Resuming a currently active one
        """
        adventure_cog = interaction.client.get_cog("AdventureCommands")

        if not adventure_cog:
            await interaction.response.send_message(
                f"{E.ERROR} The adventure system is currently unavailable.",
                ephemeral=True
            )
            return

        # Check if an adventure is already active
        session = await asyncio.to_thread(
            adventure_cog.manager.get_active_session,
            self.interaction_user.id
        )

        # --------------------------------------------------------
        # Resume existing adventure
        # --------------------------------------------------------
        if session:
            if not interaction.response.is_done():
                await interaction.response.defer()

            loc_id = session["location_id"]

            try:
                logs = json.loads(session["logs"])
            except Exception:
                logs = []

            # Fetch stats and vitals
            stats_json = await asyncio.to_thread(
                self.db.get_player_stats_json,
                self.interaction_user.id
            )
            stats = PlayerStats.from_dict(stats_json)

            vitals = await asyncio.to_thread(
                self.db.get_player_vitals,
                self.interaction_user.id
            )

            embed = AdventureEmbeds.build_exploration_embed(
                loc_id, logs, stats, vitals, session
            )

            view = ExplorationView(
                self.db,
                adventure_cog.manager,
                loc_id,
                logs,
                self.interaction_user,
                stats,
            )

            await interaction.edit_original_response(embed=embed, view=view)
            return

        # --------------------------------------------------------
        # Start new adventure
        # --------------------------------------------------------
        await interaction.response.defer()

        guild_member = await asyncio.to_thread(
            self.db.get_guild_member_data,
            self.interaction_user.id
        )
        rank = guild_member["rank"] if guild_member else "F"

        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description=(
                "*The great gates of the city loom overhead, iron-bound and weathered by countless journeys.*\n\n"
                "Select a destination to begin your expedition."
            ),
            color=discord.Color.dark_green()
        )

        view = AdventureSetupView(
            self.db,
            adventure_cog.manager,
            self.interaction_user,
            rank
        )
        view.back_btn.callback = back_to_profile_callback

        await interaction.edit_original_response(embed=embed, view=view)

    # ------------------------------------------------------------

    async def guild_hall_callback(self, interaction: discord.Interaction):
        """Returns the user to the Guild Hall interface."""
        await back_to_guild_hall_callback(interaction)
