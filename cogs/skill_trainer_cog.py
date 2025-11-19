"""
cogs/skill_trainer_cog.py

Handles the Skill Trainer UI.
Hardened: Atomic transactions for learning/upgrading skills.
"""

import asyncio
import math
import logging
import sqlite3
from typing import Tuple

import discord
from discord.ext import commands
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.skills_data import SKILLS
from .ui_helpers import back_to_guild_hall_callback

logger = logging.getLogger("eldoria.ui.trainer")


def get_upgrade_cost(base_cost: int, current_level: int) -> int:
    """Returns the Vestige cost to upgrade a skill."""
    return math.ceil(base_cost * math.pow(current_level, 1.8))


class SkillTrainerView(View):
    """Main UI for the Skill Trainer."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: sqlite3.Row,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.player_data = dict(player_data)  # Convert to dict for safe local mutation

        self.vestige_pool = self.player_data["vestige_pool"]
        self.player_class_id = self.player_data["class_id"]

        # Load skills synchronously here as it is lightweight reading
        self.player_skills = self._get_player_skills_sync()

        # Components
        self.add_item(self.build_learn_select())
        self.add_item(self.build_upgrade_select())

        # Back Button
        self.back_button = Button(
            label="Return — Guild Hall",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=2,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def _get_player_skills_sync(self) -> dict:
        """Helper to get skills for UI setup."""
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute(
                    "SELECT skill_key, skill_level FROM player_skills WHERE discord_id = ?",
                    (self.interaction_user.id,),
                ).fetchall()
            return {row["skill_key"]: row["skill_level"] for row in rows}
        except Exception:
            return {}

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This session is not yours.", ephemeral=True)
            return False
        return True

    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function

    # --------------------------------------------------------
    # Dropdown Builders
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
            learn_select.add_option(label="No new skills available.", value="disabled")
            learn_select.disabled = True
            return learn_select

        for skill in learnable:
            cost = skill["learn_cost"]
            can_afford = self.vestige_pool >= cost
            emoji = "📖" if can_afford else "🔒"
            
            learn_select.add_option(
                label=f"{skill['name']} ({cost} V)",
                value=f"{skill['key_id']}:{cost}",
                description=skill["description"][:90],
                emoji=emoji,
            )

        learn_select.callback = self.learn_skill_callback
        return learn_select

    def build_upgrade_select(self) -> Select:
        upgrade_select = Select(
            placeholder="Upgrade an existing skill...",
            min_values=1,
            max_values=1,
            row=1,
        )

        if not self.player_skills:
            upgrade_select.add_option(label="No skills to upgrade.", value="disabled")
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
            can_afford = self.vestige_pool >= upgrade_cost
            emoji = E.LEVEL_UP if can_afford else "🔒"

            upgrade_select.add_option(
                label=f"{data['name']} (Lv. {level} → {level + 1})",
                value=f"{skill_key}:{upgrade_cost}:{level}",
                description=f"Cost: {upgrade_cost} Vestige",
                emoji=emoji,
            )

        if not has_upgradable:
            upgrade_select.add_option(label="Max level reached or not upgradable.", value="disabled")
            upgrade_select.disabled = True

        upgrade_select.callback = self.upgrade_skill_callback
        return upgrade_select

    # --------------------------------------------------------
    # Execution Logic (Threaded)
    # --------------------------------------------------------
    def _execute_learn(self, skill_key: str, cost: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                # 1. Verify Funds
                row = conn.execute(
                    "SELECT vestige_pool FROM players WHERE discord_id = ?", 
                    (self.interaction_user.id,)
                ).fetchone()
                
                if not row or row["vestige_pool"] < cost:
                    return False, "Insufficient Vestige."

                # 2. Deduct & Learn
                conn.execute(
                    "UPDATE players SET vestige_pool = vestige_pool - ? WHERE discord_id = ?",
                    (cost, self.interaction_user.id)
                )
                conn.execute(
                    "INSERT INTO player_skills (discord_id, skill_key, skill_level) VALUES (?, ?, 1)",
                    (self.interaction_user.id, skill_key)
                )
            return True, "Skill Learned!"
        except Exception as e:
            logger.error(f"Learn skill error: {e}")
            return False, "System error."

    def _execute_upgrade(self, skill_key: str, cost: int, new_level: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                # 1. Verify Funds
                row = conn.execute(
                    "SELECT vestige_pool FROM players WHERE discord_id = ?", 
                    (self.interaction_user.id,)
                ).fetchone()
                
                if not row or row["vestige_pool"] < cost:
                    return False, "Insufficient Vestige."

                # 2. Deduct & Upgrade
                conn.execute(
                    "UPDATE players SET vestige_pool = vestige_pool - ? WHERE discord_id = ?",
                    (cost, self.interaction_user.id)
                )
                conn.execute(
                    "UPDATE player_skills SET skill_level = ? WHERE discord_id = ? AND skill_key = ?",
                    (new_level, self.interaction_user.id, skill_key)
                )
            return True, "Skill Upgraded!"
        except Exception as e:
            logger.error(f"Upgrade skill error: {e}")
            return False, "System error."

    # --------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------
    async def learn_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        skill_key, cost = interaction.data["values"][0].split(":")
        
        success, msg = await asyncio.to_thread(self._execute_learn, skill_key, int(cost))
        await self._refresh_ui(interaction, success, msg, skill_key)

    async def upgrade_skill_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        skill_key, cost, level = interaction.data["values"][0].split(":")
        new_level = int(level) + 1
        
        success, msg = await asyncio.to_thread(self._execute_upgrade, skill_key, int(cost), new_level)
        await self._refresh_ui(interaction, success, msg, skill_key, new_level)

    async def _refresh_ui(self, interaction, success, msg, skill_key, level=1):
        """Common refresh logic."""
        p_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        
        embed = self.build_skill_embed(dict(p_data), msg if success else f"Error: {msg}")
        
        new_view = SkillTrainerView(self.db, self.interaction_user, p_data)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)
        
        await interaction.edit_original_response(embed=embed, view=new_view)

    @staticmethod
    def build_skill_embed(player_data, status_message: str = None):
        embed = discord.Embed(
            title="🧠 Guild Skill Trainer",
            description=(
                f"**Available Vestige:** {player_data['vestige_pool']} {E.VESTIGE}\n"
                "*Select a technique to learn or refine.*"
            ),
            color=discord.Color.dark_blue(),
        )

        if status_message:
            embed.add_field(name="Status", value=status_message, inline=False)

        return embed


class SkillTrainerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()

async def setup(bot):
    await bot.add_cog(SkillTrainerCog(bot))