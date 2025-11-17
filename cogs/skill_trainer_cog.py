"""
cogs/skill_trainer_cog.py

Handles the Skill Trainer UI where players spend Vestige
to learn new skills or upgrade existing ones.

Refined for clarity, consistency, and ONE UI Policy compliance.
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

# Local
from .ui_helpers import back_to_guild_hall_callback


# ============================================================
# Cost Helper
# ============================================================
def get_upgrade_cost(base_cost: int, current_level: int) -> int:
    """Returns the Vestige cost to upgrade a skill."""
    return math.ceil(base_cost * math.pow(current_level, 1.8))


# ============================================================
# Skill Trainer View
# ============================================================
class SkillTrainerView(View):
    """Main UI for the Skill Trainer."""

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

        self.player_skills = self.get_player_skills()

        # Learn & Upgrade dropdowns
        self.add_item(self.build_learn_select())
        self.add_item(self.build_upgrade_select())

        # Back
        self.back_button = Button(
            label="Return — Guild Hall",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=2,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    # --------------------------------------------------------
    # Interaction gate
    # --------------------------------------------------------
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your session.", ephemeral=True
            )
            return False
        return True
        
    # --------------------------------------------------------
    # Navigation Helper (FIX ADDED HERE)
    # --------------------------------------------------------
    def set_back_button(self, callback_function, label="Back"):
        """Allows parent menus to override the back button destination."""
        self.back_button.label = label
        self.back_button.callback = callback_function

    # --------------------------------------------------------
    # Load player's skill dict
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Learn Skill Dropdown
    # --------------------------------------------------------
    def build_learn_select(self) -> Select:
        learn_select = Select(
            placeholder="Learn a new skill...",
            min_values=1,
            max_values=1,
            row=0,
        )

        learnable = [
            s for s in SKILLS.values()
            if s.get("class_id") == self.player_class_id
            and s.get("learn_cost", 0) > 0
            and s["key_id"] not in self.player_skills
        ]

        if not learnable:
            learn_select.add_option(label="No new skills to learn.", value="disabled")
            learn_select.disabled = True
            return learn_select

        for skill in learnable:
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

    # --------------------------------------------------------
    # Upgrade Skill Dropdown
    # --------------------------------------------------------
    def build_upgrade_select(self) -> Select:
        upgrade_select = Select(
            placeholder="Upgrade an existing skill...",
            min_values=1,
            max_values=1,
            row=1,
        )

        if not self.player_skills:
            upgrade_select.add_option(label="You have no skills to upgrade.", value="disabled")
            upgrade_select.disabled = True
            return upgrade_select

        has_upgradable = False

        for skill_key, level in self.player_skills.items():
            data = SKILLS.get(skill_key)
            if not data or data.get("upgrade_cost", 0) == 0:
                continue

            has_upgradable = True
            base_cost = data["upgrade_cost"]
            upgrade_cost = get_upgrade_cost(base_cost, level)

            upgrade_select.add_option(
                label=f"{data['name']} (Lv. {level} → {level + 1})",
                value=f"{skill_key}:{upgrade_cost}:{level}",
                description=f"Cost: {upgrade_cost} {E.VESTIGE}",
                emoji=E.LEVEL_UP,
            )

        if not has_upgradable:
            upgrade_select.add_option(label="No skills can be upgraded.", value="disabled")
            upgrade_select.disabled = True

        upgrade_select.callback = self.upgrade_skill_callback
        return upgrade_select

    # ============================================================
    # Learn Skill (DB thread)
    # ============================================================
    def _execute_learn_skill(self, skill_key: str, cost: int) -> Tuple[bool, str]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT vestige_pool FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            row = cur.fetchone()
            if not row:
                return False, "Player data missing."

            vestige = row["vestige_pool"]
            if vestige < cost:
                return False, "You do not have enough Vestige."

            # Deduct & add skill
            cur.execute(
                "UPDATE players SET vestige_pool = ? WHERE discord_id = ?",
                (vestige - cost, self.interaction_user.id),
            )
            cur.execute(
                "INSERT INTO player_skills (discord_id, skill_key, skill_level) VALUES (?, ?, 1)",
                (self.interaction_user.id, skill_key),
            )
            return True, ""

    async def learn_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        skill_key, cost_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)

        success, error_msg = await asyncio.to_thread(
            self._execute_learn_skill, skill_key, cost
        )

        if not success:
            status = f"{E.ERROR} {error_msg}"
        else:
            status = f"{E.LEVEL_UP} You have learned **{SKILLS[skill_key]['name']}**!"

        refreshed = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        embed = self.build_skill_embed(refreshed, status)
        view = SkillTrainerView(self.db, self.interaction_user, refreshed)

        # preserve your custom back button behavior
        view.back_button.callback = self.back_button.callback
        view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=embed, view=view)

    # ============================================================
    # Upgrade Skill (DB thread)
    # ============================================================
    def _execute_upgrade_skill(self, skill_key: str, cost: int, new_level: int) -> Tuple[bool, str]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT vestige_pool FROM players WHERE discord_id = ?",
                (self.interaction_user.id,),
            )
            row = cur.fetchone()

            if row["vestige_pool"] < cost:
                return False, "You do not have enough Vestige."

            # Deduct and upgrade
            cur.execute(
                "UPDATE players SET vestige_pool = ? WHERE discord_id = ?",
                (row["vestige_pool"] - cost, self.interaction_user.id),
            )
            cur.execute(
                "UPDATE player_skills SET skill_level = ? WHERE discord_id = ? AND skill_key = ?",
                (new_level, self.interaction_user.id, skill_key),
            )
            return True, ""

    async def upgrade_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        skill_key, cost_str, level_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)
        new_level = int(level_str) + 1

        success, error_msg = await asyncio.to_thread(
            self._execute_upgrade_skill, skill_key, cost, new_level
        )

        if not success:
            status = f"{E.ERROR} {error_msg}"
        else:
            name = SKILLS.get(skill_key, {}).get("name", "Unknown Skill")
            status = f"{E.LEVEL_UP} **{name}** is now **Level {new_level}**!"

        refreshed = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        embed = self.build_skill_embed(refreshed, status)
        view = SkillTrainerView(self.db, self.interaction_user, refreshed)

        view.back_button.callback = self.back_button.callback
        view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=embed, view=view)

    # ============================================================
    # Embed Builder
    # ============================================================
    @staticmethod
    def build_skill_embed(player_data, status_message: str = None):
        embed = discord.Embed(
            title="🧠 Guild Skill Trainer",
            description=(
                "*A quiet chamber lined with sigils, tomes, and training apparatus.*\n"
                "*A seasoned mentor observes you, awaiting your intent.*\n\n"
                f"**Current Vestige:** {player_data['vestige_pool']} {E.VESTIGE}"
            ),
            color=discord.Color.dark_blue(),
        )

        if status_message:
            embed.add_field(name="Training Report", value=status_message, inline=False)

        embed.set_footer(text="Unaffordable options will appear disabled.")
        return embed


# ============================================================
# Cog Wrapper
# ============================================================
class SkillTrainerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot):
    await bot.add_cog(SkillTrainerCog(bot))