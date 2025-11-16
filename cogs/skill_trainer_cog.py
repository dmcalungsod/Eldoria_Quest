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

from database.database_manager import DatabaseManager
from game_systems.data.skills_data import SKILLS
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback


# Helper function for cost calculation
def get_upgrade_cost(base_cost: int, current_level: int) -> int:
    """Calculates the Vestige cost to upgrade a skill."""
    # Formula: BaseCost * (CurrentLevel ^ 1.8)
    cost = base_cost * math.pow(current_level, 1.8)
    return math.ceil(cost)


class SkillTrainerView(View):
    """
    The main UI for the Skill Trainer.
    Allows learning new skills and upgrading existing ones.
    """

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

        # 1. Get skills the player already has
        self.player_skills = self.get_player_skills()

        # 2. Build the UI components
        self.add_item(self.build_learn_select())
        self.add_item(self.build_upgrade_select())

        # 3. Add the back button
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
        """Fetches a dict of skills the player knows, keyed by skill_key."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT skill_key, skill_level FROM player_skills WHERE discord_id = ?",
            (self.interaction_user.id,),
        )
        skills = {row["skill_key"]: row["skill_level"] for row in cur.fetchall()}
        conn.close()
        return skills

    def build_learn_select(self) -> Select:
        """Builds the dropdown for skills the player can learn."""
        learn_select = Select(
            placeholder="Learn a new skill...", min_values=1, max_values=1, row=0
        )

        learnable_skills = []
        for key, skill_data in SKILLS.items():
            # Check if:
            # 1. It matches the player's class
            # 2. It's not a default skill (learn_cost > 0)
            # 3. The player does not already know it
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
                label=f"{skill['name']} ({cost} Vestige)",
                value=f"{skill['key_id']}:{cost}",
                description=skill["description"][:100],
                emoji="📖",
                disabled=(self.vestige_pool < cost),
            )

        learn_select.callback = self.learn_skill_callback
        return learn_select

    def build_upgrade_select(self) -> Select:
        """Builds the dropdown for skills the player can upgrade."""
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

        for skill_key, current_level in self.player_skills.items():
            skill_data = SKILLS.get(skill_key)
            if not skill_data or skill_data.get("upgrade_cost", 0) == 0:
                continue  # Skip passives or un-upgradeable skills

            base_cost = skill_data["upgrade_cost"]
            upgrade_cost = get_upgrade_cost(base_cost, current_level)

            upgrade_select.add_option(
                label=f"{skill_data['name']} (Lvl {current_level} -> {current_level + 1})",
                value=f"{skill_key}:{upgrade_cost}:{current_level}",
                description=f"Cost: {upgrade_cost} Vestige",
                emoji="✨",
                disabled=(self.vestige_pool < upgrade_cost),
            )

        if not upgrade_select.options:
            upgrade_select.add_option(
                label="You have no skills to upgrade.", value="disabled"
            )
            upgrade_select.disabled = True

        upgrade_select.callback = self.upgrade_skill_callback
        return upgrade_select

    async def learn_skill_callback(self, interaction: discord.Interaction):
        """Handles the logic for learning a new skill."""
        await interaction.response.defer()

        skill_key, cost_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)

        # Re-check funds
        player_data = self.db.get_player(self.interaction_user.id)
        if player_data["vestige_pool"] < cost:
            await interaction.followup.send(
                f"{E.ERROR} You do not have enough Vestige.", ephemeral=True
            )
            return

        new_vestige = player_data["vestige_pool"] - cost
        skill_name = SKILLS.get(skill_key, {}).get("name", "Unknown Skill")

        conn = self.db.connect()
        cur = conn.cursor()
        try:
            # Debit Vestige
            cur.execute(
                "UPDATE players SET vestige_pool = ? WHERE discord_id = ?",
                (new_vestige, self.interaction_user.id),
            )
            # Add new skill
            cur.execute(
                "INSERT INTO player_skills (discord_id, skill_key, skill_level) VALUES (?, ?, 1)",
                (self.interaction_user.id, skill_key),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            await interaction.followup.send(
                f"{E.ERROR} Database error while learning skill.", ephemeral=True
            )
            print(f"Skill learn error: {e}")
            return
        finally:
            conn.close()

        await interaction.followup.send(
            f"{E.LEVEL_UP} You have learned **{skill_name}**!", ephemeral=True
        )

        # Refresh the UI
        refreshed_player_data = self.db.get_player(self.interaction_user.id)
        new_embed = self.build_skill_embed(refreshed_player_data)
        new_view = SkillTrainerView(
            self.db, self.interaction_user, refreshed_player_data
        )
        await interaction.edit_original_response(embed=new_embed, view=new_view)

    async def upgrade_skill_callback(self, interaction: discord.Interaction):
        """Handles the logic for upgrading a skill."""
        await interaction.response.defer()

        skill_key, cost_str, level_str = interaction.data["values"][0].split(":")
        cost = int(cost_str)
        current_level = int(level_str)
        new_level = current_level + 1

        # Re-check funds
        player_data = self.db.get_player(self.interaction_user.id)
        if player_data["vestige_pool"] < cost:
            await interaction.followup.send(
                f"{E.ERROR} You do not have enough Vestige.", ephemeral=True
            )
            return

        new_vestige = player_data["vestige_pool"] - cost
        skill_name = SKILLS.get(skill_key, {}).get("name", "Unknown Skill")

        conn = self.db.connect()
        cur = conn.cursor()
        try:
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
            conn.commit()
        except Exception as e:
            conn.rollback()
            await interaction.followup.send(
                f"{E.ERROR} Database error while upgrading skill.", ephemeral=True
            )
            print(f"Skill upgrade error: {e}")
            return
        finally:
            conn.close()

        await interaction.followup.send(
            f"{E.LEVEL_UP} Your **{skill_name}** is now **Level {new_level}**!",
            ephemeral=True,
        )

        # Refresh the UI
        refreshed_player_data = self.db.get_player(self.interaction_user.id)
        new_embed = self.build_skill_embed(refreshed_player_data)
        new_view = SkillTrainerView(
            self.db, self.interaction_user, refreshed_player_data
        )
        await interaction.edit_original_response(embed=new_embed, view=new_view)

    @staticmethod
    def build_skill_embed(player_data):
        """Builds the main embed for the Skill Trainer."""
        embed = discord.Embed(
            title="Skill Trainer",
            description=f"Here you can spend Vestige to acquire new skills or strengthen those you already know.\n\n"
            f"You have: **{player_data['vestige_pool']} Vestige**",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Skills you cannot afford are disabled.")
        return embed


# ======================================================================
# COG LOADER
# ======================================================================


class SkillTrainerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(SkillTrainerCog(bot))
