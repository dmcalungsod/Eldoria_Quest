"""
game_systems/character/ui/adventure_menu.py

Primary entry menu for the Adventure System.
Hardened: Safe JSON parsing for session resumption.
"""

import asyncio
import datetime
import json
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E

# Modular imports
from cogs.ui_helpers import back_to_guild_hall_callback, back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.adventure.ui.setup_view import AdventureSetupView
from game_systems.adventure.ui.status_view import AdventureStatusView
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.world_time import WorldTime

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
            await interaction.response.send_message(
                "This is not your session.", ephemeral=True
            )
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
                f"{E.ERROR} The adventure system is currently unavailable.",
                ephemeral=True,
            )
            return

        # Check if an adventure is already active (threaded)
        session = await asyncio.to_thread(
            adventure_cog.manager.get_active_session, self.interaction_user.id
        )

        # --------------------------------------------------------
        # Resume existing adventure
        # --------------------------------------------------------
        if session:
            if not interaction.response.is_done():
                await interaction.response.defer()

            status = session.get("status")
            loc_id = session["location_id"]

            # === CASE 1: IN PROGRESS (Show Status) ===
            if status == "in_progress":
                try:
                    # Calculate time remaining
                    end_time_str = session.get("end_time")
                    time_str = "Unknown"
                    if end_time_str:
                        end_time = datetime.datetime.fromisoformat(end_time_str)
                        now = WorldTime.now()
                        remaining = end_time - now
                        if remaining.total_seconds() <= 0:
                            time_str = "Complete!"
                        else:
                            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                            minutes, _ = divmod(remainder, 60)
                            time_str = f"{hours}h {minutes}m"

                    loc_data = LOCATIONS.get(loc_id, {})
                    steps = session.get("steps_completed", 0)

                    embed = AdventureEmbeds.build_status_embed(session, loc_data, time_str, steps)
                    view = AdventureStatusView(self.db, adventure_cog.manager, self.interaction_user)
                    await interaction.edit_original_response(embed=embed, view=view)
                except Exception as e:
                    logger.error(f"Error showing status: {e}", exc_info=True)
                    await interaction.followup.send("Error loading status.", ephemeral=True)
                return

            # === CASE 2: COMPLETED (Claim Rewards) ===
            elif status == "completed":
                try:
                    summary = await asyncio.to_thread(adventure_cog.manager.end_adventure, self.interaction_user.id)
                    if summary:
                        embed = AdventureEmbeds.build_summary_embed(summary, loc_id)

                        view = View()
                        btn = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
                        btn.callback = back_to_profile_callback
                        view.add_item(btn)

                        await interaction.edit_original_response(embed=embed, view=view)
                    else:
                        await interaction.followup.send("Error processing rewards.", ephemeral=True)
                except Exception as e:
                    logger.error(f"Error claiming rewards: {e}", exc_info=True)
                    await interaction.followup.send("Error processing rewards.", ephemeral=True)
                return

            # === CASE 3: FAILED (Death Report) ===
            elif status == "failed":
                try:
                    loc_data = LOCATIONS.get(loc_id, {})
                    embed = AdventureEmbeds.build_death_embed(session, loc_data)

                    view = View()
                    async def ack_callback(inter):
                         if inter.user.id != self.interaction_user.id:
                             await inter.response.send_message("This is not your session.", ephemeral=True)
                             return
                         await asyncio.to_thread(self.db.end_adventure_session, self.interaction_user.id)
                         await back_to_profile_callback(inter)

                    btn = Button(label="Acknowledge Loss", style=discord.ButtonStyle.danger)
                    btn.callback = ack_callback
                    view.add_item(btn)

                    await interaction.edit_original_response(embed=embed, view=view)
                except Exception as e:
                    logger.error(f"Error showing death report: {e}", exc_info=True)
                    await interaction.followup.send("Error loading report.", ephemeral=True)
                return

            loc_id = session.get("location_id")

            try:
                # CASE 1: Completed -> Show Rewards
                if status == "completed":
                    summary = await asyncio.to_thread(
                        adventure_cog.manager.end_adventure, self.interaction_user.id
                    )
                    if not summary:
                        await interaction.followup.send(
                            "Error processing rewards.", ephemeral=True
                        )
                        return

                    embed = AdventureEmbeds.build_summary_embed(summary, loc_id)

                    view = View()
                    back_btn = Button(
                        label="Return to Profile", style=discord.ButtonStyle.grey
                    )
                    back_btn.callback = back_to_profile_callback
                    view.add_item(back_btn)

                    await interaction.edit_original_response(embed=embed, view=view)
                    return

                # CASE 2: Failed -> Show Death Report
                if status == "failed":
                    from game_systems.data.adventure_locations import LOCATIONS
                    loc_data = LOCATIONS.get(loc_id, {})
                    embed = AdventureEmbeds.build_death_embed(session, loc_data)

                    view = View()

                    async def ack_callback(inter: discord.Interaction):
                        if inter.user.id != self.interaction_user.id:
                            await inter.response.send_message("This is not your session.", ephemeral=True)
                            return
                        await asyncio.to_thread(self.db.end_adventure_session, self.interaction_user.id)
                        await back_to_profile_callback(inter)

                    btn = Button(label="Acknowledge Loss", style=discord.ButtonStyle.danger)
                    btn.callback = ack_callback
                    view.add_item(btn)

                    await interaction.edit_original_response(embed=embed, view=view)
                    return

                # CASE 3: In Progress / Other -> Show Status View
                embed = AdventureEmbeds.build_adventure_status_embed(session)
                view = AdventureStatusView(
                    self.db, adventure_cog.manager, self.interaction_user, session
                )
                await interaction.edit_original_response(embed=embed, view=view)

            except Exception as e:
                logger.error(f"Resume adventure failed: {e}", exc_info=True)
                await interaction.followup.send(
                    "Error resuming session.", ephemeral=True
                )
            return

        # --------------------------------------------------------
        # Start new adventure
        # --------------------------------------------------------
        await interaction.response.defer()

        try:
            # Parallel fetch of guild rank and player level
            guild_member, player_data = await asyncio.gather(
                asyncio.to_thread(
                    self.db.get_guild_member_data, self.interaction_user.id
                ),
                asyncio.to_thread(self.db.get_player, self.interaction_user.id),
            )
            rank = guild_member["rank"] if guild_member else "F"
            level = player_data["level"] if player_data else 1

            embed = discord.Embed(
                title=f"{E.MAP} Prepare for Expedition",
                description=(
                    "*The great gates of the city loom overhead, iron-bound and weathered by countless journeys.*\n\n"
                    "Select a destination and duration to begin."
                ),
                color=discord.Color.dark_green(),
            )

            view = AdventureSetupView(
                self.db, adventure_cog.manager, self.interaction_user, rank, level
            )
            view.back_btn.callback = back_to_profile_callback

            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Start adventure menu failed: {e}", exc_info=True)
            await interaction.followup.send("Error loading destinations.", ephemeral=True)

    # ------------------------------------------------------------

    async def guild_hall_callback(self, interaction: discord.Interaction):
        """Returns the user to the Guild Hall interface."""
        await back_to_guild_hall_callback(interaction)
