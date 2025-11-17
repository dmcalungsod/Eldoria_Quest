"""
game_systems/character/ui/abilities_view.py
"""

import discord
import asyncio
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from cogs.ui_helpers import back_to_profile_callback, build_inventory_embed
import game_systems.data.emojis as E

from .inventory_view import InventoryView


class AbilitiesView(View):
    """
    Displays the character’s personal capabilities:
    inventory, tools, and learned combat techniques.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.inventory_manager = InventoryManager(self.db)
        self.interaction_user = interaction_user

        # Inventory Button
        btn_inv = Button(
            label="Field Kit",
            style=discord.ButtonStyle.secondary,
            custom_id="prof_inv",
            emoji=E.BACKPACK,
            row=0,
        )
        btn_inv.callback = self.inventory_callback
        self.add_item(btn_inv)

        # Skills Button
        btn_skills = Button(
            label="Tome of Arts",
            style=discord.ButtonStyle.secondary,
            custom_id="prof_skills",
            emoji="✨",
            row=0,
        )
        btn_skills.callback = self.skills_callback
        self.add_item(btn_skills)

        # Return Button
        btn_back = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_prof",
            row=1,
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id

    # ---------------------------------------------------------------
    # INVENTORY VIEW
    # ---------------------------------------------------------------

    async def inventory_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        items = await asyncio.to_thread(
            self.inventory_manager.get_inventory, self.interaction_user.id
        )
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            self.db,
            self.interaction_user,
            previous_view_callback=back_to_profile_callback,
            previous_view_label="Return — Character",
        )

        await interaction.edit_original_response(embed=embed, view=view)

    # ---------------------------------------------------------------
    # SKILLS VIEW
    # ---------------------------------------------------------------

    async def skills_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        skills = await asyncio.to_thread(
            self.db.get_player_skills, self.interaction_user.id
        )

        if not skills:
            skills_str = "*No recorded techniques.*"
        else:
            skills_str = "\n".join(
                [
                    f"• **{s['name']}** — *{s['type']}*, Rank {s['skill_level']}"
                    for s in skills
                ]
            )

        embed = discord.Embed(
            title="📖 Tome of Arts",
            description=(
                "*Collected techniques and disciplined forms.*\n\n"
                f"{skills_str}"
            ),
            color=discord.Color.purple(),
        )

        view = SkillsView(self.db, self.interaction_user)

        await interaction.edit_original_response(embed=embed, view=view)


# --------------------------------------------------------------------
# SKILLS VIEW
# --------------------------------------------------------------------

class SkillsView(View):
    def __init__(self, db, interaction_user):
        super().__init__(timeout=None)
        self.user = interaction_user

        btn_back = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
        )
        btn_back.callback = back_to_profile_callback
        self.add_item(btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # FIX: this was broken before
        return interaction.user.id == self.user.id
