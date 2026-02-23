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
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Overview",
                description="The purpose of the Adventurer's Guild.",
                emoji="📜",
                value="overview",
            ),
            discord.SelectOption(
                label="Fundamentals",
                description="Quests, Exploration, and Inventory.",
                emoji="🎒",
                value="fundamentals",
            ),
            discord.SelectOption(
                label="Combat & Stats",
                description="Attributes, Actions, and Survival.",
                emoji="⚔️",
                value="combat",
            ),
            discord.SelectOption(
                label="Guild Services",
                description="Shop, Infirmary, and Training Grounds.",
                emoji="🏰",
                value="services",
            ),
            discord.SelectOption(
                label="Command Reference",
                description="List of available commands.",
                emoji="⌨️",
                value="commands",
            ),
        ]
        super().__init__(
            placeholder="Select a topic to read...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # The view (self.view) handles the response logic
        await self.view.update_embed(interaction, self.values[0])


class HelpView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())

    async def update_embed(self, interaction: discord.Interaction, selected_value: str):
        embed = self._get_embed(selected_value)
        await interaction.response.edit_message(embed=embed, view=self)

    def _get_embed(self, value: str) -> discord.Embed:
        if value == "overview":
            embed = discord.Embed(
                title="📜 The Adventurer's Guild Handbook",
                description=(
                    "Welcome, Initiate. This handbook serves as your guide to survival and prosperity "
                    "in the shadow of the Spire.\n\n"
                    "The Guild exists to regulate the exploration of the ancient dungeons beneath Astraeon. "
                    "We provide contracts, supplies, and sanctuary to those brave enough to face the darkness."
                ),
                color=discord.Color.dark_gold(),
            )
            embed.add_field(
                name="Your Duty",
                value="Accept quests, slay monsters, gather resources, and return alive. The city depends on the riches you recover.",
                inline=False,
            )

        elif value == "fundamentals":
            embed = discord.Embed(
                title="🎒 Fundamentals of Adventure",
                description="Before you face the horrors below, master these basics.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="1. Quests & Exploration",
                value=(
                    "Visit the **Quest Board** in the Guild Hall to accept contracts. "
                    "Then, use the **Gate** to begin an expedition. "
                    "Expeditions take real time—your character explores while you rest."
                ),
                inline=False,
            )
            embed.add_field(
                name="2. Inventory Management",
                value=(
                    "Your backpack is limited. Use `/inventory` to check your supplies. "
                    "Sell excess materials at the **Guild Exchange** or craft them into gear."
                ),
                inline=False,
            )
            embed.add_field(
                name="3. The Return",
                value=(
                    "When an expedition ends, you must `Claim Rewards` to secure your loot. "
                    "If you fall in battle, you may lose some of what you gathered."
                ),
                inline=False,
            )

        elif value == "combat":
            embed = discord.Embed(
                title="⚔️ Combat & Attributes",
                description="Knowledge is your first line of defense.",
                color=discord.Color.red(),
            )
            embed.add_field(
                name="Attributes",
                value=(
                    "**STR (Strength):** Physical damage.\n"
                    "**DEX (Dexterity):** Accuracy and critical chance.\n"
                    "**END (Endurance):** Health (HP) and defense.\n"
                    "**MAG (Magic):** Spell power and mana (MP).\n"
                    "**AGI (Agility):** Evasion and turn speed.\n"
                    "**LCK (Luck):** Drop rates and critical avoidance."
                ),
                inline=False,
            )
            embed.add_field(
                name="Combat Actions",
                value=(
                    "**Attack:** Standard strike based on your weapon.\n"
                    "**Defend:** Reduces incoming damage significantly.\n"
                    "**Skill:** Uses MP for powerful effects.\n"
                    "**Flee:** Attempt to escape (chance based on AGI)."
                ),
                inline=False,
            )

        elif value == "services":
            embed = discord.Embed(
                title="🏰 Guild Services",
                description="The Guild Hall offers various facilities to aid your journey.",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="🏥 Infirmary",
                value="Heal your wounds and recover MP for a fee. Essential after a tough expedition.",
                inline=False,
            )
            embed.add_field(
                name="⚒️ Workshop",
                value="Craft weapons, armor, and potions using materials found in the dungeon.",
                inline=False,
            )
            embed.add_field(
                name="💰 Exchange",
                value="Buy basic supplies or sell your loot for gold.",
                inline=False,
            )
            embed.add_field(
                name="🏟️ Training Grounds",
                value="Test your strength or spar with fellow adventurers.",
                inline=False,
            )

        elif value == "commands":
            embed = discord.Embed(
                title="⌨️ Command Reference",
                description="Quick access to Guild protocols.",
                color=discord.Color.purple(),
            )
            embed.add_field(
                name="Core",
                value="`/profile` - View your character sheet.\n`/inventory` - Check your backpack.\n`/help` - Open this handbook.",
                inline=False,
            )
            embed.add_field(
                name="Action",
                value="`/quest` - View active quests.\n`/explore` - Start an adventure (requires context).",
                inline=False,
            )
            embed.add_field(
                name="Social",
                value="`/party` - Manage your adventuring party.\n`/guild` - View Guild status.",
                inline=False,
            )

        else:
            embed = discord.Embed(
                title="Error",
                description="Unknown section selected.",
                color=discord.Color.red(),
            )

        return embed


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
            await interaction.response.send_message(
                "Error calculating latency.", ephemeral=True
            )

    @app_commands.command(
        name="help", description="Open the Adventurer's Guild Handbook."
    )
    async def help_command(self, interaction: discord.Interaction):
        """
        Opens the interactive help menu.
        """
        try:
            view = HelpView()
            # Default to Overview
            embed = view._get_embed("overview")
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )
            logger.info(f"Help command used by {interaction.user}")
        except Exception as e:
            logger.error(f"Help command failed: {e}")
            await interaction.response.send_message(
                "The handbook seems stuck in the drawer.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
