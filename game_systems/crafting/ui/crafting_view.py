"""
crafting_view.py

The Alchemist's Workbench UI.
Allows players to view recipes and craft items.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.crafting.crafting_system import CraftingSystem

logger = logging.getLogger("eldoria.ui.crafting")


class CraftingView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User, status_msg: str = None):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.crafting_system = CraftingSystem(self.db)
        self.status_msg = status_msg
        self.last_success = True

        # Back Button placeholder
        self.back_button = Button(
            label="Back", style=discord.ButtonStyle.secondary, custom_id="back_crafting", row=2
        )

        self._setup_ui()

    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This workbench is occupied.", ephemeral=True)
            return False
        return True

    def _setup_ui(self):
        # Recipe Dropdown
        recipes = self.crafting_system.get_recipes(self.interaction_user.id)

        select = Select(placeholder="Select a recipe to brew...", min_values=1, max_values=1, row=0)

        for r_id, r_data in recipes.items():
            # Calculate if craftable
            # Optimization: could cache inventory counts, but DB call is fast enough
            can_craft, _ = self.crafting_system.can_craft(self.interaction_user.id, r_id)
            emoji = E.POTION if can_craft else E.LOCKED

            label = f"{r_data['name']} ({r_data['cost']} G)"
            desc = r_data['description'][:100]

            select.add_option(label=label, value=r_id, description=desc, emoji=emoji)

        select.callback = self.recipe_select_callback
        self.add_item(select)

    async def recipe_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        recipe_id = interaction.data["values"][0]

        # Execute Craft
        success, msg, item_data = await asyncio.to_thread(
            self.crafting_system.craft_item, self.interaction_user.id, recipe_id
        )

        # Refresh View
        new_view = CraftingView(self.db, self.interaction_user, status_msg=msg)
        new_view.last_success = success
        # Re-attach back button
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        embed = new_view.build_embed()
        await interaction.edit_original_response(embed=embed, view=new_view)

    def build_embed(self):
        color = discord.Color.purple()
        if self.status_msg and not self.last_success:
            color = discord.Color.red()
        elif self.status_msg and self.last_success:
            color = discord.Color.green()

        embed = discord.Embed(
            title="⚗️ Alchemist's Workbench",
            description="Bubbling cauldrons and drying herbs fill the air with strange scents.\n"
            "Select a recipe to combine your materials into powerful concoctions.",
            color=color,
        )

        # Show Status
        if self.status_msg:
            icon = E.CHECK if self.last_success else E.ERROR
            embed.add_field(name="Result", value=f"{icon} {self.status_msg}", inline=False)

        # Show Player Gold
        player = self.db.get_player(self.interaction_user.id)
        if player:
            embed.set_footer(text=f"Purse: {player.get('aurum', 0)} Aurum")

        return embed
