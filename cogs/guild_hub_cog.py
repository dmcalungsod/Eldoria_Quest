"""
guild_hub_cog.py

Handles the main UI hubs for the game.
- CharacterProfileView (The NEW main menu)
- GuildCardView (The Guild sub-menu)
- RankProgressView
- GuildExchangeView
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback, back_to_guild_hall_callback

# --- View Imports ---
from .quest_hub_cog import QuestBoardView, QuestLogView
from .adventure_commands import AdventureSetupView


# ======================================================================
# CHARACTER PROFILE (THE NEW MAIN MENU)
# ======================================================================


class CharacterProfileView(View):
    """
    The main character profile screen. This is the new "home" UI.
    Buttons: Inventory, Skills, Quest Log, Start Adventure, Guild
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.inventory_manager = InventoryManager(self.db)

        # --- Row 1: Character ---
        inventory_button = Button(
            label="Inventory",
            style=discord.ButtonStyle.secondary,
            custom_id="profile_inventory",
            emoji=E.BACKPACK,
        )
        inventory_button.callback = self.inventory_callback
        self.add_item(inventory_button)

        skills_button = Button(
            label="Skills",
            style=discord.ButtonStyle.secondary,
            custom_id="profile_skills",
            emoji="✨",
        )
        skills_button.callback = self.skills_callback
        self.add_item(skills_button)

        quest_log_button = Button(
            label="Quest Log",
            style=discord.ButtonStyle.primary,
            custom_id="profile_quest_log",
            emoji=E.QUEST_SCROLL,
        )
        quest_log_button.callback = self.quest_log_callback
        self.add_item(quest_log_button)

        # --- Row 2: Actions ---
        start_adventure_button = Button(
            label="Start Adventure",
            style=discord.ButtonStyle.success,
            custom_id="profile_start_adventure",
            emoji=E.MAP,
        )
        start_adventure_button.callback = self.start_adventure_callback
        self.add_item(start_adventure_button)

        guild_button = Button(
            label="Guild Hall",
            style=discord.ButtonStyle.primary,
            custom_id="profile_guild_hall",
            emoji="🛡️",
        )
        guild_button.callback = self.guild_hall_callback
        self.add_item(guild_button)

    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Inventory UI.
        """
        await interaction.response.defer()
        items = self.inventory_manager.get_inventory(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.BACKPACK} Backpack", color=discord.Color.brown()
        )

        categories = {}
        for item in items:
            itype = item["item_type"].title()
            if itype not in categories:
                categories[itype] = []
            categories[itype].append(f"• {item['item_name']} (x{item['count']})")

        if not categories:
            embed.description = "Your backpack is empty."
        else:
            for category, item_list in categories.items():
                embed.add_field(name=category, value="\n".join(item_list), inline=False)

        view = InventoryView(self.db)
        await interaction.edit_original_response(embed=embed, view=view)

    async def skills_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Skills UI.
        """
        await interaction.response.defer()
        player_skills = self.db.get_player_skills(interaction.user.id)

        if not player_skills:
            skills_str = "You have not learned any skills."
        else:
            skills_str = "\n".join(
                [
                    f"• **{s['name']}** (Lv. {s['skill_level']}) - *{s['type']}*"
                    for s in player_skills
                ]
            )

        embed = discord.Embed(
            title="Acquired Skills",
            description=skills_str,
            color=discord.Color.purple(),
        )

        view = SkillsView(self.db)
        await interaction.edit_original_response(embed=embed, view=view)

    async def quest_log_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Quest Log UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        active_quests = quest_system.get_player_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventurer's Log",
            description="A review of your currently accepted assignments.",
            color=discord.Color.from_rgb(139, 69, 19),
        )
        if not active_quests:
            embed.add_field(
                name="No Active Quests",
                value="Visit the Guild Hall Quest Board to accept a task.",
            )
        else:
            for quest in active_quests:
                progress_text = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})
                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        for task, required in tasks.items():
                            current = progress.get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text) or "No objectives.",
                    inline=False,
                )

        view = QuestLogView(self.db, active_quests, interaction.user.id)
        # Default back button on this view goes to Profile
        view.set_back_button(back_to_profile_callback, "Back to Profile")
        await interaction.edit_original_response(embed=embed, view=view)

    async def start_adventure_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Adventure Setup (location picker) UI.
        """
        adventure_cog = interaction.client.get_cog("AdventureCommands")
        if not adventure_cog:
            await interaction.response.send_message(
                f"{E.ERROR} Adventure system is offline.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description="You stand before the city gates, the Guild's clearance seal in your hand. The wilderness beyond the walls of Ashgrave awaits.\n\nSelect a destination.",
            color=discord.Color.dark_green(),
        )
        view = AdventureSetupView(self.db, adventure_cog.manager)
        await interaction.response.edit_message(embed=embed, view=view)

    async def guild_hall_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Guild Hall (sub-menu) UI.
        """
        await back_to_guild_hall_callback(interaction)


# ======================================================================
# INVENTORY & SKILLS VIEWS (NEW)
# ======================================================================


class InventoryView(View):
    """
    A simple view that just shows the "Back to Profile" button.
    The embed itself contains all the inventory info.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)


class SkillsView(View):
    """
    A simple view that just shows the "Back to Profile" button.
    The embed itself contains all the skills info.
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager

        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)


# ======================================================================
# GUILD CARD (THE NEW SUB-MENU)
# ======================================================================


