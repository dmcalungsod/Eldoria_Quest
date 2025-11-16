"""
cogs/skill_trainer_cog.py

Handles the "Skill Trainer" UI where players
spend Vestige to learn new skills and upgrade existing ones.
"""

import discord
from discord.ui import View, Button, Select
from discord.ext import commands
import json
import sqlite3
import math
import asyncio
from typing import Tuple

from database.database_manager import DatabaseManager
from game_systems.data.skills_data import SKILLS
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback


# --------------------------------------
# Helper function for cost calculation
# --------------------------------------
def get_upgrade_cost(base_cost: int, current_level: int) -> int:
    """Calculates the Vestige cost to upgrade a skill."""
    cost = base_cost * math.pow(current_level, 1.8)
    return math.ceil(cost)


# --------------------------------------
# Skill Trainer View
# --------------------------------------
class SkillTrainerView(View):
    """UI view for the skill trainer."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: sqlite3.Row,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.player_data = player_data
        self.vestige_pool = player_data["vestige_pool"]
        self.player_class_id = player_data["class_id"]

        # Fetch player skills
        self.player_skills = self.get_player_skills()

        # Build UI components
        self.add_item(self.build_learn_select())
        self.add_item(self.build_upgrade_select())

        # Back button
        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=2,
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your guild.", ephemeral=True
            )
            return False
        return True

    def get_player_skills(self) -> dict:
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT skill_key, skill_level FROM player_skills WHERE discord_id = ?",
            (self.interaction_user.id,),
        )
        skills = {row["skill_key"]: row["skill_level"] for row in cur.fetchall()}
        conn.close()
        return skills

    # ------------------------------------------------
    # Build Learn Select
    # ------------------------------------------------
    def build_learn_select(self) -> Select:
        learn_select = Select(
            placeholder="Learn a new skill...", min_values=1, max_values=1, row=0
        )

        learnable_skills = []
        for key, skill_data in SKILLS.items():
            if (
                skill_data.get("class_id") == self.player_class_id
                and skill_data.get("learn_cost", 0) > 0
                and key not in self.player_skills
            ):
                learnable_skills.append(skill_data)

        if not learnable_skills:
            learn_select.add_option(label="No new skills to learn.", value="disabled")
            learn_select.disabled = True
            return learn_select

        for skill in learnable_skills:
            cost = skill["learn_cost"]
            learn_select.add_option(
                label=f"{skill['name']} ({cost} {E.VESTIGE})",
                value=f"{skill['key_id']}:{cost}",
                description=skill["description"][:100],
                emoji="📖",
            )

        if self.vestige_pool == 0:
            learn_select.placeholder = "You have no Vestige to learn skills."

        learn_select.callback = self.learn_skill_callback
        return learn_select

    # ------------------------------------------------
    # Build Upgrade Select
    # ------------------------------------------------
    def build_upgrade_select(self) -> Select:
        upgrade_select = Select(
            placeholder="Upgrade an existing skill...",
            min_values=1,
            max_values=1,
            row=1,
        )

        if not self.player_skills:
            upgrade_select.add_option(
                label="You have no skills to upgrade.", value="disabled"
            )
            upgrade_select.disabled = True
            return upgrade_select

        has_upgradable_skill = False
        for skill_key, current_level in self.player_skills.items():
            skill_data = SKILLS.get(skill_key)
            if not skill_data or skill_data.get("upgrade_cost", 0) == 0:
                continue

            has_upgradable_skill = True
            base_cost = skill_data["upgrade_cost"]
            upgrade_cost = get_upgrade_cost(base_cost, current_level)

            upgrade_select.add_option(
                label=f"{skill_data['name']} (Lvl {current_level} → {current_level + 1})",
                value=f"{skill_key}:{upgrade_cost}:{current_level}",
                description=f"Cost: {upgrade_cost} {E.VESTIGE}",
                emoji="✨",
            )

        if not has_upgradable_skill:
            upgrade_select.add_option(
                label="You have no skills to upgrade.", value="disabled"
            )
            upgrade_select.disabled = True

        upgrade_select.callback = self.upgrade_skill_callback
        return upgrade_select

    # ------------------------------------------------
    # Learning Skill (async thread wrapper)
    # ------------------------------------------------
    def _execute_learn_skill(self, skill_key: str, cost: int) -> Tuple[bool, str, int]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT vestige_pool FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            player_data = cur.fetchone()

            if player_data["vestige_pool"] < cost:
                return (False, "You do not have enough Vestige.", 0)

            new_vestige = player_data["vestige_pool"] - cost

            # Update player Vestige
            cur.execute(
                "UPDATE players SET vestige_pool = ? WHERE discord_id = ?",
                (new_vestige, self.interaction_user.id),
            )

            # Add skill
            cur.execute(
                "INSERT INTO player_skills (discord_id, skill_key, skill_level) VALUES (?, ?, 1)",
                (self.interaction_user.id, skill_key),
            )

            return (True, "", new_vestige)

    async def learn_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        skill_key, cost_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)

        success, error_msg, new_vestige = await asyncio.to_thread(
            self._execute_learn_skill, skill_key, cost
        )

        if not success:
            await interaction.followup.send(f"{E.ERROR} {error_msg}", ephemeral=True)
            return

        skill_name = SKILLS.get(skill_key, {}).get("name", "Unknown Skill")
        await interaction.followup.send(
            f"{E.LEVEL_UP} You have learned **{skill_name}**!", ephemeral=True
        )

        # Refresh UI
        refreshed_player_data = await asyncio.to_thread(
            self.db.get_player, self.interaction_user.id
        )
        new_embed = self.build_skill_embed(refreshed_player_data)
        new_view = SkillTrainerView(self.db, self.interaction_user, refreshed_player_data)
        await interaction.edit_original_response(embed=new_embed, view=new_view)

    # ------------------------------------------------
    # Upgrade Skill (async wrapper)
    # ------------------------------------------------
    def _execute_upgrade_skill(
        self, skill_key: str, cost: int, new_level: int
    ) -> Tuple[bool, str, int]:

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT vestige_pool FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            player_data = cur.fetchone()

            if player_data["vestige_pool"] < cost:
                return (False, "You do not have enough Vestige.", 0)

            new_vestige = player_data["vestige_pool"] - cost

            # Debit Vestige
            cur.execute(
                "UPDATE players SET vestige_pool = ? WHERE discord_id = ?",
                (new_vestige, self.interaction_user.id),
            )

            # Upgrade skill
            cur.execute(
                "UPDATE player_skills SET skill_level = ? WHERE discord_id = ? AND skill_key = ?",
                (new_level, self.interaction_user.id, skill_key),
            )

            return (True, "", new_vestige)

    async def upgrade_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        skill_key, cost_str, level_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)
        current_level = int(level_str)
        new_level = current_level + 1

        success, error_msg, new_vestige = await asyncio.to_thread(
            self._execute_upgrade_skill, skill_key, cost, new_level
        )

        if not success:
            await interaction.followup.send(f"{E.ERROR} {error_msg}", ephemeral=True)
            return

        skill_name = SKILLS.get(skill_key, {}).get("name", "Unknown Skill")
        await interaction.followup.send(
            f"{E.LEVEL_UP} Your **{skill_name}** is now **Level {new_level}**!",
            ephemeral=True,
        )

        refreshed_player_data = await asyncio.to_thread(
            self.db.get_player, self.interaction_user.id
        )
        new_embed = self.build_skill_embed(refreshed_player_data)
        new_view = SkillTrainerView(self.db, self.interaction_user, refreshed_player_data)
        await interaction.edit_original_response(embed=new_embed, view=new_view)

    # ------------------------------------------------
    # Embed
    # ------------------------------------------------
    @staticmethod
    def build_skill_embed(player_data):
        embed = discord.Embed(
            title="Skill Trainer",
            description=(
                f"Here you can spend Vestige to acquire new skills or strengthen those you already know.\n\n"
                f"You have: **{player_data['vestige_pool']} {E.VESTIGE} Vestige**"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Skills you cannot afford are disabled in the dropdown.")
        return embed


# --------------------------------------
# Cog Wrapper (Required for Extension)
# --------------------------------------
class SkillTrainerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to open trainer (you already have this in your bot?)
    @commands.command(name="skilltrainer")
    async def open_skill_trainer(self, ctx):
        """Manual command for testing."""
        db = DatabaseManager()
        player = db.get_player(ctx.author.id)

        if not player:
            await ctx.send("No player found.")
            return

        embed = SkillTrainerView.build_skill_embed(player)
        view = SkillTrainerView(db, ctx.author, player)
        await ctx.send(embed=embed, view=view)


# --------------------------------------
# REQUIRED SETUP FUNCTION
# --------------------------------------
async def setup(bot):
    await bot.add_cog(SkillTrainerCog(bot))
