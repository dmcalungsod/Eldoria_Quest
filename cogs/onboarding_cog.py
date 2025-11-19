"""
onboarding_cog.py

Character creation flow.
Hardened against race conditions and double-creations.
"""

import asyncio
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
from game_systems.data.messages import WELCOME_MESSAGE, WELCOME_TITLE
from game_systems.data.stat_descriptions import STAT_DESCRIPTIONS
from game_systems.player.player_creator import PlayerCreator
from .ui_helpers import back_to_profile_callback

logger = logging.getLogger("eldoria.onboarding")

class StartMenuView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=300)
        self.db = db_manager
        self.interaction_user = interaction_user
        self._init_buttons()

    def _init_buttons(self):
        # Static class list, safe to load synchronously
        sorted_classes = sorted(CLASS_DEFINITIONS.items(), key=lambda x: x[1]['id'])
        for name, data in sorted_classes:
            btn = Button(label=name, custom_id=f"cls_{data['id']}")
            btn.callback = self.class_select_callback
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id

    async def class_select_callback(self, interaction: discord.Interaction):
        class_id = int(interaction.data["custom_id"].split("_")[1])
        
        # Find class data
        class_info = next((v for k, v in CLASS_DEFINITIONS.items() if v["id"] == class_id), None)
        class_name = next((k for k, v in CLASS_DEFINITIONS.items() if v["id"] == class_id), "Unknown")

        if not class_info:
            await interaction.response.send_message("Class data error.", ephemeral=True)
            return

        # Format Stats
        stats_str = "\n".join([f"`{k}: {v}`" for k, v in class_info["stats"].items()])
        desc_str = f"{class_info['description']}\n\n**Base Stats:**\n{stats_str}"

        embed = discord.Embed(title=class_name, description=desc_str, color=0x00B0F4)
        view = ClassDetailView(self.db, class_id, self.interaction_user)
        await interaction.response.edit_message(embed=embed, view=view)

class ClassDetailView(View):
    def __init__(self, db, class_id, user):
        super().__init__(timeout=300)
        self.db = db
        self.class_id = class_id
        self.user = user
        self.creator = PlayerCreator(db)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Create Character", style=discord.ButtonStyle.success)
    async def create_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        # 1. Final check for existing character (Race condition prevention)
        exists = await asyncio.to_thread(self.db.player_exists, self.user.id)
        if exists:
            await interaction.followup.send("You already have a character!", ephemeral=True)
            return

        # 2. Create
        success, msg = await asyncio.to_thread(
            self.creator.create_player, self.user.id, self.user.display_name, self.class_id
        )

        if success:
            embed = discord.Embed(
                title="Welcome to Astraeon",
                description="You have registered with the Guild. Your journey begins.",
                color=discord.Color.gold()
            )
            view = CharacterMenuView(self.db, self.user)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.followup.send(f"{E.WARNING} {msg}", ephemeral=True)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold())
        view = StartMenuView(self.db, self.user)
        await interaction.response.edit_message(embed=embed, view=view)

class CharacterMenuView(View):
    def __init__(self, db, user):
        super().__init__(timeout=300)
        self.db = db
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Enter Guild Hall", style=discord.ButtonStyle.success)
    async def enter_btn(self, interaction: discord.Interaction, button: Button):
        await back_to_profile_callback(interaction, is_new_message=False)

class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="start", description="Begin your adventure.")
    async def start(self, interaction: discord.Interaction):
        exists = await asyncio.to_thread(self.db.player_exists, interaction.user.id)
        
        if exists:
            await interaction.response.defer()
            await back_to_profile_callback(interaction, is_new_message=True)
        else:
            embed = discord.Embed(title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold())
            view = StartMenuView(self.db, interaction.user)
            await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))