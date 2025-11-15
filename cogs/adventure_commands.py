"""
adventure_commands.py

This cog initializes the AdventureManager and provides the UI
views for starting and managing active, turn-by-turn exploration.
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
import json

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback


class AdventureCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)
        self.inventory_manager = InventoryManager(self.db)

    # --- NO COMMANDS ---


class AdventureSetupView(View):
    """
    View 1: The player selects their destination.
    This view is shown when "Start Adventure" is clicked on the profile.
    """

    def __init__(self, db, manager):
        super().__init__()
        self.db = db
        self.manager = manager

        self.location_select = Select(placeholder="Choose a Zone...")
        for key, loc in LOCATIONS.items():
            self.location_select.add_option(
                label=loc["name"],
                value=key,
                description=f"Lv. {loc['level_req']} | {loc['min_rank']}-Rank",
                emoji=loc.get("emoji"),
            )
        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

        # Add a back button to return to profile
        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)

    async def location_callback(self, interaction: discord.Interaction):
        """
        Callback for when a location is selected.
        This edits the message to show the main ExplorationView.
        """
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS[loc_id]

        # 1. Start the "session" in the database (duration -1 = active)
        self.manager.start_adventure(interaction.user.id, loc_id, duration_minutes=-1)

        # 2. Create the new Exploration View
        initial_log = [
            f"You step past the threshold into the {loc_data['name']}. The air feels different."
        ]

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}",
            description="\n".join(initial_log),
            color=discord.Color.green(),
        )

        adventure_cog = self.manager.bot.get_cog("AdventureCommands")
        view = ExplorationView(self.db, self.manager, loc_id, initial_log)

        # 3. Edit the original message to show the new UI
        await interaction.response.edit_message(embed=embed, view=view)


class ExplorationView(View):
    """
    View 2: This is the main exploration UI.
    The player is actively in a zone.
    The embed on this message is the "Exploration Log".
    """

    def __init__(self, db, manager, location_id, log: list):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log
        self.log_limit = 10  # Max number of lines to show

        # --- The New Buttons ---
        explore_button = Button(
            label="Explore",
            style=discord.ButtonStyle.success,
            custom_id="explore_step",
            emoji="🧭",
        )
        explore_button.callback = self.explore_callback
        self.add_item(explore_button)

        leave_button = Button(
            label="Return to City",
            style=discord.ButtonStyle.danger,
            custom_id="explore_leave",
            emoji="🛡️",
        )
        leave_button.callback = self.leave_callback
        self.add_item(leave_button)

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The player takes a step forward in the dungeon.
        This is the new "tick" of progression.
        """
        await interaction.response.defer()

        # This one function does all the backend work
        result = self.manager.simulate_adventure_step(interaction.user.id)

        log_entries = result.get("log", ["An unknown error occurred."])
        is_dead = result.get("dead", False)

        # Append new log entries
        self.log.extend(log_entries)

        # Trim the log if it's too long
        if len(self.log) > self.log_limit:
            self.log = self.log[-self.log_limit :]

        # Update the embed description with the new log
        new_description = "\n".join(self.log)

        # Get the original embed and update it
        embed = interaction.message.embeds[0]
        embed.description = new_description

        if is_dead:
            embed.color = discord.Color.red()
            embed.set_footer(text="You have been defeated! Your adventure is over.")

            # Disable all buttons on death
            for item in self.children:
                item.disabled = True

            # Edit the message to show death and disable buttons
            await interaction.edit_original_response(embed=embed, view=self)

            # Send a followup and then go home
            return_embed = discord.Embed(
                title="Returned to Guild",
                description="You were defeated and recovered by the Guild. Your adventure is over.",
                color=discord.Color.dark_red(),
            )
            # Use the helper to go back to the profile
            await back_to_profile_callback(interaction, embed_to_show=return_embed)

        else:
            # Just edit the message with the new log
            await interaction.edit_original_response(embed=embed, view=self)

    async def leave_callback(self, interaction: discord.Interaction):
        """
        The player decides to leave the adventure and return to the Guild Hall.
        """
        # 1. Mark the adventure as inactive and grant rewards
        self.manager.end_adventure(interaction.user.id)

        # 2. Go back to the main Profile
        await interaction.response.defer()

        embed = discord.Embed(
            title="Returned to City",
            description="You safely return to Ashgrave City. Your journey is over... for now.",
            color=discord.Color.blue(),
        )

        await back_to_profile_callback(interaction, embed_to_show=embed)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))
