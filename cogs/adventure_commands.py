"""
adventure_commands.py

This cog NO LONGER contains user-facing slash commands.
Its primary purpose is to initialize and run the
background AdventureManager loop.
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
import game_systems.data.emojis as E


class AdventureCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)  # Starts the loop

    # --- NO COMMANDS ---
    # The /adventure command has been removed.
    # All adventure UI is now launched from the "View Profile"
    # button in the GuildHubCog.


class AdventureSetupView(View):
    def __init__(self, db, manager):
        super().__init__()
        self.db = db
        self.manager = manager

        # Location Select
        self.location_select = Select(placeholder="Choose a Zone...")
        for key, loc in LOCATIONS.items():
            # Use the emoji from the location data file
            self.location_select.add_option(
                label=loc["name"],
                value=key,
                description=f"Lv. {loc['level_req']} | {loc['min_rank']}-Rank",
                emoji=loc.get("emoji"),  # Use .get() for safety
            )
        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

    async def location_callback(self, interaction: discord.Interaction):
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS[loc_id]

        # Create Duration Buttons
        self.clear_items()

        for mins in loc_data["duration_options"]:
            btn = Button(
                label=f"{mins} Mins",
                style=discord.ButtonStyle.primary,
                custom_id=f"dur_{loc_id}_{mins}",
            )
            btn.callback = self.duration_callback
            self.add_item(btn)

        await interaction.response.edit_message(
            content=f"{loc_data.get('emoji', E.MAP)} **Destination:** {loc_data['name']}\nSelect Duration:",
            view=self,
        )

    async def duration_callback(self, interaction: discord.Interaction):
        # custom_id format: dur_locationID_minutes
        parts = interaction.data["custom_id"].split("_")
        loc_id = "_".join(parts[1:-1])  # handle IDs with underscores
        duration = int(parts[-1])

        self.manager.start_adventure(interaction.user.id, loc_id, duration)

        # Updated to an embed
        embed = discord.Embed(
            title=f"{E.MAP} Adventure Started!",
            description=(
                f"You have set off for **{LOCATIONS[loc_id]['name']}** for {duration} minutes.\n\n"
                f"The Guild will receive intermittent reports on your progress. "
                f"You can check your status from your profile."
            ),
            color=discord.Color.green(),
        )

        await interaction.response.edit_message(content=None, embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))
