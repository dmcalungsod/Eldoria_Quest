"""
game_systems/character/ui/adventure_menu.py

Primary entry menu for the Adventure System.
Hardened: Safe JSON parsing for session resumption.
"""

import asyncio
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E

# Modular imports
from cogs.utils.ui_helpers import back_to_guild_hall_callback, back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.adventure.ui.setup_view import AdventureSetupView
from game_systems.adventure.ui.status_view import AdventureStatusView
from game_systems.data.consumables import CONSUMABLES

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

        # Tutorial Button
        btn_tutorial = Button(
            label="How Expeditions Work",
            style=discord.ButtonStyle.secondary,
            custom_id="tutorial_adv",
            emoji="❓",
            row=2,
        )
        btn_tutorial.callback = self.tutorial_callback
        self.add_item(btn_tutorial)

    # ------------------------------------------------------------

    async def tutorial_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🧭 Expedition Guide",
            description=(
                "**Time-Based Exploration**\n"
                "Expeditions in Eldoria are unforgiving. You select a destination and duration, then wait while your character explores the wilds automatically.\n\n"
                "**Supplies**\n"
                "Pack Hardtack to reduce fatigue over long journeys, and Pitch Torches to avoid deadly night ambushes.\n\n"
                "**Hazards & Retreat**\n"
                "If your HP drops below 30%, you will automatically retreat, though you may lose gathered loot. "
                "You can also check your status and retreat manually at any time to secure your findings."
            ),
            color=discord.Color.blue()
        )
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

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
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(
                content=f"{E.ERROR} The adventure system is currently unavailable.",
                ephemeral=True,
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

            status = session.get("status", "in_progress")

            try:
                # CASE 1: Completed -> Show Rewards
                if status == "completed":
                    summary = await asyncio.to_thread(adventure_cog.manager.end_adventure, self.interaction_user.id)
                    if not summary:
                        await interaction.followup.send("Error processing rewards.", ephemeral=True)
                        return

                    loc_id = session.get("location_id")
                    embed = AdventureEmbeds.build_summary_embed(summary, loc_id)

                    # Create a simple view with just "Back"
                    view = View()
                    back_btn = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
                    back_btn.callback = back_to_profile_callback
                    view.add_item(back_btn)

                    await interaction.edit_original_response(embed=embed, view=view)
                    return

                # CASE 2: Active / In Progress / Failed
                # Show Status View
                embed = AdventureEmbeds.build_adventure_status_embed(session)
                view = AdventureStatusView(self.db, adventure_cog.manager, self.interaction_user, session)
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
            # Parallel fetch of guild rank, player level, and inventory data
            guild_member, player_data, inventory_items, max_slots, current_slots = await asyncio.gather(
                asyncio.to_thread(self.db.get_guild_member_data, self.interaction_user.id),
                asyncio.to_thread(self.db.get_player, self.interaction_user.id),
                asyncio.to_thread(self.db.get_inventory_items, self.interaction_user.id, equipped=0),
                asyncio.to_thread(self.db.calculate_inventory_limit, self.interaction_user.id),
                asyncio.to_thread(self.db.get_inventory_slot_count, self.interaction_user.id),
            )
            rank = guild_member["rank"] if guild_member else "F"
            level = player_data["level"] if player_data else 1

            # Filter valid supplies (supply, hp, mp, buff, etc.)
            valid_types = {"supply", "hp", "mp", "buff", "antidote", "food", "throwable"}
            supplies = []
            for item in inventory_items:
                c_data = CONSUMABLES.get(item["item_key"])
                # Fallback to item_type from DB if not in CONSUMABLES (legacy safety)
                i_type = c_data["type"] if c_data else item.get("item_type")
                if i_type in valid_types:
                    supplies.append(item)

            # Capacity Check Flavor
            capacity_str = f"🎒 **Pack:** {current_slots}/{max_slots}"
            if current_slots >= max_slots:
                capacity_str += " (FULL! You cannot carry loot.)"
            elif current_slots >= max_slots - 2:
                capacity_str += " (Heavy)"

            embed = discord.Embed(
                title=f"{E.MAP} Prepare for Expedition",
                description=(
                    f"*The great gates of the city loom overhead.*\n\n{capacity_str}\n"
                    "Select a destination and duration to begin."
                ),
                color=discord.Color.dark_green(),
            )

            view = AdventureSetupView(
                self.db,
                adventure_cog.manager,
                self.interaction_user,
                rank,
                level,
                supplies=supplies,
                capacity=(current_slots, max_slots),
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
