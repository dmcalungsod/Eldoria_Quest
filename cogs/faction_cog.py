"""
cogs/faction_cog.py

Handles faction management commands: joining, status, and lists.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from database.database_manager import DatabaseManager
from game_systems.data.factions import FACTIONS
from game_systems.guild_system.faction_system import FactionSystem

logger = logging.getLogger("eldoria.factions_cog")


class FactionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.faction_system = FactionSystem(self.db)

    faction_group = app_commands.Group(
        name="faction", description="Faction management commands"
    )

    @faction_group.command(name="list", description="List all available factions.")
    async def list_factions(self, interaction: discord.Interaction):
        """Lists available factions with descriptions."""
        embed = discord.Embed(title="🏔️ Eldoria Factions", color=discord.Color.gold())

        for fid, data in FACTIONS.items():
            name = f"{data['emoji']} {data['name']}"
            desc = data["description"]
            interests = (
                ", ".join(data.get("interests", {}).keys()).replace("_", " ").title()
            )

            embed.add_field(
                name=name, value=f"{desc}\n*Interests: {interests}*", inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @faction_group.command(name="join", description="Join a faction.")
    @app_commands.choices(
        faction=[
            app_commands.Choice(name=data["name"], value=fid)
            for fid, data in FACTIONS.items()
        ]
    )
    async def join_faction(
        self, interaction: discord.Interaction, faction: app_commands.Choice[str]
    ):
        """Joins a selected faction."""
        success, msg = self.faction_system.join_faction(
            interaction.user.id, faction.value
        )
        await interaction.response.send_message(msg, ephemeral=True)

    @faction_group.command(name="status", description="Check your faction status.")
    async def faction_status(self, interaction: discord.Interaction):
        """Displays current faction status."""
        data = self.faction_system.get_player_faction(interaction.user.id)

        if not data:
            await interaction.response.send_message(
                "You are not in a faction. Use `/faction list` to see options.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"{data['emoji']} {data['name']}",
            description=data["description"],
            color=discord.Color.green(),
        )

        embed.add_field(
            name="Rank",
            value=f"{data['rank_title']} (Tier {data['rank_tier']})",
            inline=True,
        )
        embed.add_field(name="Reputation", value=f"{data['reputation']}", inline=True)

        next_rank = data.get("next_rank")
        if next_rank:
            needed = next_rank["reputation_needed"] - data["reputation"]
            embed.add_field(
                name="Next Rank",
                value=f"{next_rank['title']} (Needs {needed} more rep)",
                inline=False,
            )
        else:
            embed.add_field(
                name="Next Rank", value="Maximum Rank Achieved", inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @faction_group.command(
        name="leave",
        description="Leave your current faction (Reputation will be reset).",
    )
    async def leave_faction(self, interaction: discord.Interaction):
        """Leaves the current faction."""
        # Confirmation could be added here with a View, but for simplicity we'll just do it.
        success, msg = self.faction_system.leave_faction(interaction.user.id)
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(FactionCog(bot))
