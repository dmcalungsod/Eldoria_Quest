"""
guild_hub_cog.py

Handles the main "Guild Hall" UI, which is the GuildCardView.
This is the central hub for players.
It also contains the direct sub-menus for administrative tasks:
- Profile/Falna
- Guild Exchange
- Rank Progress
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
from game_systems.player.player_stats import PlayerStats
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_card_callback

# We import the Quest views from the other cog for the button callback
from .quest_hub_cog import QuestBoardView, QuestLogView


# =GA===================================================================
# GUILD CARD & MAIN MENU
# ======================================================================


class GuildCardView(View):
    """
    The view for the player's Guild Card, showing main actions.
    This is the "Main Menu" of the Guild Hall.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)

        # --- Row 1: Primary Actions ---
        quests_button = Button(
            label="Quest Board",
            style=discord.ButtonStyle.primary,
            custom_id="view_quests",
            emoji=E.HERB,
        )
        quests_button.callback = self.view_quests_callback
        self.add_item(quests_button)

        quest_log_button = Button(
            label="Quest Log",
            style=discord.ButtonStyle.primary,
            custom_id="view_quest_log",
            emoji=E.QUEST_SCROLL,
        )
        quest_log_button.callback = self.view_quest_log_callback
        self.add_item(quest_log_button)

        exchange_button = Button(
            label="Guild Exchange",
            style=discord.ButtonStyle.primary,
            custom_id="guild_exchange",
            emoji=E.EXCHANGE,
        )
        exchange_button.callback = self.guild_exchange_callback
        self.add_item(exchange_button)

        # --- Row 2: Character Management ---
        profile_button = Button(
            label="View Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="view_profile",
            emoji=E.SCROLL,
        )
        profile_button.callback = self.view_profile_callback
        self.add_item(profile_button)

        check_rank_button = Button(
            label="Check Rank",
            style=discord.ButtonStyle.secondary,
            custom_id="check_rank",
            emoji=E.MEDAL,
        )
        check_rank_button.callback = self.check_rank_callback
        self.add_item(check_rank_button)

    async def view_quests_callback(self, interaction: discord.Interaction):
        """
        Hands off to the QuestBoardView from the quest_hub_cog.
        """
        await interaction.response.defer()
        # We must import the QuestSystem here to pass it
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)

        available_quests = quest_system.get_available_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets—some crisp and new, others curled and water-stained. The scent of pine resin clings to them.",
            color=discord.Color.dark_green(),
        )

        if not available_quests:
            embed.add_field(
                name="No Quests Available",
                value="There are currently no quests available for your rank. Check back later, adventurer.",
            )
        else:
            for quest in available_quests:
                embed.add_field(
                    name=f"[{quest['tier']}-Rank] {quest['title']} (ID: {quest['id']})",
                    value=quest["summary"],
                    inline=False,
                )

        view = QuestBoardView(self.db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)

    async def view_quest_log_callback(self, interaction: discord.Interaction):
        """
        Hands off to the QuestLogView from the quest_hub_cog.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)

        active_quests = quest_system.get_player_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventurer's Log",
            description="A review of your currently accepted assignments from the Guild.",
            color=discord.Color.from_rgb(139, 69, 19),  # Brown
        )

        if not active_quests:
            embed.add_field(
                name="No Active Quests",
                value="You have no assignments. Please visit the Quest Board to accept a new task.",
            )
        else:
            for quest in active_quests:
                progress_text = []
                for obj_type, tasks in quest["objectives"].items():
                    if isinstance(tasks, dict):
                        for task, required in tasks.items():
                            current = quest["progress"].get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                    else:
                        current = quest["progress"].get(obj_type, {}).get(tasks, 0)
                        progress_text.append(f"• {tasks}: {current} / 1")

                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text),
                    inline=False,
                )

        view = QuestLogView(self.db)
        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_exchange_callback(self, interaction: discord.Interaction):
        """
        Switches to the Guild Exchange view.
        """
        await interaction.response.defer()

        exchange = GuildExchange(self.db)
        total_value, materials = exchange.calculate_exchange_value(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description=f'A guild receptionist looks up from her ledger. "Greetings, adventurer. Here to exchange your haul for Aurum?"\n\nShe tallies your materials...',
            color=discord.Color.blue(),
        )

        if total_value == 0:
            embed.add_field(
                name="Materials on Hand", value="You have no materials to exchange."
            )
        else:
            mat_list = [f"• {item['item_name']} x{item['count']}" for item in materials]
            embed.add_field(
                name="Materials on Hand", value="\n".join(mat_list), inline=False
            )
            embed.add_field(
                name="Total Value",
                value=f"{E.AURUM} **{total_value} Aurum**",
                inline=False,
            )

        view = GuildExchangeView(self.db, total_value > 0)
        await interaction.edit_original_response(embed=embed, view=view)

    async def view_profile_callback(self, interaction: discord.Interaction):
        """
        Displays the player's 'Falna' or profile.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        player = self.db.get_player(discord_id)

        if not player:
            await interaction.edit_original_response(
                content="Could not find your player data.", embed=None, view=None
            )
            return

        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT rank, merit_points FROM guild_members WHERE discord_id = ?",
            (discord_id,),
        )
        guild_data = cur.fetchone()
        conn.close()

        stats_json = self.db.get_player_stats_json(discord_id)
        stats = PlayerStats.from_dict(stats_json)
        class_row = self.db.get_class(player["class_id"])
        class_name = class_row["name"] if class_row else "Unknown"

        embed = discord.Embed(
            title=f"{E.SCROLL} Falna — {player['name']}",
            description=f"**Familia:** Eldorian Consortium\n**Class:** {class_name}",
            color=discord.Color.dark_red(),
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else None
        )
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
        embed.add_field(
            name="Vitals",
            value=f"{E.HP} **HP:** {stats.max_hp}\n{E.MP} **MP:** {stats.max_mp}",
            inline=True,
        )
        embed.add_field(
            name="Wealth",
            value=f"{E.AURUM} **Aurum:** {player['gold']}",
            inline=True,
        )
        embed.set_footer(text="The hieroglyphs on your back glow faintly.")

        view = ProfileView(self.db)
        await interaction.edit_original_response(embed=embed, view=view)

    async def check_rank_callback(self, interaction: discord.Interaction):
        """
        Checks player's promotion eligibility and switches to the Rank Progress view.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        player_data = self.rank_system.get_rank_info(discord_id)

        if not player_data:
            await interaction.edit_original_response(
                content="Could not retrieve your guild data.", embed=None, view=None
            )
            return

        current_rank = player_data["rank"]
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have already reached the highest available rank. Your legend is known throughout the Guild.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(
                self.db, eligible=False
            )  # Create view with disabled button
            await interaction.edit_original_response(embed=embed, view=view)
            return

        requirements = self.rank_system.RANKS[current_rank].get("requirements", {})
        next_rank_title = self.rank_system.RANKS[next_rank_key]["title"]

        # Build the progress report embed
        embed = discord.Embed(
            title=f"{E.MEDAL} Promotion Evaluation: Rank {current_rank} → Rank {next_rank_key}",
            description=f"Here is your progress towards the rank of **{next_rank_title}**.",
            color=discord.Color.blue(),
        )

        progress_text = ""
        eligible = True
        for req, required_value in requirements.items():
            current_value = player_data.get(req, 0)
            progress_text += f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}\n"
            if current_value < required_value:
                eligible = False

        embed.add_field(name="Current Progress", value=progress_text, inline=False)

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(
                text="You are eligible for promotion! Speak with the Guild Master."
            )
        else:
            embed.set_footer(text="Continue your efforts, adventurer.")

        # Switch to the new view, passing eligibility to the button
        view = RankProgressView(self.db, eligible=eligible)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# PROFILE VIEW
# ======================================================================


class ProfileView(View):
    """
    Simple view that just shows the player's Falna/Status.
    Its only purpose is to provide a "Back" button.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        # Button 1: Back to Guild Card
        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================