class GuildCardView(View):
    """
    The view for the player's Guild Card. This is a sub-menu.
    Buttons: Quest Board, Guild Exchange, Quest Turn In, Guild Rank, Back
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)

        # --- Row 1: Guild Services ---
        quests_button = Button(
            label="Quest Board",
            style=discord.ButtonStyle.primary,
            custom_id="guild_quests",
            emoji=E.HERB,
        )
        quests_button.callback = self.view_quests_callback
        self.add_item(quests_button)

        exchange_button = Button(
            label="Guild Exchange",
            style=discord.ButtonStyle.primary,
            custom_id="guild_exchange",
            emoji=E.EXCHANGE,
        )
        exchange_button.callback = self.guild_exchange_callback
        self.add_item(exchange_button)

        turn_in_button = Button(
            label="Quest Turn-In",
            style=discord.ButtonStyle.primary,
            custom_id="guild_turn_in",
            emoji=E.QUEST_SCROLL,
        )
        turn_in_button.callback = self.quest_turn_in_callback
        self.add_item(turn_in_button)

        # --- Row 2: Administration ---
        check_rank_button = Button(
            label="Check Rank",
            style=discord.ButtonStyle.secondary,
            custom_id="guild_rank",
            emoji=E.MEDAL,
        )
        check_rank_button.callback = self.check_rank_callback
        self.add_item(check_rank_button)

        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="guild_back_profile",
            emoji="⬅️",
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)

    async def view_quests_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Quest Board UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        available_quests = quest_system.get_available_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets...",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="Available Contracts",
            value="Select an available quest from the dropdown menu.",
        )
        view = QuestBoardView(self.db, available_quests)
        await interaction.edit_original_response(embed=embed, view=view)

    async def quest_turn_in_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Quest Log / Turn-In UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        active_quests = quest_system.get_player_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Quest Turn-In",
            description="Report on your completed assignments to the Guild.",
            color=discord.Color.from_rgb(139, 69, 19),
        )
        if not active_quests:
            embed.add_field(
                name="No Active Quests",
                value="Visit the Quest Board to accept a task.",
            )

        view = QuestLogView(self.db, active_quests, interaction.user.id)
        # We pass a flag to the QuestLogView to change its "Back" button
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Hall")
        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_exchange_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Guild Exchange UI.
        """
        await interaction.response.defer()
        exchange = GuildExchange(self.db)
        total_value, materials = exchange.calculate_exchange_value(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description=f'A guild receptionist looks up from her ledger. "Here to exchange your haul for Aurum?"',
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

    async def check_rank_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Rank Progress UI.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        player_data = self.rank_system.get_rank_info(discord_id)
        current_rank = player_data["rank"]
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have reached the highest rank.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(self.db, eligible=False)
            await interaction.edit_original_response(embed=embed, view=view)
            return

        requirements = self.rank_system.RANKS[current_rank].get("requirements", {})
        next_rank_title = self.rank_system.RANKS[next_rank_key]["title"]
        embed = discord.Embed(
            title=f"{E.MEDAL} Promotion Evaluation: {current_rank} → {next_rank_key}",
            description=f"Your progress towards the rank of **{next_rank_title}**.",
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
            embed.set_footer(text="You are eligible for promotion!")
        else:
            embed.set_footer(text="Continue your efforts, adventurer.")

        view = RankProgressView(self.db, eligible=eligible)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================


class RankProgressView(View):
    """
    Shows promotion eligibility and the "Promote" button.
    """

    def __init__(self, db_manager: DatabaseManager, eligible: bool):
        super().__init__(timeout=None)
        self.db = db_manager

        promote_button = Button(
            label="Request Promotion",
            style=discord.ButtonStyle.success,
            custom_id="promote",
            disabled=not eligible,
        )
        promote_button.callback = self.promote_callback
        self.add_item(promote_button)

        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def promote_callback(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        rank_system = RankSystem(self.db)
        success, message = rank_system.promote_player(discord_id)

        await interaction.response.defer()
        await interaction.followup.send(message, ephemeral=True)

        if success:
            await back_to_guild_hall_callback(interaction)  # Refresh the guild hall


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

        sell_button = Button(
            label="Sell All Materials",
            style=discord.ButtonStyle.success,
            custom_id="sell_mats",
            disabled=not can_sell,
            emoji=E.AURUM,
        )
        sell_button.callback = self.sell_materials_callback
        self.add_item(sell_button)

        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def sell_materials_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        exchange = GuildExchange(self.db)
        total_earned, sold_items = exchange.exchange_all_materials(interaction.user.id)

        if total_earned == 0:
            await interaction.followup.send("You have nothing to sell.", ephemeral=True)
            return

        sold_list = [f"• {item['item_name']} x{item['count']}" for item in sold_items]
        receipt_embed = discord.Embed(
            title=f"{E.EXCHANGE} Exchange Complete",
            description=f'The receptionist stamps your ledger. "A fine haul... your payment has been processed."\n\n**Total Earned: {E.AURUM} {total_earned} Aurum**',
            color=discord.Color.green(),
        )
        receipt_embed.add_field(name="Sold Materials", value="\n".join(sold_list))

        # Go back to the Guild Hall, showing the receipt ephemerally
        await back_to_guild_hall_callback(interaction, embed_to_show=receipt_embed)


# ======================================================================
# COG LOADER
# ======================================================================


class GuildHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))
