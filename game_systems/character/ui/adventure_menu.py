"""
game_systems/character/ui/adventure_menu.py

Primary entry menu for the Adventure System.
Hardened: Safe JSON parsing for session resumption.
"""

import asyncio
import json
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E

# Modular imports
from cogs.ui_helpers import back_to_guild_hall_callback, back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.adventure.ui.exploration_view import ExplorationView
from game_systems.adventure.ui.setup_view import AdventureSetupView
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.ui.adventure_menu")


class AdventureView(View):
    """Character Menu → Adventure Menu."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        active_session: bool = False,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Determine button state based on active session
        label = "Resume Expedition" if active_session else "Begin Expedition"
        emoji = "🧭" if active_session else "⚔️"

        # Begin/Resume Expedition
        btn_start = Button(
            label=label,
            style=discord.ButtonStyle.success,
            custom_id="start_adv",
            emoji=emoji,
            row=0,
        )
        btn_start.callback = self.start_adventure_callback
        self.add_item(btn_start)

        # Return to Character Menu
        btn_back = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_prof",
            row=1,
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    # ------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Restricts interaction to the original user.
        """
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your session.", ephemeral=True)
            return False
        return True

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
                f"{E.ERROR} The adventure system is currently unavailable.", ephemeral=True
            )
            return

        # Check if an adventure is already active (threaded)
        session = await asyncio.to_thread(adventure_cog.manager.get_active_session, self.interaction_user.id)

        # --------------------------------------------------------
        # Resume existing adventure
        # --------------------------------------------------------
        if session:
            if not interaction.response.is_done():
                await interaction.response.defer()

            loc_id = session["location_id"]

            try:
                logs = json.loads(session["logs"]) if session["logs"] else []
            except json.JSONDecodeError:
                logs = ["*Log corrupted or lost.*"]

            # Parse active monster to update button state
            active_monster = None
            if session["active_monster_json"]:
                try:
                    active_monster = json.loads(session["active_monster_json"])
                except Exception:
                    active_monster = None

            # Fetch stats and vitals
            try:
                stats_json = await asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
                stats = PlayerStats.from_dict(stats_json)
                vitals = await asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)
                player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
                skills = await asyncio.to_thread(self.db.get_combat_skills, self.interaction_user.id)
                class_id = player_data["class_id"] if player_data else 1

                embed = AdventureEmbeds.build_exploration_embed(loc_id, logs, stats, vitals, active_monster)

                view = ExplorationView(
                    self.db,
                    adventure_cog.manager,
                    loc_id,
                    logs,
                    self.interaction_user,
                    stats,
                    vitals=vitals,
                    active_monster=active_monster,
                    class_id=class_id,
                    skills=skills,
                )

                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Resume adventure failed: {e}", exc_info=True)
                await interaction.followup.send("Error resuming session.", ephemeral=True)
            return

        # --------------------------------------------------------
        # Start new adventure
        # --------------------------------------------------------
        await interaction.response.defer()

        try:
            # Parallel fetch of guild rank and player level
            guild_member, player_data = await asyncio.gather(
                asyncio.to_thread(self.db.get_guild_member_data, self.interaction_user.id),
                asyncio.to_thread(self.db.get_player, self.interaction_user.id),
            )
            rank = guild_member["rank"] if guild_member else "F"
            level = player_data["level"] if player_data else 1

            embed = discord.Embed(
                title=f"{E.MAP} Prepare for Expedition",
                description=(
                    "*The great gates of the city loom overhead, iron-bound and weathered by countless journeys.*\n\n"
                    "Select a destination to begin your expedition."
                ),
                color=discord.Color.dark_green(),
            )

            view = AdventureSetupView(self.db, adventure_cog.manager, self.interaction_user, rank, level)
            view.back_btn.callback = back_to_profile_callback

            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Start adventure menu failed: {e}", exc_info=True)
            await interaction.followup.send("Error loading destinations.", ephemeral=True)

    # ------------------------------------------------------------

    async def guild_hall_callback(self, interaction: discord.Interaction):
        """Returns the user to the Guild Hall interface."""
        await back_to_guild_hall_callback(interaction)