class RankProgressView(View):
    """
    Shows the player's progress towards the next rank.
    Contains the "Promote" button.
    """

    def __init__(self, db_manager: DatabaseManager, eligible: bool):
        super().__init__(timeout=None)
        self.db = db_manager

        # Button 1: Promote
        promote_button = Button(
            label="Request Promotion",
            style=discord.ButtonStyle.success,
            custom_id="promote",
            disabled=not eligible,
        )
        promote_button.callback = self.promote_callback
        self.add_item(promote_button)

        # Button 2: Back to Guild Card
        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback
        self.add_item(back_button)

    async def promote_callback(self, interaction: discord.Interaction):
        """
        Promotes the player to the next rank.
        """
        discord_id = interaction.user.id
        rank_system = RankSystem(self.db)
        success, message = rank_system.promote_player(discord_id)

        if success:
            await interaction.response.defer()
            # Show the promotion message ephemerally
            await interaction.followup.send(message, ephemeral=True)
            # Go back to the Guild Card, which will now show the new rank
            await back_to_guild_card_callback(interaction)
        else:
            await interaction.response.send_message(message, ephemeral=True)


# ======================================================================
# GUILD EXCHANGE VIEW
# ======================================================================


class GuildExchangeView(View):
    """
    Handles the UI for selling materials.
    """

    def __init__(self, db_manager: DatabaseManager, can_sell: bool):
        super().__init__(timeout=None)
        self.db = db_manager

        # Button 1: Sell Materials
        sell_button = Button(
            label="Sell All Materials",
            style=discord.ButtonStyle.success,
            custom_id="sell_mats",
            disabled=not can_sell,
            emoji=E.AURUM,
        )
        sell_button.callback = self.sell_materials_callback
        self.add_item(sell_button)

        # Button 2: Back to Guild Card
        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback  # Use the global helper
        self.add_item(back_button)

    async def sell_materials_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        exchange = GuildExchange(self.db)
        total_earned, sold_items = exchange.exchange_all_materials(interaction.user.id)

        if total_earned == 0:
            await interaction.followup.send("You have nothing to sell.", ephemeral=True)
            return

        # Create receipt
        sold_list = [f"• {item['item_name']} x{item['count']}" for item in sold_items]

        receipt_embed = discord.Embed(
            title=f"{E.EXCHANGE} Exchange Complete",
            description=f'The receptionist stamps your ledger. "A fine haul, adventurer. Your payment has been processed."\n\n**Total Earned: {E.AURUM} {total_earned} Aurum**',
            color=discord.Color.green(),
        )
        receipt_embed.add_field(name="Sold Materials", value="\n".join(sold_list))

        # Go back to the main guild card, showing the receipt ephemerally
        await back_to_guild_card_callback(interaction, embed_to_show=receipt_embed)


# ======================================================================
# COG LOADER
# ======================================================================


class GuildHubCog(commands.Cog):
    """
    A cog for housing the main Guild Hub UI and its admin sub-views.
    This cog has no commands, it just makes the Views loadable
    and acts as the import hub for other UI cogs.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))
