"""
guild_cog.py

Handles all persistent UI Views for the main Guild Hall.
This cog has NO slash commands. It is a library of Views that
other cogs (like onboarding_cog) can call.
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

from database.database_manager import DatabaseManager
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
import game_systems.data.emojis as E


# ======================================================================
# GLOBAL HELPER CALLBACK
# ======================================================================


async def back_to_guild_card_callback(
    interaction: discord.Interaction, embed_to_show: discord.Embed = None
):
    """
    A shared callback to return to the main Guild Card menu.
    This prevents code duplication.
    If embed_to_show is provided, it's shown ephemerally *before* the edit.
    """
    # Defer the response if it's the first action
    if not interaction.response.is_done():
        await interaction.response.defer()

    # If we have a receipt (like from selling), show it ephemerally
    if embed_to_show:
        await interaction.followup.send(embed=embed_to_show, ephemeral=True)

    discord_id = interaction.user.id
    db = DatabaseManager()
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.name, c.name as class_name, p.level, p.experience, gm.rank, gm.join_date
        FROM players p
        JOIN classes c ON p.class_id = c.id
        JOIN guild_members gm ON p.discord_id = gm.discord_id
        WHERE p.discord_id = ?
    """,
        (discord_id,),
    )
    card_data = cur.fetchone()
    conn.close()

    if not card_data:
        await interaction.edit_original_response(
            content=f"{E.ERROR} Error retrieving your Guild Card.",
            embed=None,
            view=None,
        )
        return

    embed = discord.Embed(
        title=f"{E.SCROLL} Guild Card",
        description=f"This card certifies that **{card_data['name']}** is a registered member of The Eldorian Adventurer’s Consortium.",
        color=discord.Color.dark_gold(),
    )
    embed.add_field(name="Class", value=card_data["class_name"], inline=True)
    embed.add_field(name="Rank", value=card_data["rank"], inline=True)
    embed.add_field(name="Level", value=card_data["level"], inline=True)
    embed.add_field(
        name="Experience", value=f"{card_data['experience']} XP", inline=True
    )
    embed.set_footer(text=f"Joined: {card_data['join_date']}")

    view = GuildCardView(db)
    await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
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
        self.quest_system = QuestSystem(self.db)

        # Button 1: View Quests
        quests_button = Button(
            label="View Quests",
            style=discord.ButtonStyle.primary,
            custom_id="view_quests",
            emoji=E.QUEST_SCROLL,
        )
        quests_button.callback = self.view_quests_callback
        self.add_item(quests_button)

        # Button 2: Guild Exchange
        exchange_button = Button(
            label="Guild Exchange",
            style=discord.ButtonStyle.primary,
            custom_id="guild_exchange",
            emoji=E.EXCHANGE,
        )
        exchange_button.callback = self.guild_exchange_callback
        self.add_item(exchange_button)

        # Button 3: Check Rank
        check_rank_button = Button(
            label="Check Rank",
            style=discord.ButtonStyle.secondary,
            custom_id="check_rank",
            emoji=E.MEDAL,
        )
        check_rank_button.callback = self.check_rank_callback
        self.add_item(check_rank_button)

        # Note: The "Promote" button is now GONE from this view.
        # It only appears on the Rank Progress screen if you are eligible.

    async def view_quests_callback(self, interaction: discord.Interaction):
        """
        Displays the quest board with available quests for the player.
        """
        await interaction.response.defer()
        available_quests = self.quest_system.get_available_quests(interaction.user.id)

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

    async def guild_exchange_callback(self, interaction: discord.Interaction):
        """
        Switches to the Guild Exchange view.
        """
        await interaction.response.defer()

        exchange = GuildExchange(self.db)
        total_value, materials = exchange.calculate_exchange_value(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description='A guild receptionist looks up from her ledger. "Greetings, adventurer. Here to exchange your haul for Valis?"\n\nShe tallies your materials...',
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
                value=f"{E.GOLD} **{total_value} Valis**",
                inline=False,
            )

        view = GuildExchangeView(self.db, total_value > 0)
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
# RANK PROGRESS VIEW (NEW)
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
            emoji=E.GOLD,
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
            description=f'The receptionist stamps your ledger. "A fine haul, adventurer. Your payment has been processed."\n\n**Total Earned: {E.GOLD} {total_earned} Valis**',
            color=discord.Color.green(),
        )
        receipt_embed.add_field(name="Sold Materials", value="\n".join(sold_list))

        # Go back to the main guild card, showing the receipt ephemerally
        await back_to_guild_card_callback(interaction, embed_to_show=receipt_embed)


