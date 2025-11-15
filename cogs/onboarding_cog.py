"""
onboarding_cog.py

Handles the /start command and the new player onboarding flow:
- Class Selection (StartMenuView, ClassDetailView)
- Character Creation (ClassDetailView)
- Guild Registration (CharacterMenuView)
"""

from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.player.player_creator import PlayerCreator
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
from game_systems.data.messages import WELCOME_MESSAGE, WELCOME_TITLE
from game_systems.data.stat_descriptions import STAT_DESCRIPTIONS
import game_systems.data.emojis as E

# --- Handoff Import ---
from .ui_helpers import back_to_profile_callback


# ======================================================================
# ONBOARDING VIEWS
# ======================================================================


class StartMenuView(View):
    """
    The main menu view for the /start command.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.create_class_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    def create_class_buttons(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM classes ORDER BY id")
        classes = cur.fetchall()
        conn.close()
        for cls in classes:
            button = Button(label=cls["name"], custom_id=f"class_{cls['id']}")
            button.callback = self.class_button_callback
            self.add_item(button)

    async def class_button_callback(self, interaction: discord.Interaction):
        class_id = int(interaction.data["custom_id"].split("_")[1])
        class_name = None
        for name, data in CLASS_DEFINITIONS.items():
            if data["id"] == class_id:
                class_name = name
                break
        if not class_name:
            await interaction.response.send_message(
                "This class does not exist.", ephemeral=True
            )
            return

        class_data = CLASS_DEFINITIONS[class_name]
        base_stats = [
            f"`{stat:<3}: {value:>2}`" for stat, value in class_data["stats"].items()
        ]
        stats_lines = []
        for i in range(0, len(base_stats), 3):
            stats_lines.append("  ".join(base_stats[i : i + 3]))
        stats_block = "\n".join(stats_lines)
        descriptions = "\n".join(
            [
                f"> **{stat}** – {STAT_DESCRIPTIONS.get(stat, 'No description.')}"
                for stat in class_data["stats"]
            ]
        )
        description_string = (
            f"{class_data['description']}\n\n"
            f"**Base Stats**\n{stats_block}\n\n"
            f"**Stat Descriptions:**\n{descriptions}"
        )
        embed = discord.Embed(
            title=class_name,
            description=description_string,
            color=0x00B0F4,
            timestamp=datetime.now(),
        )
        view = ClassDetailView(self.db, class_id, self.interaction_user)
        await interaction.response.edit_message(embed=embed, view=view)


class ClassDetailView(View):
    """
    The view that shows the details of a specific class.
    """

    def __init__(
        self, db_manager: DatabaseManager, class_id: int, interaction_user: discord.User
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.class_id = class_id
        self.interaction_user = interaction_user

        create_button = Button(
            label="Create",
            style=discord.ButtonStyle.success,
            custom_id=f"create_{self.class_id}",
        )
        create_button.callback = self.create_button_callback
        self.add_item(create_button)
        back_button = Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_main_menu",
        )
        back_button.callback = self.back_button_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def create_button_callback(self, interaction: discord.Interaction):
        creator = PlayerCreator(self.db)
        success, message = creator.create_player(
            interaction.user.id, interaction.user.display_name, self.class_id
        )
        if success:
            welcome_title = (
                f"Welcome, {interaction.user.display_name}, to Ashgrave City."
            )
            welcome_description = (
                "Your name is known, but your deeds are not. The path ahead is fraught with peril... \n\n"
                "To seek purpose, coin, or redemption, you must register with the **Adventurer's Guild**."
            )
            embed = discord.Embed(
                title=welcome_title,
                description=welcome_description,
                color=discord.Color.dark_gold(),
            )
            embed.set_footer(text="Your journey begins now. Tread boldly.")
            view = CharacterMenuView(self.db, self.interaction_user)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(
                f"{E.WARNING} {message}", ephemeral=True
            )

    async def back_button_callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold()
        )
        embed.set_footer(
            text="Once you have chosen a class, you can create your character."
        )
        view = StartMenuView(self.db, self.interaction_user)
        await interaction.response.edit_message(embed=embed, view=view)


class CharacterMenuView(View):
    """
    The view displayed after a character has been created, prompting for guild registration.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        register_button = Button(
            label="Register with the Adventurer's Guild",
            style=discord.ButtonStyle.success,
            custom_id="register_guild",
        )
        register_button.callback = self.register_button_callback
        self.add_item(register_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def register_button_callback(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,)
            )
            if cur.fetchone():
                # This check is good, but the button shouldn't be visible
                # if the player is already registered.
                # For now, we'll just hand off to the profile.
                conn.close()
                await back_to_profile_callback(interaction, is_new_message=False)
                return

            cur.execute(
                "INSERT INTO guild_members (discord_id, join_date) VALUES (?, ?)",
                (discord_id, join_date),
            )
            conn.commit()
            conn.close()

            # --- THIS IS THE FIX ---
            #
            # We no longer send an ephemeral message.
            # We call the back_to_profile_callback directly.
            # That helper function will defer the interaction and then
            # edit the original message, which is the correct
            # "ONE UI" behavior.
            #
            # [REMOVED] embed = discord.Embed(...)
            # [REMOVED] await interaction.response.send_message(embed=embed, ephemeral=True)
            #
            # --- END OF FIX ---

            # This call will now handle the response, defer, and edit.
            await back_to_profile_callback(interaction, is_new_message=False)

        except Exception as e:
            print(f"Error during guild registration: {e}")
            # We still need to respond to the interaction on failure
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{E.ERROR} An error occurred during registration.", ephemeral=True
                )


# ======================================================================
# COG LOADER
# ======================================================================


class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="start", description="Begin your journey in Eldoria.")
    async def start(self, interaction: discord.Interaction):
        """
        The main entry point for new players.
        """
        if self.db.player_exists(interaction.user.id):
            # --- FIX: Load profile in a NEW message ---
            await interaction.response.send_message(
                f"{E.WARNING} You are already an adventurer. Loading your profile...",
                ephemeral=True,
            )
            # This creates a new, persistent "ONE UI" message
            await back_to_profile_callback(interaction, is_new_message=True)
            return

        embed = discord.Embed(
            title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold()
        )
        embed.set_footer(
            text="Once you have chosen a class, you can create your character."
        )

        # --- THE FIX ---
        # Send the first message as non-ephemeral.
        # This becomes the "ONE UI" that everything else edits.
        view = StartMenuView(self.db, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))
