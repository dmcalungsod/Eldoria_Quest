"""
experiment_view.py

UI for the Alchemy Experimentation System.
Allows players to select materials and mix them.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

from database.database_manager import DatabaseManager
from game_systems.crafting.crafting_system import CraftingSystem

logger = logging.getLogger("eldoria.ui.experiment")


class ExperimentView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User, back_callback=None):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.crafting_system = CraftingSystem(self.db)
        self.back_callback = back_callback
        self.selected_materials = []  # List of inv_ids
        self.mix_btn = None

        self._setup_ui()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This workbench is occupied.", ephemeral=True)
            return False
        return True

    def _setup_ui(self):
        # 1. Material Select Menu
        # Fetch materials (limit to 25, sort by count)
        materials = self.db.get_inventory_items(self.interaction_user.id, item_type="material", equipped=0)

        # Sort by count desc
        materials.sort(key=lambda x: x["count"], reverse=True)

        if not materials:
            select = Select(placeholder="No materials available.", disabled=True, row=0)
            select.add_option(label="Empty", value="empty")
            self.add_item(select)
        else:
            # Determine max_values
            # If user has fewer than 2 items, they can't even select 2.
            # But the requirement is "Select 2-3".
            # If len < 2, disable?
            if len(materials) < 2:
                select = Select(placeholder="Not enough unique materials (need 2+).", disabled=True, row=0)
                select.add_option(label="Empty", value="empty")
                self.add_item(select)
            else:
                max_val = min(3, len(materials))
                select = Select(
                    placeholder="Select 2-3 materials to mix...", min_values=2, max_values=max_val, row=0
                )

                for item in materials[:25]:
                    label = f"{item['item_name']} (x{item['count']})"
                    # Value must be string
                    select.add_option(label=label, value=str(item["id"]), description=item.get("rarity", "Common"))

                select.callback = self.material_select_callback
                self.add_item(select)

        # 2. Mix Button
        self.mix_btn = Button(
            label="Mix Ingredients", style=discord.ButtonStyle.success, disabled=True, row=1, emoji="⚗️"
        )
        self.mix_btn.callback = self.mix_callback
        self.add_item(self.mix_btn)

        # 3. Back Button
        if self.back_callback:
            back_btn = Button(label="Back", style=discord.ButtonStyle.secondary, row=1)
            back_btn.callback = self.back_callback
            self.add_item(back_btn)

    async def material_select_callback(self, interaction: discord.Interaction):
        # Update selected materials
        self.selected_materials = [int(v) for v in interaction.data["values"]]

        # Enable Mix Button
        self.mix_btn.disabled = False

        # Update View
        await interaction.response.edit_message(view=self)

    async def mix_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.selected_materials:
            await interaction.followup.send("No materials selected.", ephemeral=True)
            return

        # Execute Experiment
        success, msg, result_item = await asyncio.to_thread(
            self.crafting_system.experiment, self.interaction_user.id, self.selected_materials
        )

        # Show Result
        embed = self.build_result_embed(success, msg, result_item)

        # Refresh View (Inventory changed, so we need to rebuild Select)
        new_view = ExperimentView(self.db, self.interaction_user, self.back_callback)

        await interaction.edit_original_response(embed=embed, view=new_view)

    def build_embed(self):
        embed = discord.Embed(
            title="🧪 Alchemy Experimentation",
            description="Select raw materials to discover new recipes.\n**Warning:** Failed experiments result in lost materials!",
            color=discord.Color.blue(),
        )
        return embed

    def build_result_embed(self, success, msg, result_item):
        color = discord.Color.green() if success else discord.Color.dark_gray()
        title = "Experiment Result"

        embed = discord.Embed(title=title, description=msg, color=color)
        if success and result_item:
            # Add item details
            embed.add_field(name="Item Created", value=result_item["name"], inline=False)
            if result_item.get("effect"):
                # Format effect nicely
                effects = []
                for k, v in result_item["effect"].items():
                    effects.append(f"{k}: {v}")
                embed.add_field(name="Effects", value=", ".join(effects), inline=False)

        return embed
