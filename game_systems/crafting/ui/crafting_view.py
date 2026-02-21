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
    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        status_msg: str = None,
        category: str = "consumable",
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.crafting_system = CraftingSystem(self.db)
        self.status_msg = status_msg
        self.last_success = True
        self.category = category  # "consumable", "equipment", or "dismantle"

        # Back Button placeholder (re-attached via set_back_button)
        self.back_button = Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back_crafting", row=2)

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
        # Row 0: Category Buttons
        btn_cons = Button(
            label="Consumables",
            style=discord.ButtonStyle.primary if self.category == "consumable" else discord.ButtonStyle.secondary,
            custom_id="cat_consumable",
            row=0,
        )
        btn_equip = Button(
            label="Equipment",
            style=discord.ButtonStyle.primary if self.category == "equipment" else discord.ButtonStyle.secondary,
            custom_id="cat_equipment",
            row=0,
        )
        btn_dismantle = Button(
            label="Dismantle",
            style=discord.ButtonStyle.danger if self.category == "dismantle" else discord.ButtonStyle.secondary,
            custom_id="cat_dismantle",
            row=0,
        )

        btn_cons.callback = self.category_cons_callback
        btn_equip.callback = self.category_equip_callback
        btn_dismantle.callback = self.category_dismantle_callback

        self.add_item(btn_cons)
        self.add_item(btn_equip)
        self.add_item(btn_dismantle)

        # Row 1: Select Menu
        if self.category == "dismantle":
            self._setup_dismantle_select()
        else:
            self._setup_recipe_select()

    def _setup_dismantle_select(self):
        # Fetch unequipped equipment
        items = self.db.get_inventory_items(self.interaction_user.id, item_type="equipment", equipped=0)

        if not items:
            select = Select(
                placeholder="No equipment to dismantle.",
                min_values=1,
                max_values=1,
                row=1,
                disabled=True,
            )
            select.add_option(label="Empty", value="empty")
            self.add_item(select)
            return

        select = Select(placeholder="Select item to dismantle...", min_values=1, max_values=1, row=1)

        # Sort by rarity or name? Rarity then Name.
        # Rarity order helper?
        rarity_rank = {"Common": 1, "Uncommon": 2, "Rare": 3, "Epic": 4, "Legendary": 5, "Mythical": 6}
        items.sort(key=lambda x: (rarity_rank.get(x.get("rarity", "Common"), 0), x.get("item_name", "")))

        for item in items[:25]:
            inv_id = str(item["id"])
            label = f"{item['item_name']} ({item['rarity']})"
            desc = "Dismantle for materials..."
            emoji = E.HAMMER if hasattr(E, "HAMMER") else "🔨"

            select.add_option(label=label, value=inv_id, description=desc, emoji=emoji)

        select.callback = self.dismantle_select_callback
        self.add_item(select)

    def _setup_recipe_select(self):
        # Row 1: Recipe Dropdown
        all_recipes = self.crafting_system.get_recipes(self.interaction_user.id)
        filtered_recipes = {}

        for r_id, r_data in all_recipes.items():
            rtype = r_data.get("type", "consumable")
            # Normalize type check
            if self.category == "consumable" and rtype != "equipment":
                filtered_recipes[r_id] = r_data
            elif self.category == "equipment" and rtype == "equipment":
                filtered_recipes[r_id] = r_data

        if not filtered_recipes:
            select = Select(
                placeholder=f"No {self.category} recipes available.",
                min_values=1,
                max_values=1,
                row=1,
                disabled=True,
            )
            select.add_option(label="Empty", value="empty")
            self.add_item(select)
            return

        select = Select(placeholder=f"Select {self.category} to craft...", min_values=1, max_values=1, row=1)

        # Sort recipes by cost for better UX
        sorted_recipes = sorted(filtered_recipes.items(), key=lambda x: x[1].get("cost", 0))

        # Limit to 25 just in case
        for r_id, r_data in sorted_recipes[:25]:
            # Calculate if craftable
            can_craft, _ = self.crafting_system.can_craft(self.interaction_user.id, r_id)

            # Determine Emoji
            if not can_craft:
                emoji = E.LOCKED
            elif r_data.get("type") == "equipment":
                emoji = getattr(E, "SWORDS", "⚔️")
            else:
                emoji = E.POTION

            label = f"{r_data['name']} ({r_data['cost']} G)"

            # Construct materials string
            mats = []
            for m_key, m_amt in r_data.get("materials", {}).items():
                m_name = m_key.replace("_", " ").title()
                mats.append(f"{m_name} x{m_amt}")

            mat_str = ", ".join(mats)
            desc = f"Cost: {r_data['cost']}G • {mat_str}"

            if len(desc) > 100:
                desc = desc[:97] + "..."

            select.add_option(label=label, value=r_id, description=desc, emoji=emoji)

        select.callback = self.recipe_select_callback
        self.add_item(select)

    async def category_cons_callback(self, interaction: discord.Interaction):
        await self._switch_category(interaction, "consumable")

    async def category_equip_callback(self, interaction: discord.Interaction):
        await self._switch_category(interaction, "equipment")

    async def category_dismantle_callback(self, interaction: discord.Interaction):
        await self._switch_category(interaction, "dismantle")

    async def _switch_category(self, interaction: discord.Interaction, category: str):
        if self.category == category:
            await interaction.response.defer()
            return  # No change

        await interaction.response.defer()
        new_view = CraftingView(self.db, self.interaction_user, status_msg=None, category=category)
        # Re-attach back button
        new_view.set_back_button(self.back_button.callback, self.back_button.label)
        embed = new_view.build_embed()
        await interaction.edit_original_response(embed=embed, view=new_view)

    async def recipe_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        recipe_id = interaction.data["values"][0]

        # Execute Craft
        success, msg, item_data = await asyncio.to_thread(
            self.crafting_system.craft_item, self.interaction_user.id, recipe_id
        )

        # Refresh View (Keep category)
        new_view = CraftingView(self.db, self.interaction_user, status_msg=msg, category=self.category)
        new_view.last_success = success
        # Re-attach back button
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        embed = new_view.build_embed()
        await interaction.edit_original_response(embed=embed, view=new_view)

    async def dismantle_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Parse int ID
        try:
            inv_id = int(interaction.data["values"][0])
        except ValueError:
            await interaction.followup.send("Invalid selection.", ephemeral=True)
            return

        # Execute Dismantle
        success, msg, rewards = await asyncio.to_thread(
            self.crafting_system.dismantle_item, self.interaction_user.id, inv_id
        )

        # Refresh View
        new_view = CraftingView(self.db, self.interaction_user, status_msg=msg, category=self.category)
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

        if self.category == "consumable":
            cat_title = "Consumables"
            desc = "Bubbling cauldrons and drying herbs fill the air.\nSelect a recipe to brew potions."
        elif self.category == "equipment":
            cat_title = "Equipment"
            desc = "The forge is hot and the anvil rings.\nSelect a recipe to forge new gear."
        else:
            cat_title = "Dismantling"
            desc = "Salvage materials from your unwanted equipment.\n**Warning:** Dismantled items are destroyed forever."

        embed = discord.Embed(
            title=f"⚗️ Alchemist's Workbench — {cat_title}",
            description=desc,
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