# ======================================================================
# QUEST BOARD VIEWS
# ======================================================================


class QuestBoardView(View):
    """
    Displays the list of available quests.
    """

    def __init__(self, db_manager: DatabaseManager, quests: list):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quests = quests

        for quest in self.quests:
            button = Button(
                label=f"View ID: {quest['id']}", custom_id=f"view_quest_{quest['id']}"
            )
            button.callback = self.view_quest_details_callback
            self.add_item(button)

        back_button = Button(
            label="Back to Guild Card",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_card",
        )
        back_button.callback = back_to_guild_card_callback  # Use the global helper
        self.add_item(back_button)

    async def view_quest_details_callback(self, interaction: discord.Interaction):
        quest_id = int(interaction.data["custom_id"].split("_")[-1])
        quest_system = QuestSystem(self.db)
        quest_details = quest_system.get_quest_details(quest_id)

        if not quest_details:
            await interaction.response.send_message(
                f"{E.ERROR} Could not find details for this quest.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.HERB} Quest: {quest_details['title']}",
            description=quest_details["description"],
            color=discord.Color.dark_teal(),
        )

        objectives_text = ""
        for obj_type, tasks in quest_details["objectives"].items():
            if isinstance(tasks, dict):
                for task, value in tasks.items():
                    objectives_text += f"• **{obj_type.title()}:** {task} ({value})\n"
            else:
                objectives_text += f"• **{obj_type.title()}:** {tasks}\n"

        embed.add_field(name="Objectives", value=objectives_text, inline=False)

        rewards_text = ""
        if "rewards" in quest_details and quest_details["rewards"]:
            for reward, value in quest_details["rewards"].items():
                rewards_text += f"• **{reward.title()}:** {value}\n"
        else:
            rewards_text = "No rewards listed."

        embed.add_field(name="Rewards", value=rewards_text, inline=False)
        embed.set_footer(text=f"Quest ID: {quest_id} | Tier: {quest_details['tier']}")

        view = QuestDetailView(self.db, quest_id)
        await interaction.response.edit_message(embed=embed, view=view)


class QuestDetailView(View):
    """
    Displays the details of a single quest and allows the player to accept it.
    """

    def __init__(self, db_manager: DatabaseManager, quest_id: int):
        super().__init__(timeout=None)
        self.db = db_manager
        self.quest_id = quest_id

        accept_button = Button(
            label="Accept Quest",
            style=discord.ButtonStyle.success,
            custom_id=f"accept_quest_{self.quest_id}",
        )
        accept_button.callback = self.accept_quest_callback
        self.add_item(accept_button)

        back_button = Button(
            label="Back to Quest Board",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_quest_board",
        )
        back_button.callback = self.back_to_quest_board_callback
        self.add_item(back_button)

    async def accept_quest_callback(self, interaction: discord.Interaction):
        quest_system = QuestSystem(self.db)
        success = quest_system.accept_quest(interaction.user.id, self.quest_id)

        if success:
            await interaction.response.send_message(
                "Quest accepted! The Guild seal burns briefly across the parchment, marking your oath.",
                ephemeral=True,
            )
            # Disable the accept button after accepting
            for item in self.children:
                if (
                    isinstance(item, Button)
                    and item.custom_id == f"accept_quest_{self.quest_id}"
                ):
                    item.disabled = True
            await interaction.edit_original_response(view=self)
        else:
            await interaction.response.send_message(
                "You have already accepted this quest or an error occurred.",
                ephemeral=True,
            )

    async def back_to_quest_board_callback(self, interaction: discord.Interaction):
        """
        Returns to the quest board view.
        """
        await interaction.response.defer()
        db = DatabaseManager()  # Need a fresh instance for the new view
        quest_system = QuestSystem(db)
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

        view = QuestBoardView(db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# COG LOADER
# ======================================================================


class GuildCog(commands.Cog):
    """
    A cog for housing all Guild-related Views.
    This cog has no commands, it just makes the Views loadable.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildCog(bot))
