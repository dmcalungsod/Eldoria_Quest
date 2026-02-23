"""
game_systems/adventure/ui/status_view.py

View for monitoring active background adventures.
Allows refreshing status or retreating early.
"""

import datetime
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.world_time import WorldTime

logger = logging.getLogger("eldoria.ui.status")


class AdventureStatusView(View):
    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        interaction_user: discord.User,
        session_id: str = None # Optional, mainly for verification if needed
    ):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user

        # Refresh Button
        self.btn_refresh = Button(
            label="Refresh Status",
            style=discord.ButtonStyle.primary,
            custom_id="adv_refresh",
            emoji="🔄",
            row=0
        )
        self.btn_refresh.callback = self.refresh_callback
        self.add_item(self.btn_refresh)

        # Retreat Button
        self.btn_retreat = Button(
            label="Retreat (End Early)",
            style=discord.ButtonStyle.danger,
            custom_id="adv_retreat",
            emoji="🏳️",
            row=0
        )
        self.btn_retreat.callback = self.retreat_callback
        self.add_item(self.btn_retreat)

        # Back Button
        self.btn_back = Button(
            label="Return to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="adv_back",
            row=1
        )
        self.btn_back.callback = back_to_profile_callback
        self.add_item(self.btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your expedition.", ephemeral=True)
            return False
        return True

    async def refresh_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        session = self.db.get_active_adventure(self.interaction_user.id)
        if not session or session.get("status") != "in_progress":
            await interaction.followup.send("Expedition has ended or is no longer active.", ephemeral=True)
            # Disable buttons?
            return

        # Calculate time remaining
        try:
            end_time = datetime.datetime.fromisoformat(session["end_time"])
            now = WorldTime.now()
            remaining = end_time - now

            if remaining.total_seconds() <= 0:
                time_str = "Complete!"
            else:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}h {minutes}m"
        except Exception:
            time_str = "Unknown"

        loc_data = LOCATIONS.get(session["location_id"], {})
        steps = session.get("steps_completed", 0)

        embed = AdventureEmbeds.build_status_embed(session, loc_data, time_str, steps)
        await interaction.edit_original_response(embed=embed, view=self)

    async def retreat_callback(self, interaction: discord.Interaction):
        # Confirm retreat? For now, direct action as per ONE UI (fast interaction)
        await interaction.response.defer()

        session = self.db.get_active_adventure(self.interaction_user.id)
        if not session:
            await interaction.followup.send("No active expedition found.", ephemeral=True)
            return

        # Attempt to end adventure
        summary = self.manager.end_adventure(self.interaction_user.id)

        if summary:
            embed = AdventureEmbeds.build_summary_embed(summary, session["location_id"])
            # Remove view or provide back button
            # We can reuse self, but remove retreat/refresh
            self.clear_items()

            btn_back = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
            btn_back.callback = back_to_profile_callback
            self.add_item(btn_back)

            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.followup.send("Failed to retreat. Try again.", ephemeral=True)
