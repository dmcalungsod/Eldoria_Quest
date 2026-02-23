"""
Chronicle System
----------------
UI for managing titles and achievements.
"""

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from database.database_manager import DatabaseManager
from game_systems.chronicle.ui.chronicle_view import ChroniclesView

logger = logging.getLogger("eldoria.chronicles")


class ChronicleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="chronicles", description="View and manage your earned titles.")
    async def chronicles(self, interaction: discord.Interaction):
        await interaction.response.defer()

        discord_id = interaction.user.id

        # Check if player exists
        exists = await asyncio.to_thread(self.db.player_exists, discord_id)
        if not exists:
            await interaction.followup.send("You do not have a character profile.", ephemeral=True)
            return

        titles = await asyncio.to_thread(self.db.get_titles, discord_id)
        active_title = await asyncio.to_thread(self.db.get_active_title, discord_id)

        description = "*Your deeds are etched in history.*"

        embed = discord.Embed(
            title="🏆 Chronicles & Titles",
            description=description,
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="Active Title",
            value=f"**{active_title}**" if active_title else "*None*",
            inline=False,
        )

        if titles:
            titles.sort()
            titles_str = ", ".join([f"`{t}`" for t in titles])
            embed.add_field(name=f"Unlocked Titles ({len(titles)})", value=titles_str, inline=False)
        else:
            embed.add_field(name="Unlocked Titles", value="*No titles earned yet.*", inline=False)

        view = ChroniclesView(self.db, interaction.user, titles, active_title)

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ChronicleCog(bot))
