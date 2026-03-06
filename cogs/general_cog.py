"""
cogs/general_cog.py

Handles general utility commands for all users.
Hardened: Added logging for monitoring.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("eldoria.general")


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        """
        Returns the bot's current websocket latency.
        """
        try:
            # Latency is in seconds, convert to ms
            latency_ms = round(self.bot.latency * 1000)

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latency: **{latency_ms}ms**",
                color=discord.Color.blue(),
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Ping requested by {interaction.user} ({latency_ms}ms)")

        except Exception as e:
            logger.error(f"Ping command failed: {e}")
            await interaction.response.send_message("Error calculating latency.", ephemeral=True)

    @app_commands.command(name="help", description="Access the Guild Handbook to learn about Eldoria.")
    async def help_command(self, interaction: discord.Interaction):
        """
        Sends the Guild Handbook explaining core game concepts.
        """
        try:
            embed = discord.Embed(
                title="Guild Handbook",
                description="*The pages are worn, bearing the stains of countless adventurers before you.*",
                color=discord.Color.dark_gold(),
            )
            embed.add_field(
                name="/start",
                value="Begin your journey in Astraeon City and register with the Guild.",
                inline=False,
            )
            embed.add_field(
                name="⚔️ Guild Classes",
                value="Warriors hold the line, Mages shape the Veil, Rogues strike from the shadows, Clerics mend shattered flesh, Rangers track unseen horrors, and Alchemists turn the environment against the enemy.",
                inline=False,
            )
            embed.add_field(
                name="🗺️ Expeditions",
                value="Time-based exploration is your core duty. Select a destination and duration, then wait for your return. The wilds do not sleep—prepare your supplies carefully, or the darkness will claim you.",
                inline=False,
            )
            embed.add_field(
                name="📜 Quests & Guild Hall",
                value="Review available contracts and report successes at the Guild Hall. Access the Shop, Infirmary, and Training Grounds.",
                inline=False,
            )
            embed.add_field(
                name="👤 Profile",
                value="View your Guild Card, manage your abilities, and prepare your kit for the next expedition.",
                inline=False,
            )
            embed.set_footer(text="May your light hold against the darkness.")

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Help handbook requested by {interaction.user}")

        except Exception as e:
            logger.error(f"Help command failed: {e}")
            await interaction.response.send_message("Error accessing the Guild Handbook.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
