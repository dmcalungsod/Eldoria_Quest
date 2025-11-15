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
# We import the GuildCardView from the *other* cog.
# This is the handoff from onboarding to the main guild menu.
from .guild_cog import GuildCardView


# ======================================================================
# ONBOARDING VIEWS
# ======================================================================


class StartMenuView(View):
    """
    The main menu view for the /start command.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.create_class_buttons()

    def create_class_buttons(self):
        """
        Dynamically creates buttons for each class in the database.
        """
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
        """
        Callback for the class buttons. Shows the class detail view.
        """
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

        # Build the single description string
        stats_line = "  ".join(
            [f"`{stat}: {value}`" for stat, value in class_data["stats"].items()]
        )

        descriptions = "\n".join(
            [
                f"> `{stat}` – {STAT_DESCRIPTIONS.get(stat, 'No description available.')}"
                for stat in class_data["stats"]
            ]
        )

        description_string = (
            f"{class_data['description']}\n\n"
            f"**Base Stats**\n"
            f"{stats_line}\n\n"
            f"> **Stat Descriptions:**\n"
            f"{descriptions}\n\n"
            f"**Class ID:** {class_data['id']}"
        )

        embed = discord.Embed(
            title=class_name,
            description=description_string,
            color=0x00B0F4,
            timestamp=datetime.now(),
        )

        view = ClassDetailView(self.db, class_id)
        await interaction.response.edit_message(embed=embed, view=view)


class ClassDetailView(View):
    """
    The view that shows the details of a specific class.
    """

    def __init__(self, db_manager: DatabaseManager, class_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.class_id = class_id

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

    async def create_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the create button. Creates a new character and updates the view.
        """
        creator = PlayerCreator(self.db)
        success, message = creator.create_player(
            interaction.user.id, interaction.user.display_name, self.class_id
        )

        if success:
            welcome_title = f"Welcome, {interaction.user.display_name}, to The Eldorian Adventurer’s Consortium."
            welcome_description = (
                "Your name has been recorded in the registry. The path ahead is fraught with peril, "
                "shadows, and whispers of forgotten power. May your will be your guide and your courage be your shield.\n\n"
                "Your journey begins now. Tread boldly."
            )

            embed = discord.Embed(
                title=welcome_title,
                description=welcome_description,
                color=discord.Color.dark_gold(),
            )
            embed.set_footer(
                text="Under the watchful eyes of Guildmaster Daemon Caelungarde."
            )

            view = CharacterMenuView(self.db)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(
                f"{E.WARNING} {message}", ephemeral=True
            )

    async def back_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the back button. Returns to the main menu.
        """
        embed = discord.Embed(
            title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold()
        )
        embed.set_footer(
            text="Once you have chosen a class, you can create your character."
        )

        view = StartMenuView(self.db)
        await interaction.response.edit_message(embed=embed, view=view)


class CharacterMenuView(View):
    """
    The view displayed after a character has been created, prompting for guild registration.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        register_button = Button(
            label="Register with the Guild",
            style=discord.ButtonStyle.success,
            custom_id="register_guild",
        )
        register_button.callback = self.register_button_callback
        self.add_item(register_button)

    async def register_button_callback(self, interaction: discord.Interaction):
        """
        Callback for the register button. Registers the player in the guild
        and hands them off to the main GuildCardView.
        """
        discord_id = interaction.user.id
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = self.db.connect()
            cur = conn.cursor()

            # Check if already registered
            cur.execute(
                "SELECT * FROM guild_members WHERE discord_id = ?", (discord_id,)
            )
            if cur.fetchone():
                await interaction.response.send_message(
                    "You are already registered with the Guild.", ephemeral=True
                )
                conn.close()
                return

            # Register the player
            cur.execute(
                "INSERT INTO guild_members (discord_id, join_date) VALUES (?, ?)",
                (discord_id, join_date),
            )
            conn.commit()

            # Fetch player and guild data for the card
            cur.execute(
                """
                SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
                FROM players p
                JOIN classes c ON p.class_id = c.id
                JOIN guild_members gm ON p.discord_id = gm.discord_id
                WHERE p.discord_id = ?
            """,
                (discord_id,),
            )
            card_data = cur.fetchone()
            conn.close()

            if not card_data:
                await interaction.response.send_message(
                    f"{E.ERROR} Error retrieving your Guild Card.", ephemeral=True
                )
                return

            # Create the Guild Card embed
            embed = discord.Embed(
                title=f"{E.SCROLL} Guild Card",
                # --- TYPO FIX ---
                description=f"This card certifies that **{card_data['name']}** is a registered member of The Eldorian Adventurer’s Consortium.",
                color=discord.Color.dark_gold(),
            )
            embed.add_field(name="Class", value=card_data["class_name"], inline=True)
            embed.add_field(name="Rank", value=card_data["rank"], inline=True)
            embed.add_field(name="Level", value=card_data["level"], inline=True)
            embed.add_field(
                name="Experience", value=f"{card_data['experience']} XP", inline=True
            )
            embed.set_footer(text=f"Joined: {card_data['join_date']}")

            # --- HANDOFF ---
            # We now pass control to the main Guild menu
            view = GuildCardView(self.db)
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"Error during guild registration: {e}")
            await interaction.response.send_message(
                f"{E.ERROR} An error occurred during registration.", ephemeral=True
            )


# ======================================================================
# COG LOADER
# ======================================================================


class OnboardingCog(commands.Cog):
    """
    A cog for UI-based commands.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="start", description="Begin your journey in Eldoria.")
    async def start(self, interaction: discord.Interaction):
        """
        The main entry point for new players.
        """
        embed = discord.Embed(
            title=WELCOME_TITLE, description=WELCOME_MESSAGE, color=discord.Color.gold()
        )
        embed.set_footer(
            text="Once you have chosen a class, you can create your character."
        )

        view = StartMenuView(self.db)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))
