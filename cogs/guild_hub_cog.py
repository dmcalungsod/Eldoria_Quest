"""
guild_hub_cog.py

Handles the main UI hubs for the game.
- GuildLobbyView (The new main Guild menu)
- QuestsMenuView (Quest sub-menu)
- GuildServicesView (Services sub-menu)
- RankProgressView
- GuildExchangeView
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio 

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
# GUILD LOBBY (THE NEW MAIN MENU)
# ======================================================================

class GuildLobbyView(View):
    """
    The new main view for the Guild Lobby.
    This replaces the old GuildCardView.
    Buttons: Quests, Guild Services, Back to Profile
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # --- Row 1: Main Menu Buttons ---
        self.add_item(Button(
            label="Quests",
            style=discord.ButtonStyle.success,
            custom_id="lobby_quests",
            emoji="📜",
            row=0
        ))
        self.add_item(Button(
            label="Guild Services",
            style=discord.ButtonStyle.primary,
            custom_id="lobby_services",
            emoji="🏦",
            row=0
        ))
        
        # --- Row 2: Navigation ---
        back_btn = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="lobby_back_profile",
            emoji="⬅️",
            row=1
        )
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        
        # --- Handle button routing ---
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "lobby_quests":
            await self.quests_menu_callback(interaction)
            return False # Stop further processing
            
        if custom_id == "lobby_services":
            await self.guild_services_menu_callback(interaction)
            return False # Stop further processing

        # Allow interaction to proceed (for back_to_profile_callback)
        return True

    async def quests_menu_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Quest sub-menu.
        """
        await interaction.response.defer()
        # THIS IS YOUR NEW THEMATIC EMBED
        embed = discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unfold the Guild’s mission ledger. Inked seals, stamped parchments, and "
                "weathered entries detail the labors of countless adventurers before you.*\n\n"
                "From here, you may review your duties, track your progress, or pursue new "
                "assignments sanctioned by the Guild."
            ),
            color=discord.Color.dark_green()
        )

        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_services_menu_callback(self, interaction: discord.Interaction):
        """
        Edits the message to show the Guild Services sub-menu.
        """
        await interaction.response.defer()
        # THIS IS YOUR NEW THEMATIC EMBED
        embed = discord.Embed(
            title="🏦 Guild Services",
            description=(
                "*You step into the Guild’s service hall, where lanternlight dances across "
                "stone walls and clerks work in quiet precision.*\n"
                "*Ledgers, sigils, and sealed documents fill the counters—this is the heart of "
                "the Guild’s economy and infrastructure.*\n\n"
                "**Available Services:**\n"
                "• **Guild Exchange** — Trade materials, relics, and rare findings.\n"
                "• **Guild Shop** — Acquire sanctioned gear and adventuring supplies.\n"
                "• **Infirmary** — Receive medical care and restore your strength.\n"
                "• **Skill Trainer** — Refine your abilities and advance your craft."
            ),
            color=discord.Color.dark_blue()
        )

        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)



# ======================================================================
# QUESTS SUB-MENU
# ======================================================================

class QuestsMenuView(View):
    """
    The sub-menu for all quest-related activities.
    Buttons: Quest Board, Quest Turn-In, Check Rank
    """
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)
        self.interaction_user = interaction_user
        
        # --- Add Back Button ---
        back_btn = Button(
            label="Back to Guild Lobby",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=1
        )
        back_btn.callback = back_to_guild_hall_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

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
        
        available_quests = await asyncio.to_thread(
            quest_system.get_available_quests, self.interaction_user.id
        )

        # THIS IS YOUR NEW THEMATIC EMBED
        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description=(
                "*A vast wooden board dominates the hall, crowded with torn parchments, "
                "fresh postings, and blood-stamped contracts. Candlelight flickers across "
                "the edges of each sheet, casting shifting shadows over the quests awaiting "
                "a willing adventurer.*\n\n"
                "New assignments, bounties, and Guild-sanctioned contracts are posted here."
            ),
            color=discord.Color.dark_green(),
        )

        embed.add_field(
            name="Available Contracts",
            value="Choose a quest from the dropdown to inspect its details.",
            inline=False,
        )

        view = QuestBoardView(self.db, available_quests, self.interaction_user)
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
        
        active_quests = await asyncio.to_thread(
            quest_system.get_player_quests, self.interaction_user.id
        )

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
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Lobby")
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Check Rank",
        style=discord.ButtonStyle.secondary,
        custom_id="guild_rank",
        emoji=E.MEDAL,
        row=0,
    )
    async def check_rank_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Rank Progress UI.
        """
        await interaction.response.defer()
        discord_id = interaction.user.id
        
        player_data = await asyncio.to_thread(self.rank_system.get_rank_info, discord_id)
        
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
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Lobby") # Set back button
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# GUILD SERVICES SUB-MENU
# ======================================================================

class GuildServicesView(View):
    """
    The sub-menu for all guild facilities and economy.
    Buttons: Exchange, Shop, Infirmary, Skill Trainer
    """
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        
        # --- Add Back Button ---
        back_btn = Button(
            label="Back to Guild Lobby",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_hall",
            row=2 # Place below the other 4 buttons
        )
        back_btn.callback = back_to_guild_hall_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

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
        
        total_value, materials = await asyncio.to_thread(
            exchange.calculate_exchange_value, self.interaction_user.id
        )

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
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Lobby") # Set back button
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Guild Shop",
        style=discord.ButtonStyle.primary,
        custom_id="guild_shop",
        emoji="🪙",
        row=0,
    )
    async def guild_shop_callback(self, interaction: discord.Interaction, button: Button):
        """
        Edits the message to show the new Guild Shop UI.
        """
        await interaction.response.defer()
        
        from .shop_cog import ShopView
        
        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        
        current_aurum = player_data['aurum'] if player_data else 0

        embed = discord.Embed(
            title=f"Guild Shop",
            description=f"Welcome to the Guild's public shop. Spend your hard-earned Aurum.\n\nYou have: {current_aurum} {E.AURUM}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Items you can't afford are not shown in the dropdown.")
        
        view = ShopView(self.db, self.interaction_user, current_aurum)
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Lobby") # Set back button
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Infirmary",
        style=discord.ButtonStyle.secondary,
        custom_id="guild_infirmary",
        emoji="❤️‍🩹",
        row=1,
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
        
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)
        
        embed = InfirmaryView.build_infirmary_embed(player_data, player_stats)
        view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        view.set_back_button(back_to_guild_hall_callback, "Back to Guild Lobby") # Set back button
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Skill Trainer",
        style=discord.ButtonStyle.secondary,
        custom_id="skill_trainer",
        emoji="🧠",
        row=1,
    )
    async def skill_trainer_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the new Skill Trainer UI.
        """
        await interaction.response.defer()
        
        from .skill_trainer_cog import SkillTrainerView
        
        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        
        embed = SkillTrainerView.build_skill_embed(player_data)
        view = SkillTrainerView(self.db, self.interaction_user, player_data)
        
        # Set the back button to point to the Guild Lobby
        view.back_button.callback = back_to_guild_hall_callback
        view.back_button.label = "Back to Guild Lobby"
        await interaction.edit_original_response(embed=embed, view=view)


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

        self.back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    # New helper to allow parent view to change the back button
    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function

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
        
        success, message = await asyncio.to_thread(
            rank_system.promote_player, discord_id
        )

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

        self.back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)
        
    # New helper to allow parent view to change the back button
    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def sell_materials_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        total_earned, sold_items = await asyncio.to_thread(
            self.exchange.exchange_all_materials, self.interaction_user.id
        )

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