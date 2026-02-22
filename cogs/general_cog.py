"""
cogs/general_cog.py

Handles general utility commands for all users.
Hardened: Added logging for monitoring.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

logger = logging.getLogger("eldoria.general")


class HelpSelect(Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Select a topic to learn more...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        embed = discord.Embed(color=discord.Color.dark_gold())

        if val == "Getting Started":
            embed.title = "🌱 Getting Started"
            embed.description = (
                "Welcome to Eldoria. Your journey begins with the **/start** command.\n\n"
                "1. **Create your Character**: Choose your class wisely.\n"
                "2. **Visit the Guild**: From your Profile (`/start`), enter the Guild Hall.\n"
                "3. **Accept a Quest**: Check the Quest Board for work.\n"
                "4. **Adventure**: Use the 'Adventure' button on your Profile to explore.\n"
                "5. **Return**: Report back to the Guild to claim rewards."
            )
        elif val == "Commands":
            embed.title = "📜 Command Reference"
            embed.add_field(
                name="/start", value="The main menu. Access Profile, Inventory, and Adventure.", inline=False
            )
            embed.add_field(name="/help", value="Opens this handbook.", inline=False)
            embed.add_field(name="/ping", value="Check connection latency.", inline=False)
            embed.set_footer(text="Most actions are performed via buttons in the interface.")
        elif val == "Guild & Quests":
            embed.title = "🏰 Guild & Quests"
            embed.description = (
                "The **Adventurer's Guild** is your home base.\n\n"
                "**Ranks**: You start at Rank F. Complete quests to earn promotion trials.\n"
                "**Quests**: Contracts post daily. They require you to defeat monsters or collect items.\n"
                "**Shop**: Spend your hard-earned Aurum on potions and gear."
            )
        elif val == "Combat & Exploration":
            embed.title = "⚔️ Combat & Exploration"
            embed.description = (
                "The dungeons are unforgiving. Prepare yourself.\n\n"
                "**Turn-Based Combat**: You and the enemy take turns. Choose Attack, Defend, or Skill.\n"
                "**Telegraphs**: Watch for cues like *'The enemy winds up!'* Use **Defend** or interrupt with a Skill!\n"
                "**Resting**: Use a Campfire during adventures to recover HP/MP, but beware of ambushes.\n"
                "**Return**: Always return to the Guild to save your loot. Death means losing items!"
            )
        elif val == "Character Progression":
            embed.title = "📈 Character Progression"
            embed.description = (
                "**Stats**: Strength, Dexterity, Magic... choose gear that complements your build.\n"
                "**Skills**: Unlock new abilities as you level up.\n"
                "**Inventory**: You have limited space. Sell junk materials at the Guild Shop."
            )

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=180)
        self.user = user

        # Define options for the Select Menu
        options = [
            discord.SelectOption(label="Getting Started", description="First steps in Eldoria", emoji="🌱"),
            discord.SelectOption(label="Commands", description="List of available commands", emoji="📜"),
            discord.SelectOption(label="Guild & Quests", description="How to earn coin and fame", emoji="🏰"),
            discord.SelectOption(label="Combat & Exploration", description="Surviving the dungeons", emoji="⚔️"),
            discord.SelectOption(label="Character Progression", description="Stats, Skills, and Gear", emoji="📈"),
        ]

        # Add the Select Menu
        self.add_item(HelpSelect(options))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This manual is not for you.", ephemeral=True)
            return False
        return True


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

    @app_commands.command(name="help", description="Open the Adventurer's Handbook.")
    async def help_command(self, interaction: discord.Interaction):
        """
        Displays the interactive help menu.
        """
        embed = discord.Embed(
            title="📘 Adventurer's Handbook",
            description=(
                "Welcome, traveler. This tome contains knowledge to aid your survival.\n\n"
                "**Select a topic below to begin.**"
            ),
            color=discord.Color.dark_gold(),
        )
        view = HelpView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
