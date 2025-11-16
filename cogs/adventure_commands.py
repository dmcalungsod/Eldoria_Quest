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
# (Import moved into callbacks to prevent circular import)


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

    # --- MODIFIED __init__ ---
    def __init__(self, db, manager, interaction_user: discord.User, player_rank: str):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user
        # --- END MODIFICATION ---

        self.location_select = Select(
            placeholder="Choose a Zone...", min_values=1, max_values=1, row=0
        )

        # --- REMOVED DB CALL, WE NOW USE THE PASSED-IN player_rank ---
        for loc_id, loc_data in LOCATIONS.items():
            # This logic to check rank is not yet implemented, but the var is ready
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

        # --- ASYNC FIX ---
        # Run the DB write in a thread
        await asyncio.to_thread(
            self.manager.start_adventure,
            interaction.user.id,
            loc_id,
            duration_minutes=-1
        )
        # --- END FIX ---

        # 2. Create the new Exploration View
        initial_log = [
            f"You step past the threshold into the {loc_data['name']}. The air feels different."
        ]

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}",
            description="\n".join(initial_log),
            color=discord.Color.green(),
        )

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
        # This function is already async!
        await back_to_profile_callback(interaction, is_new_message=False)


class ExplorationView(View):
    """
    View 2: This is the main exploration UI.
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
        self.inv_manager = InventoryManager(self.db)

        # ... (button definitions are unchanged) ...
        self.explore_button = Button(...)
        self.inventory_button = Button(...)
        self.leave_button = Button(...)
        
        self.explore_button.callback = self.explore_callback
        self.add_item(self.explore_button)
        self.inventory_button.callback = self.inventory_callback
        self.add_item(self.inventory_button)
        self.leave_button.callback = self.leave_callback
        self.add_item(self.leave_button)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The player takes a step forward in the dungeon.
        """
        await interaction.response.defer()

        self.explore_button.disabled = True
        self.inventory_button.disabled = True
        self.leave_button.disabled = True
        await interaction.edit_original_response(view=self)

        # --- ASYNC FIX ---
        # This is the most important one!
        # simulate_adventure_step runs the *entire* combat loop
        result = await asyncio.to_thread(
            self.manager.simulate_adventure_step, interaction.user.id
        )
        # --- END FIX ---

        log_entries = result.get("log", ["An unknown error occurred."])
        is_dead = result.get("dead", False)
        embed = interaction.message.embeds[0]

        for entry in log_entries:
            self.log.append(entry)
            if len(self.log) > self.log_limit:
                self.log = self.log[-self.log_limit :]

            new_description = "\n".join(self.log)
            embed.description = new_description
            await interaction.edit_original_response(embed=embed)

            await asyncio.sleep(1.5) # This is already non-blocking, so it's fine

        if is_dead:
            embed.color = discord.Color.red()
            embed.set_footer(text="You have been defeated! Your adventure is over.")

            await interaction.edit_original_response(embed=embed, view=self)

            return_embed = discord.Embed(
                title=f"{E.DEFEAT} Defeated!",
                description="You were recovered by the Guild. Your adventure is over.",
                color=discord.Color.dark_red(),
            )
            await interaction.followup.send(embed=return_embed, ephemeral=True)

        else:
            self.explore_button.disabled = False
            self.inventory_button.disabled = False
            self.leave_button.disabled = False
            await interaction.edit_original_response(embed=embed, view=self)

    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Opens the inventory UI from the exploration view.
        """
        from .character_cog import InventoryView

        await interaction.response.defer()
        
        # --- ASYNC FIX ---
        items = await asyncio.to_thread(
            self.inv_manager.get_inventory, interaction.user.id
        )
        embed = await asyncio.to_thread(build_inventory_embed, items)
        # --- END FIX ---

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

        embed = discord.Embed(
            title=f"{LOCATIONS[self.location_id].get('emoji', E.MAP)} Exploring: {LOCATIONS[self.location_id]['name']}",
            description="\n".join(self.log),
            color=discord.Color.green(),
        )

        new_view = ExplorationView(
            self.db, self.manager, self.location_id, self.log, self.interaction_user
        )

        await interaction.edit_original_response(embed=embed, view=new_view)

    async def leave_callback(self, interaction: discord.Interaction):
        """
        The player decides to leave the adventure and return to the Guild Hall.
        """
        await interaction.response.defer() # Defer *before* the blocking call

        # --- ASYNC FIX ---
        # end_adventure is a heavy blocking call
        await asyncio.to_thread(self.manager.end_adventure, interaction.user.id)
        # --- END FIX ---

        embed = discord.Embed(
            title="Returned to City",
            description="You safely return to Ashgrave City. Your journey is over... for now.",
            color=discord.Color.blue(),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # This callback is now fully async, so we can await it
        await back_to_profile_callback(interaction, is_new_message=False)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))