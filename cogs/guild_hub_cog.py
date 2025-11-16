"""
guild_hub_cog.py

Handles the main UI hubs for the game.
- GuildCardView (The Guild sub-menu)
- RankProgressView
- GuildExchangeView
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio # <-- IMPORT ASYNCIO

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback, back_to_guild_hall_callback

# --- View Imports ---
from .quest_hub_cog import QuestBoardView, QuestLogView

# Note: CharacterProfileView, InventoryView, and SkillsView have been
# moved to character_cog.py


# ======================================================================
# GUILD CARD (THE NEW SUB-MENU)
# ======================================================================


class GuildCardView(View):
    """
    The view for the player's Guild Card. This is a sub-menu.
    Buttons: Quest Board, Guild Exchange, Quest Turn In, Guild Rank, Back
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)
        self.interaction_user = interaction_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    # --- (Row 1 buttons) ---
    @discord.ui.button(
        label="Quest Board",
        style=discord.ButtonStyle.primary,
        custom_id="guild_quests",
        emoji=E.HERB,
        row=0,
    )
    async def view_quests_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Quest Board UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        
        # --- ASYNC FIX ---
        available_quests = await asyncio.to_thread(
            quest_system.get_available_quests, self.interaction_user.id
        )
        # --- END FIX ---

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description="The board is cluttered with parchment sheets...",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="Available Contracts",
            value="Select an available quest from the dropdown menu.",
        )
        view = QuestBoardView(self.db, available_quests, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Guild Exchange",
        style=discord.ButtonStyle.primary,
        custom_id="guild_exchange",
        emoji=E.EXCHANGE,
        row=0,
    )
    async def guild_exchange_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Guild Exchange UI.
        """
        await interaction.response.defer()
        exchange = GuildExchange(self.db)
        
        # --- ASYNC FIX ---
        total_value, materials = await asyncio.to_thread(
            exchange.calculate_exchange_value, self.interaction_user.id
        )
        # --- END FIX ---

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

        view = GuildExchangeView(self.db, total_value > 0, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Quest Turn-In",
        style=discord.ButtonStyle.primary,
        custom_id="guild_turn_in",
        emoji=E.QUEST_SCROLL,
        row=0,
    )
    async def quest_turn_in_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Quest Log / Turn-In UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        
        # --- ASYNC FIX ---
        active_quests = await asyncio.to_thread(
            quest_system.get_player_quests, self.interaction_user.id
        )
        # --- END FIX ---

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Quest Turn-In",
            description="Report on your completed assignments to the Guild.",
            color=discord.Color.from_rgb(139, 69, 19),
        )
        if not active_quests:
            embed.add_field(
                name="No Active Quests", value="Visit the Quest Board to accept a task."
            )

        view = QuestLogView(self.db, active_quests, self.interaction_user)
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Hall")
        await interaction.edit_original_response(embed=embed, view=view)

    # --- (Row 2 buttons) ---
    
    @discord.ui.button(
        label="Guild Shop",
        style=discord.ButtonStyle.secondary,
        custom_id="guild_shop",
        emoji="🪙",
        row=1,
    )
    async def guild_shop_callback(self, interaction: discord.Interaction, button: Button):
        """
        Edits the message to show the new Guild Shop UI.
        """
        await interaction.response.defer()
        
        from .shop_cog import ShopView
        
        # --- ASYNC FIX ---
        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        # --- END FIX ---
        
        current_aurum = player_data['aurum'] if player_data else 0

        embed = discord.Embed(
            title=f"Guild Shop",
            description=f"Welcome to the Guild's public shop. Spend your hard-earned Aurum.\n\nYou have: {current_aurum} {E.AURUM}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Items you can't afford are not shown in the dropdown.")
        
        view = ShopView(self.db, self.interaction_user, current_aurum)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Check Rank",
        style=discord.ButtonStyle.secondary,
        custom_id="guild_rank",
        emoji=E.MEDAL,
        row=1,
    )
    async def check_rank_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Rank Progress UI.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        
        # --- ASYNC FIX ---
        player_data = await asyncio.to_thread(self.rank_system.get_rank_info, discord_id)
        # --- END FIX ---
        
        current_rank = player_data["rank"]
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have reached the highest rank.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(
                self.db, eligible=False, interaction_user=self.interaction_user
            )
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

        view = RankProgressView(
            self.db, eligible=eligible, interaction_user=self.interaction_user
        )
        await interaction.edit_original_response(embed=embed, view=view)

    # --- THIS IS THE NEW BUTTON (ROW 2) ---
    @discord.ui.button(
        label="Infirmary",
        style=discord.ButtonStyle.secondary,
        custom_id="guild_infirmary",
        emoji="❤️‍🩹",
        row=2,
    )
    async def infirmary_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the new Guild Infirmary UI.
        """
        await interaction.response.defer()
        
        from .infirmary_cog import InfirmaryView
        from game_systems.player.player_stats import PlayerStats
        
        # We need both player data (for aurum/current_hp) and stats (for max_hp)
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)
        
        embed = InfirmaryView.build_infirmary_embed(player_data, player_stats)
        view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        await interaction.edit_original_response(embed=embed, view=view)
    # --- END OF NEW BUTTON ---

    @discord.ui.button(
        label="Skill Trainer",
        style=discord.ButtonStyle.secondary,
        custom_id="skill_trainer",
        emoji="🧠",
        row=3, # Moved to row 3
    )
    async def skill_trainer_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the new Skill Trainer UI.
        """
        await interaction.response.defer()
        
        from .skill_trainer_cog import SkillTrainerView
        
        # --- ASYNC FIX ---
        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        # --- END FIX ---
        
        embed = SkillTrainerView.build_skill_embed(player_data)
        view = SkillTrainerView(self.db, self.interaction_user, player_data)
        await interaction.edit_original_response(embed=embed, view=view)


    @discord.ui.button(
        label="Back to Profile",
        style=discord.ButtonStyle.grey,
        custom_id="guild_back_profile",
        emoji="⬅️",
        row=3, # Moved to row 3
    )
    async def back_to_profile(self, interaction: discord.Interaction, button: Button):
        # This function is already async!
        await back_to_profile_callback(interaction)


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================


class RankProgressView(View):
    """
    Shows promotion eligibility and the "Promote" button.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        eligible: bool,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def promote_callback(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        rank_system = RankSystem(self.db)
        
        await interaction.response.defer()
        
        # --- ASYNC FIX ---
        success, message = await asyncio.to_thread(
            rank_system.promote_player, discord_id
        )
        # --- END FIX ---

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

    def __init__(
        self,
        db_manager: DatabaseManager,
        can_sell: bool,
        interaction_user: discord.User,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.exchange = GuildExchange(self.db) # Create instance

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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def sell_materials_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # --- ASYNC FIX ---
        total_earned, sold_items = await asyncio.to_thread(
            self.exchange.exchange_all_materials, self.interaction_user.id
        )
        # --- END FIX ---

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

        # Send ephemeral receipt, then go back
        await interaction.followup.send(embed=receipt_embed, ephemeral=True)
        await back_to_guild_hall_callback(interaction)


# ======================================================================
# COG LOADER
# ======================================================================


class GuildHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildHubCog(bot))