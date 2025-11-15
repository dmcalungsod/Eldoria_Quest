"""
Character Commands Cog
Handles /status (Falna), /inventory, and other player management.
"""

import discord
from discord import app_commands
from discord.ext import commands
from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E


class CharacterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.inventory = InventoryManager(self.db)

    @app_commands.command(
        name="status", description="View your Falna (Adventurer Status)."
    )
    async def status(self, interaction: discord.Interaction):
        """Displays the player's stats, rank, and progress."""
        await interaction.response.defer()

        discord_id = interaction.user.id
        player = self.db.get_player(discord_id)

        if not player:
            await interaction.followup.send(
                "You have not registered with the Guild yet. Use `/start`.",
                ephemeral=True,
            )
            return

        # Get Guild Rank
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT rank, merit_points FROM guild_members WHERE discord_id = ?",
            (discord_id,),
        )
        guild_data = cur.fetchone()
        conn.close()

        # Get Stats
        stats_json = self.db.get_player_stats_json(discord_id)
        stats = PlayerStats.from_dict(stats_json)

        # Determine Class Name
        class_row = self.db.get_class(player["class_id"])
        class_name = class_row["name"] if class_row else "Unknown"

        # --- Build the Danmachi-style Embed ---
        embed = discord.Embed(
            title=f"{E.SCROLL} Falna — {player['name']}",
            description=f"**Familia:** Eldorian Consortium\n**Class:** {class_name}",
            color=discord.Color.dark_red(),
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        # Rank & Level
        embed.add_field(
            name="Condition",
            value=f"**Lv.** {player['level']}\n**Rank:** {guild_data['rank']}",
            inline=True,
        )
        embed.add_field(
            name="Progress",
            value=f"**EXP:** {player['experience']} / {player['exp_to_next']}\n**Merit:** {guild_data['merit_points']}",
            inline=True,
        )

        # The 6 Basic Abilities
        stat_block = (
            f"{E.STR} **STR:** {stats.strength:<4}  "
            f"{E.DEX} **DEX:** {stats.dexterity}\n"
            f"{E.CON} **CON:** {stats.constitution:<4}  "
            f"{E.INT} **INT:** {stats.intelligence}\n"
            f"{E.WIS} **WIS:** {stats.wisdom:<4}  "
            f"{E.CHA} **CHA:** {stats.charisma}\n"
            f"{E.LCK} **LCK:** {stats.luck}"
        )
        embed.add_field(name="Basic Abilities", value=stat_block, inline=False)

        # Resources
        embed.add_field(
            name="Vitals",
            value=f"{E.HP} **HP:** {stats.max_hp}\n{E.MP} **MP:** {stats.max_mp}",
            inline=True,
        )
        embed.add_field(
            name="Wealth",
            value=f"{E.AURUM} **Aurum:** {player['aurum']}",
            inline=True,
        )

        embed.set_footer(text="The hieroglyphs on your back glow faintly.")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="inventory", description="Check your backpack.")
    async def inventory(self, interaction: discord.Interaction):
        """Displays the player's items."""
        items = self.inventory.get_inventory(interaction.user.id)

        if not items:
            await interaction.response.send_message(
                f"{E.BACKPACK} Your backpack is empty.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.BACKPACK} Backpack", color=discord.Color.brown()
        )

        # Group by type
        categories = {}
        for item in items:
            itype = item["item_type"].title()
            if itype not in categories:
                categories[itype] = []
            categories[itype].append(f"• {item['item_name']} (x{item['count']})")

        for category, item_list in categories.items():
            embed.add_field(name=category, value="\n".join(item_list), inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(CharacterCommands(bot))
