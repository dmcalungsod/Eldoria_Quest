"""
game_systems/adventure/ui/setup_view.py

The preparation screen where players select their destination and duration.
Hardened: Async initialization and safe session creation.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from cogs.utils.ui_helpers import back_to_profile_callback, get_player_or_error
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS

from .adventure_embeds import AdventureEmbeds
from .status_view import AdventureStatusView

logger = logging.getLogger("eldoria.ui.setup")

RANK_ORDER = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"]


class AdventureSetupView(View):
    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        interaction_user: discord.User,
        player_rank: str,
        player_level: int,
    ):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user
        self.player_rank = player_rank
        self.player_level = player_level

        self.selected_location = None
        self.selected_duration = None

        # 1. Location Select
        self.location_select = Select(
            placeholder="Select Destination...",
            min_values=1,
            max_values=1,
            row=0,
        )
        # Populate Locations
        for loc_id, loc_data in LOCATIONS.items():
            is_unlocked = self._is_unlocked(loc_data)

            if is_unlocked:
                label = loc_data["name"]
                desc = f"Lv.{loc_data['level_req']} (Rank {loc_data['min_rank']})"
                emoji = loc_data.get("emoji", E.MAP)
            else:
                label = f"{E.LOCKED} {loc_data['name']}"
                desc = f"[LOCKED] Req: Lv.{loc_data['level_req']}, Rank {loc_data['min_rank']}"
                emoji = E.LOCKED

            self.location_select.add_option(
                label=label,
                value=loc_id,
                description=desc,
                emoji=emoji,
            )

        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

        # 2. Duration Select
        self.duration_select = Select(
            placeholder="Select Duration...",
            min_values=1,
            max_values=1,
            row=1,
            options=[
                discord.SelectOption(label="30 Minutes", value="30", description="Short patrol", emoji="⏲️"),
                discord.SelectOption(label="1 Hour", value="60", description="Standard expedition", emoji="⏲️"),
                discord.SelectOption(label="4 Hours", value="240", description="Extended journey", emoji="⛺"),
                discord.SelectOption(label="8 Hours", value="480", description="Full day trek", emoji="🌙"),
            ],
        )
        self.duration_select.callback = self.duration_callback
        self.add_item(self.duration_select)

        # 3. Start Button
        self.start_btn = Button(
            label="Begin Expedition",
            style=discord.ButtonStyle.success,
            row=2,
            disabled=True,
            emoji="⚔️",
        )
        self.start_btn.callback = self.start_callback
        self.add_item(self.start_btn)

        # 4. Back Button
        self.back_btn = Button(label="Return to Ledger", style=discord.ButtonStyle.grey, row=2)
        self.back_btn.callback = self.back_callback
        self.add_item(self.back_btn)

    def _is_unlocked(self, loc_data: dict) -> bool:
        """Checks if the player meets rank and level requirements."""
        req_rank = loc_data["min_rank"]
        req_level = loc_data["level_req"]

        # Level Check
        if self.player_level < req_level:
            return False

        # Rank Check
        try:
            player_rank_idx = RANK_ORDER.index(self.player_rank)
            req_rank_idx = RANK_ORDER.index(req_rank)
            if player_rank_idx < req_rank_idx:
                return False
        except ValueError:
            # Fallback if rank is unknown (shouldn't happen)
            logger.warning(f"Unknown rank encountered: {self.player_rank} or {req_rank}")
            return False

        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def back_callback(self, interaction: discord.Interaction):
        await back_to_profile_callback(interaction, is_new_message=False)

    def _update_start_button(self):
        if self.selected_location and self.selected_duration:
            self.start_btn.disabled = False
        else:
            self.start_btn.disabled = True

    async def location_callback(self, interaction: discord.Interaction):
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone"})

        if not self._is_unlocked(loc_data):
            await interaction.response.send_message(
                f"{E.LOCKED} **Access Denied**\nYou need **Level {loc_data['level_req']}** and **Rank {loc_data['min_rank']}** to enter {loc_data['name']}.",
                ephemeral=True,
            )
            return

        self.selected_location = loc_id
        self._update_start_button()

        await interaction.response.edit_message(view=self)

    async def duration_callback(self, interaction: discord.Interaction):
        self.selected_duration = int(self.duration_select.values[0])
        self._update_start_button()
        await interaction.response.edit_message(view=self)

    async def start_callback(self, interaction: discord.Interaction):
        # Validate player before starting adventure
        if not await get_player_or_error(interaction, self.db):
            return

        await interaction.response.defer()

        try:
            # 1. Start the adventure in DB (Threaded)
            success = await asyncio.to_thread(
                self.manager.start_adventure,
                interaction.user.id,
                self.selected_location,
                self.selected_duration,
            )

            if not success:
                await interaction.followup.send("Failed to start adventure. Please try again.", ephemeral=True)
                return

            # 2. Get new session data
            session = await asyncio.to_thread(self.manager.get_active_session, interaction.user.id)
            if not session:
                await interaction.followup.send("Error starting session.", ephemeral=True)
                return

            # 3. Build Status Embed
            embed = AdventureEmbeds.build_adventure_status_embed(session)

            # 4. Switch View
            view = AdventureStatusView(self.db, self.manager, self.interaction_user, session)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Adventure start error: {e}", exc_info=True)
            await interaction.followup.send("An error occurred starting the expedition.", ephemeral=True)
