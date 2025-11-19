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
                title="🏓 Pong!", description=f"Latency: **{latency_ms}ms**", color=discord.Color.blue()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Ping requested by {interaction.user} ({latency_ms}ms)")

        except Exception as e:
            logger.error(f"Ping command failed: {e}")
            await interaction.response.send_message("Error calculating latency.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
