"""
game_systems/adventure/ui/status_view.py

Displays the current status of an ongoing adventure.
Hardened: Async handling and robust error recovery.
"""

import asyncio
import logging

import discord
from discord.ui import Button, View

from cogs.utils.ui_helpers import back_to_profile_callback
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds

logger = logging.getLogger("eldoria.ui.status_view")


class AdventureStatusView(View):
    def __init__(self, db, manager, user, session_data):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.user = user
        self.session_data = session_data

        # Refresh Button
        self.refresh_btn = Button(
            label="Refresh Status",
            style=discord.ButtonStyle.primary,
            emoji="🔄",
            row=0,
        )
        self.refresh_btn.callback = self.refresh_callback
        self.add_item(self.refresh_btn)

        # Retreat Button
        self.retreat_btn = Button(
            label="Retreat Early",
            style=discord.ButtonStyle.danger,
            emoji="🏳️",
            row=0,
        )
        self.retreat_btn.callback = self.retreat_callback
        self.add_item(self.retreat_btn)

        # Back to Profile
        self.back_btn = Button(
            label="Return to Profile",
            style=discord.ButtonStyle.grey,
            row=1,
        )
        self.back_btn.callback = back_to_profile_callback
        self.add_item(self.back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def refresh_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fetch latest session data
        session = await asyncio.to_thread(self.manager.get_active_session, self.user.id)

        if not session:
            await interaction.followup.send("Adventure session not found or already ended.", ephemeral=True)
            # Disable buttons since session is gone
            for item in self.children:
                if item != self.back_btn:
                    item.disabled = True
            await interaction.edit_original_response(view=self)
            return

        self.session_data = session

        try:
            embed = AdventureEmbeds.build_adventure_status_embed(session)
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Failed to refresh status embed: {e}", exc_info=True)
            await interaction.followup.send("Error refreshing status.", ephemeral=True)

    async def retreat_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # End adventure
        summary = await asyncio.to_thread(self.manager.end_adventure, self.user.id)

        if not summary:
            await interaction.followup.send("Failed to retrieve adventure results.", ephemeral=True)
            return

        # Build summary embed
        loc_id = self.session_data.get("location_id")
        embed = AdventureEmbeds.build_summary_embed(summary, loc_id)

        # Update message, remove view (replace with simple back button)
        self.clear_items()

        back_btn = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

        await interaction.edit_original_response(embed=embed, view=self)
