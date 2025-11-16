import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv
import asyncio
import logging
import traceback

# --- Path Configuration ---
# This ensures that the bot can find your 'core' modules
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# --- Setup Logging ---
logs_dir = os.path.join(ROOT_DIR, "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)  # Set to INFO or DEBUG for more details
handler = logging.FileHandler(
    filename=os.path.join(logs_dir, "eldoria.log"), encoding="utf-8", mode="w"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

# --- Load Token & Guild ID ---
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

if TOKEN is None:
    print("CRITICAL ERROR: DISCORD_BOT_TOKEN not found in .env file.")
    logger.critical("DISCORD_BOT_TOKEN not found in .env file. Bot cannot start.")
    exit()

if GUILD_ID is None:
    print(
        "Warning: GUILD_ID not found in .env file. Slash commands will be registered globally, which can take up to an hour to update."
    )
    logger.warning(
        "GUILD_ID not found in .env file. Slash commands will be registered globally."
    )


# --- Bot Class ---
class EldoriaBot(commands.Bot):
    """
    Main Bot class for Eldoria Quest.
    """

    def __init__(self):
        # Define the intents your bot needs
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading !commands
        intents.members = True  # Optional: for greeting new members

        super().__init__(
            command_prefix="!",
            intents=intents,
            activity=discord.Game(name="Eldoria | /start"),
            help_command=None,  # We will build a custom one
        )

    async def setup_hook(self):
        """
        This is called once when the bot logs in.
        It's the perfect place to load your Cogs (extensions).
        """
        print("--- Loading Cogs ---")
        logger.info("Loading Cogs...")

        cogs_dir = os.path.join(ROOT_DIR, "cogs")
        if not os.path.exists(cogs_dir):
            os.makedirs(cogs_dir)
            logger.warning("No 'cogs' directory found. Created one.")
            print("No 'cogs' directory found. I've created one for you.")

        for filename in os.listdir(cogs_dir):
            # This logic automatically finds and loads your new cogs
            if (
                filename.endswith(".py")
                and not filename.startswith("_")
                and filename != "ui_helpers.py"
            ):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    print(f"  [+] Loaded: {cog_name}")
                    logger.info(f"Successfully loaded extension: {cog_name}")
                except Exception as e:
                    # If a cog fails, log it and continue
                    print(f"  [!] FAILED to load: {cog_name}")
                    logger.error(f"Failed to load extension {cog_name}.", exc_info=True)
                    traceback.print_exc()

        print("--- Cog loading complete ---")

        # Sync slash commands to the specific guild for instant updates
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"--- Synced slash commands to Guild ID: {GUILD_ID} ---")
            logger.info(f"Synced slash commands to Guild ID: {GUILD_ID}")
        else:
            # If no guild ID, sync globally (slower)
            await self.tree.sync()
            print("--- Synced slash commands globally ---")
            logger.info("Synced slash commands globally.")

    async def on_ready(self):
        """
        Called when the bot is fully connected and ready.
        """
        print("-------------------------------------------------")
        print(f"Logged in as: {self.user.name} (ID: {self.user.id})")
        print(f"Discord.py Version: {discord.__version__}")
        print("Eldoria is online and ready for adventure!")
        print("-------------------------------------------------")
        logger.info(f"Bot '{self.user.name}' is online and ready.")


from database.create_database import create_tables
from database.populate_database import main as populate_db

# --- Main Entry Point ---
if __name__ == "__main__":
    # Ensure the database schema is created and populated before the bot runs
    print("--- Initializing Database ---")
    create_tables()
    populate_db()
    print("--- Database Initialized and Populated ---")

    bot = EldoriaBot()

    try:
        # This starts the bot
        bot.run(TOKEN, log_handler=handler)
    except discord.errors.LoginFailure:
        logger.critical("Improper token passed. Bot cannot log in.")
        print("\nError: Improper token passed. Please check your .env file.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")