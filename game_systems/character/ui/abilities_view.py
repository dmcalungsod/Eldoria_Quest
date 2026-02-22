"""
game_systems/character/ui/abilities_view.py

Displays the character’s personal capabilities: inventory and skills.
Hardened: Async fetching for responsive UI.
"""

import asyncio
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback, build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager

from .inventory_view import InventoryView

logger = logging.getLogger("eldoria.ui.abilities")


class AbilitiesView(View):
    """
    Displays the character’s personal capabilities.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.inventory_manager = InventoryManager(self.db)
        self.interaction_user = interaction_user

        # Inventory Button
        btn_inv = Button(
            label="Manage Equipment",
            style=discord.ButtonStyle.secondary,
            custom_id="prof_inv",
            emoji=E.BACKPACK,
            row=0,
        )
        btn_inv.callback = self.inventory_callback
        self.add_item(btn_inv)

        # Skills Button
        btn_skills = Button(
            label="View Skills",
            style=discord.ButtonStyle.secondary,
            custom_id="prof_skills",
            emoji="✨",
            row=0,
        )
        btn_skills.callback = self.skills_callback
        self.add_item(btn_skills)

        # Return Button
        btn_back = Button(
            label="Return — Profile",
            style=discord.ButtonStyle.grey,
            custom_id="back_prof",
            row=1,
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your profile.", ephemeral=True)
            return False
        return True

    # ---------------------------------------------------------------
    # INVENTORY VIEW
    # ---------------------------------------------------------------

    async def inventory_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            items = await asyncio.to_thread(self.inventory_manager.get_inventory, self.interaction_user.id)
            max_slots = await asyncio.to_thread(self.db.calculate_inventory_limit, self.interaction_user.id)
            # build_inventory_embed is CPU bound (formatting), safe to run in thread
            embed = await asyncio.to_thread(build_inventory_embed, items, max_slots)

            view = InventoryView(
                self.db,
                self.interaction_user,
                previous_view_callback=back_to_profile_callback,
                previous_view_label="Return — Character",
            )

            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Inventory open error: {e}", exc_info=True)
            await interaction.followup.send("Error opening inventory.", ephemeral=True)

    # ---------------------------------------------------------------
    # SKILLS VIEW
    # ---------------------------------------------------------------

    async def skills_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            skills = await asyncio.to_thread(self.db.get_player_skills, self.interaction_user.id)

            if not skills:
                skills_str = "*No recorded techniques.*"
            else:
                # Using dict access since Row behaves like dict
                skills_str = "\n".join([f"• **{s['name']}** — *{s['type']}*, Rank {s['skill_level']}" for s in skills])

            embed = discord.Embed(
                title="📖 Tome of Arts",
                description=(f"*Collected techniques and disciplined forms.*\n\n{skills_str}"),
                color=discord.Color.purple(),
            )

            view = SkillsView(self.db, self.interaction_user)

            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Skills view error: {e}", exc_info=True)
            await interaction.followup.send("Error loading skills.", ephemeral=True)


# --------------------------------------------------------------------
# SKILLS VIEW (Sub-view)
# --------------------------------------------------------------------


class SkillsView(View):
    def __init__(self, db, interaction_user):
        super().__init__(timeout=180)
        self.user = interaction_user

        btn_back = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
