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

    def __init__(self, db, manager, interaction_user: discord.User):
        super().__init__()
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    @discord.ui.select(placeholder="Choose a Zone...")
    async def location_callback(self, interaction: discord.Interaction, select: Select):
        """
        Callback for when a location is selected.
        This edits the message to show the main ExplorationView.
        """
        loc_id = select.values[0]
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
        view = ExplorationView(
            self.db, self.manager, loc_id, initial_log, self.interaction_user
        )

        # 3. Edit the original message to show the new UI
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        label="Back to Profile",
        style=discord.ButtonStyle.grey,
        custom_id="back_to_profile",
        row=1,
    )
    async def back_to_profile(self, interaction: discord.Interaction, button: Button):
        await back_to_profile_callback(interaction)


class ExplorationView(View):
    """
    View 2: This is the main exploration UI.
    The player is actively in a zone.
    The embed on this message is the "Exploration Log".
    """

    def __init__(
        self, db, manager, location_id, log: list, interaction_user: discord.User
    ):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log
        self.log_limit = 10  # Max number of lines to show
        self.interaction_user = interaction_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Explore",
        style=discord.ButtonStyle.success,
        custom_id="explore_step",
        emoji="🧭",
    )
    async def explore_callback(self, interaction: discord.Interaction, button: Button):
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

            await interaction.edit_original_response(embed=embed, view=self)

            return_embed = discord.Embed(
                title=f"{E.DEFEAT} Defeated!",
                description="You were recovered by the Guild. Your adventure is over.",
                color=discord.Color.dark_red(),
            )
            await interaction.followup.send(embed=return_embed, ephemeral=True)
            await back_to_profile_callback(interaction)

        else:
            # Just edit the message with the new log
            await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(
        label="Return to City",
        style=discord.ButtonStyle.danger,
        custom_id="explore_leave",
        emoji="🛡️",
    )
    async def leave_callback(self, interaction: discord.Interaction, button: Button):
        """
        The player decides to leave the adventure and return to the Guild Hall.
        """
        # 1. Mark the adventure as inactive and grant rewards
        self.manager.end_adventure(interaction.user.id)

        await interaction.response.defer()

        embed = discord.Embed(
            title="Returned to City",
            description="You safely return to Ashgrave City. Your journey is over... for now.",
            color=discord.Color.blue(),
        )

        # Send ephemeral notification, then edit the main UI
        await interaction.followup.send(embed=embed, ephemeral=True)
        await back_to_profile_callback(interaction)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))
