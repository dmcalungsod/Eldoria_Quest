"""
Main Entry Point for Eldoria Quest
----------------------------------
Initializes the bot, loads cogs, and ensures database integrity.
Hardened: Safe startup, logging, and error handling.
"""

import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

# --- Database Imports ---
# Moved to top to satisfy PEP 8 / Ruff (E402)
from database.create_database import create_tables
from database.populate_database import main as populate_db

# Ensure root dir is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# --- Configuration & Secrets ---
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# --- Logging Setup ---
logs_dir = os.path.join(ROOT_DIR, "logs")
os.makedirs(logs_dir, exist_ok=True)

logger = logging.getLogger("eldoria")
logger.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler(filename=os.path.join(logs_dir, "eldoria.log"), encoding="utf-8", mode="w")
file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(console_handler)

if not TOKEN:
    logger.critical("Missing DISCORD_BOT_TOKEN in .env. Exiting.")
    sys.exit(1)


def init_db():
    """Initializes the database safely on startup."""
    logger.info("Checking database schema...")
    try:
        create_tables()
        populate_db()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


# --- Bot Class ---
class EldoriaBot(commands.Bot):
    def __init__(self):
        # Define intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading commands

        super().__init__(
            command_prefix="!", intents=intents, activity=discord.Game(name="Eldoria | /start"), help_command=None
        )

    async def setup_hook(self):
        """Loads Cogs and Syncs Commands."""
        logger.info("Loading Cogs...")
        cogs_dir = os.path.join(ROOT_DIR, "cogs")

        if not os.path.exists(cogs_dir):
            logger.warning("'cogs' directory missing. Creating...")
            os.makedirs(cogs_dir, exist_ok=True)
            return

        # Dynamic Cog Loading
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("_") and filename != "ui_helpers.py":
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load {cog_name}: {e}", exc_info=True)

        # Command Sync
        if GUILD_ID:
            try:
                guild = discord.Object(id=GUILD_ID)
                self.tree.clear_commands(guild=guild)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Commands synced to Guild ID: {GUILD_ID}")
            except discord.HTTPException as e:
                logger.error(f"Failed to sync commands to guild: {e}")
        else:
            await self.tree.sync()
            logger.info("Commands synced globally (may take up to 1 hour).")

    async def on_ready(self):
        """Called when bot is connected."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Eldoria Quest is online and ready.")


# --- Main Execution ---``
if __name__ == "__main__":
    # 1. Init Database
    init_db()

    # 2. Start Bot
    bot = EldoriaBot()
    try:
        bot.run(TOKEN, log_handler=None)  # Use our custom logger
    except discord.LoginFailure:
        logger.critical("Invalid Token provided.")
    except Exception as e:
        logger.critical(f"Fatal runtime error: {e}", exc_info=True)
