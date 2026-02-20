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
from discord.ui import View, Select

from database.database_manager import DatabaseManager
import game_systems.data.emojis as E

logger = logging.getLogger("eldoria.chronicles")

class TitleSelect(Select):
    def __init__(self, titles, current_active):
        options = []

        # Add "No Title" option
        options.append(discord.SelectOption(
            label="No Title",
            value="None",
            description="Remove your current title.",
            default=(current_active is None)
        ))

        # Sort titles for consistency
        sorted_titles = sorted(titles)

        for title in sorted_titles:
            options.append(discord.SelectOption(
                label=title,
                value=title,
                default=(title == current_active)
            ))

        # Truncate if too many (Discord limit 25 options)
        if len(options) > 25:
             options = options[:25]

        super().__init__(placeholder="Choose a title...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        selected = self.values[0]
        title_to_set = None if selected == "None" else selected

        db = DatabaseManager()
        success = await asyncio.to_thread(db.set_active_title, interaction.user.id, title_to_set)

        if success:
            await interaction.followup.send(f"Title set to: **{selected if selected != 'None' else 'None'}**", ephemeral=True)
        else:
            await interaction.followup.send("Failed to set title.", ephemeral=True)

class ChroniclesView(View):
    def __init__(self, db, user, titles, active_title):
        super().__init__(timeout=180)
        self.db = db
        self.user = user

        if titles:
            self.add_item(TitleSelect(titles, active_title))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

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
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Active Title",
            value=f"**{active_title}**" if active_title else "*None*",
            inline=False
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
