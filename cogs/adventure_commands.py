"""
adventure_commands.py

This cog initializes the AdventureManager and provides the UI
views for starting and managing active, turn-by-turn exploration.
"""

import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback, build_inventory_embed

# --- View Imports ---
# --- UPDATED: We now need InventoryView from character_cog ---
from .character_cog import InventoryView


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
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user

        self.location_select = Select(
            placeholder="Choose a Zone...", min_values=1, max_values=1, row=0
        )

        try:
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT rank FROM guild_members WHERE discord_id = ?",
                (interaction_user.id,),
            )
            player_rank_row = cur.fetchone()
            player_rank = player_rank_row["rank"] if player_rank_row else "F"
            conn.close()
        except Exception:
            player_rank = "F"

        for loc_id, loc_data in LOCATIONS.items():
            self.location_select.add_option(
                label=loc_data["name"],
                value=loc_id,
                description=f"Lv.{loc_data['level_req']} (Rank {loc_data['min_rank']})",
                emoji=loc_data.get("emoji", E.MAP),
            )

        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

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
        await back_to_profile_callback(interaction, is_new_message=False)


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

        # --- NEW ---
        self.inv_manager = InventoryManager(self.db)

        # --- Add the inventory button ---
        inventory_button = Button(
            label="Inventory",
            style=discord.ButtonStyle.secondary,
            custom_id="explore_inventory",
            emoji=E.BACKPACK,
            row=0,  # Put it next to the Explore button
        )
        inventory_button.callback = self.inventory_callback
        # We need to add it *after* the explore button but *before* the leave button
        # self.children[0] is Explore
        # self.children[1] is Return to City
        # We insert at index 1
        self.insert_item(1, inventory_button)
        # --- END NEW ---

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
        row=0,  # Ensure it's on row 0
    )
    async def explore_callback(self, interaction: discord.Interaction, button: Button):
        """
        The player takes a step forward in the dungeon.
        This is the new "tick" of progression.
        """
        await interaction.response.defer()

        # --- COMBAT LOOP START ---
        # Disable buttons during the action
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

        # This one function does all the backend work
        result = self.manager.simulate_adventure_step(interaction.user.id)

        log_entries = result.get("log", ["An unknown error occurred."])
        is_dead = result.get("dead", False)
        embed = interaction.message.embeds[0]

        # "Play back" the log entries one by one
        for entry in log_entries:
            self.log.append(entry)
            if len(self.log) > self.log_limit:
                self.log = self.log[-self.log_limit :]

            new_description = "\n".join(self.log)
            embed.description = new_description
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.5)

        # --- COMBAT LOOP END ---

        if is_dead:
            embed.color = discord.Color.red()
            embed.set_footer(text="You have been defeated! Your adventure is over.")

            # All buttons are already disabled
            await interaction.edit_original_response(embed=embed, view=self)

            return_embed = discord.Embed(
                title=f"{E.DEFEAT} Defeated!",
                description="You were recovered by the Guild. Your adventure is over.",
                color=discord.Color.dark_red(),
            )
            await interaction.followup.send(embed=return_embed, ephemeral=True)

        else:
            # Re-enable buttons
            for item in self.children:
                item.disabled = False
            await interaction.edit_original_response(embed=embed, view=self)

    # --- NEW CALLBACK ---
    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Opens the inventory UI from the exploration view.
        """
        await interaction.response.defer()
        items = self.inv_manager.get_inventory(interaction.user.id)

        embed = build_inventory_embed(items)

        # Pass the 'back_to_exploration' callback
        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=self.back_to_exploration_callback,
            previous_view_label="Back to Adventure",
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_exploration_callback(self, interaction: discord.Interaction):
        """
        A custom callback function that returns to *this* exploration view.
        """
        await interaction.response.defer()

        # Re-build the embed
        embed = discord.Embed(
            title=f"{LOCATIONS[self.location_id].get('emoji', E.MAP)} Exploring: {LOCATIONS[self.location_id]['name']}",
            description="\n".join(self.log),
            color=discord.Color.green(),
        )

        # Re-create the view to ensure buttons are enabled
        new_view = ExplorationView(
            self.db, self.manager, self.location_id, self.log, self.interaction_user
        )

        await interaction.edit_original_response(embed=embed, view=new_view)

    @discord.ui.button(
        label="Return to City",
        style=discord.ButtonStyle.danger,
        custom_id="explore_leave",
        row=1,  # Move to row 1 to make space for inventory
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
        await back_to_profile_callback(interaction, is_new_message=False)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))
