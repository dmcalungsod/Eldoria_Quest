"""
Chronicle System UI
-------------------
UI for managing titles and achievements.
"""

import asyncio
import logging

import discord
from discord.ui import Select, View, Button

from database.database_manager import DatabaseManager
import cogs.ui_helpers as ui_helpers

logger = logging.getLogger("eldoria.chronicles.ui")


class TitleSelect(Select):
    def __init__(self, titles, current_active):
        options = []

        # Add "No Title" option
        options.append(
            discord.SelectOption(
                label="No Title",
                value="None",
                description="Remove your current title.",
                default=(current_active is None),
            )
        )

        # Sort titles for consistency
        sorted_titles = sorted(titles)

        for title in sorted_titles:
            options.append(discord.SelectOption(label=title, value=title, default=(title == current_active)))

        # Truncate if too many (Discord limit 25 options)
        if len(options) > 25:
            options = options[:25]

        super().__init__(placeholder="Choose a title...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        selected = self.values[0]
        title_to_set = None if selected == "None" else selected

        db = DatabaseManager()
        success = await asyncio.to_thread(db.set_active_title, interaction.user.id, title_to_set)

        if success:
            await interaction.followup.send(
                f"Title set to: **{selected if selected != 'None' else 'None'}**",
                ephemeral=True,
            )
        else:
            await interaction.followup.send("Failed to set title.", ephemeral=True)


class ChroniclesView(View):
    def __init__(self, db, user, titles, active_title):
        super().__init__(timeout=180)
        self.db = db
        self.user = user

        # Add Title Select if user has titles
        if titles:
            self.add_item(TitleSelect(titles, active_title))

        # Back Button
        self.back_button = Button(label="Back to Profile", style=discord.ButtonStyle.secondary, row=1)
        self.back_button.callback = ui_helpers.back_to_profile_callback
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This view does not belong to you.", ephemeral=True)
            return False
        return True
