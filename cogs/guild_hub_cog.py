"""
cogs/guild_hub_cog.py

Rewritten, thematic, and consistent Guild Hub for Eldoria Quest.

- GuildLobbyView (Main Guild menu)
- QuestsMenuView (Quest sub-menu)
- GuildServicesView (Services sub-menu)
- RankProgressView
- GuildExchangeView

All embeds and button labels use the Adventurer's Guild tone (grim, pragmatic, survivalist).
Database calls are executed off the event loop where appropriate.
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio
from typing import Optional

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
import game_systems.data.emojis as E

# Local helpers
from .ui_helpers import back_to_profile_callback, back_to_guild_hall_callback

# View imports (imported at runtime in callbacks to avoid circular imports)
# from .quest_hub_cog import QuestBoardView, QuestLogView  (imported inside functions)


# ======================================================================
# GUILD LOBBY (MAIN MENU)
# ======================================================================

class GuildLobbyView(View):
    """
    Main view for the Adventurer's Guild Lobby.
    Presents the player with gateway options: Quests, Services, Profile.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # --- Buttons (added as Items so they can be assigned callbacks) ---
        self.quests_btn = Button(
            label="Quests",
            style=discord.ButtonStyle.success,
            custom_id="lobby_quests",
            emoji="📜",
            row=0,
        )
        self.quests_btn.callback = self._quests_btn_callback
        self.add_item(self.quests_btn)

        self.services_btn = Button(
            label="Guild Services",
            style=discord.ButtonStyle.primary,
            custom_id="lobby_services",
            emoji="🏦",
            row=0,
        )
        self.services_btn.callback = self._services_btn_callback
        self.add_item(self.services_btn)

        self.back_btn = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="lobby_back_profile",
            emoji="⬅️",
            row=1,
        )
        self.back_btn.callback = back_to_profile_callback
        self.add_item(self.back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    # --- Button callbacks delegate to async helpers ---

    async def _quests_btn_callback(self, interaction: discord.Interaction):
        await self.quests_menu_callback(interaction)

    async def _services_btn_callback(self, interaction: discord.Interaction):
        await self.guild_services_menu_callback(interaction)

    # --- Menu builders ---

    async def quests_menu_callback(self, interaction: discord.Interaction):
        """
        Show the Quests sub-menu.
        """
        await interaction.response.defer()

        embed = discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unfold the Guild’s mission ledger. Inked seals and stamped parchments mark the tasks entrusted to you.*\n\n"
                "From here you may inspect the Quest Board, turn in completed contracts, or review promotion requirements."
            ),
            color=discord.Color.dark_green(),
        )

        from .guild_hub_cog import QuestsMenuView as LocalQuestsMenuView  # type: ignore
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_services_menu_callback(self, interaction: discord.Interaction):
        """
        Show the Guild Services sub-menu.
        """
        await interaction.response.defer()

        embed = discord.Embed(
            title="🏦 Guild Services",
            description=(
                "*Lanternlight slides across service counters and ledgers. The Guild maintains many practical services — "
                "each intended to keep you alive for the next contract.*\n\n"
                "**Available Services:**\n"
                "• **Guild Exchange** — Trade gathered materials for Aurum.\n"
                "• **Guild Supply** — Purchase provisions and curatives.\n"
                "• **Infirmary** — Receive medical treatment.\n"
                "• **Skill Trainer** — Refine techniques and learn new arts."
            ),
            color=discord.Color.dark_blue(),
        )

        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# QUESTS SUB-MENU
# ======================================================================

class QuestsMenuView(View):
    """
    Sub-menu for the Guild's quest systems.
    Buttons: Quest Board, Quest Turn-In, Check Rank, Back.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.rank_system = RankSystem(self.db)
        self.interaction_user = interaction_user

        # --- THIS IS THE FIX ---

        # Button 1: Quest Board
        self.quest_board_btn = Button(
            label="Quest Board",
            style=discord.ButtonStyle.primary,
            custom_id="guild_quest_board",
            emoji=E.SCROLL,
            row=0,
        )
        self.quest_board_btn.callback = self.view_quests_callback
        self.add_item(self.quest_board_btn)

        # Button 2: Quest Ledger (View Only)
        self.quest_ledger_btn = Button(
            label="Quest Ledger",
            style=discord.ButtonStyle.primary,
            custom_id="guild_quest_ledger",
            emoji=E.QUEST_SCROLL,
            row=0,
        )
        self.quest_ledger_btn.callback = self.view_quest_ledger_callback
        self.add_item(self.quest_ledger_btn)

        # Button 3: Quest Turn-In
        self.turn_in_btn = Button(
            label="Quest Turn-In",
            style=discord.ButtonStyle.success, # Changed style
            custom_id="guild_turn_in",
            emoji=E.MEDAL, # Changed emoji
            row=0,
        )
        self.turn_in_btn.callback = self.quest_turn_in_callback
        self.add_item(self.turn_in_btn)

        # Button 4: Check Rank
        self.check_rank_btn = Button(
            label="Check Rank",
            style=discord.ButtonStyle.secondary,
            custom_id="guild_check_rank",
            emoji="🏅",
            row=1, # Moved to row 1
        )
        self.check_rank_btn.callback = self.check_rank_callback
        self.add_item(self.check_rank_btn)

        # Button 5: Back
        self.back_btn = Button(
            label="Back to Guild Lobby",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_lobby",
            row=1,
        )
        self.back_btn.callback = back_to_guild_hall_callback
        self.add_item(self.back_btn)
        
        # --- END OF FIX ---

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    # -------------------------
    # Quest Board
    # -------------------------
    async def view_quests_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from .quest_hub_cog import QuestBoardView  # imported here to avoid circular import
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        available_quests = await asyncio.to_thread(quest_system.get_available_quests, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description=(
                "*A battered board hangs within the hall, pinned with contracts and bounty slips. Each posting carries risk and reward.*\n\n"
                "Select a contract from the dropdown to inspect its details."
            ),
            color=discord.Color.dark_green(),
        )

        embed.add_field(name="Available Contracts", value="Choose a quest from the dropdown to inspect it.", inline=False)

        view = QuestBoardView(self.db, available_quests, self.interaction_user)
        # Make sure QuestBoardView's back returns to this menu if supported
        try:
            view.set_back_button(self.back_to_this_menu, "Back to Quests")
        except Exception:
            # ignore if the child view doesn't support set_back_button
            pass

        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Quest Ledger (NEW CALLBACK)
    # -------------------------
    async def view_quest_ledger_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem
        from .quest_hub_cog import QuestLedgerView # Import our new view

        quest_system = QuestSystem(self.db)
        active_quests = await asyncio.to_thread(quest_system.get_player_quests, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Quest Ledger",
            description="A review of your currently accepted contracts and their progress.",
            color=discord.Color.from_rgb(139, 69, 19), # Brown color
        )

        if not active_quests:
            embed.add_field(
                name="No Active Contracts",
                value="Visit the Quest Board to accept a task.",
            )
        else:
            for quest in active_quests:
                progress_text = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})
                
                # --- THIS IS THE FIX ---
                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        # This handles {"defeat": {"Goblin": 5}}
                        for task, required in tasks.items():
                            current = progress.get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                    else:
                        # This handles {"locate": "Lina"}
                        task = tasks  # task is "Lina"
                        required = 1  # required is 1
                        current = progress.get(obj_type, {}).get(task, 0)
                        # --- THIS IS THE LINE TO FIX ---
                        progress_text.append(f"• {obj_type.title()} {task.title()}: {current} / {required}")
                        # --- END OF LINE TO FIX ---
                # --- END OF FIX ---
                        
                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text) or "No objectives.",
                    inline=False,
                )
        
        view = QuestLedgerView(self.db, active_quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")
        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Quest Turn-In
    # -------------------------
    async def quest_turn_in_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem
        from .quest_hub_cog import QuestLogView

        quest_system = QuestSystem(self.db)
        active_quests = await asyncio.to_thread(quest_system.get_player_quests, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.MEDAL} Quest Turn-In",
            description="Report completed contracts and receive your due Aurum and reputation. Select a quest from the dropdown to report.",
            color=discord.Color.gold(), # Gold color for rewards
        )
        
        # We still build the list of *all* active quests for the QuestLogView
        if not active_quests:
            embed.add_field(name="No Active Contracts", value="You have no contracts to turn in.", inline=False)
        else:
            # This list is for the *dropdown*, which only shows completable quests
            completable_quests = 0
            for quest in active_quests:
                 if quest_system.check_completion(quest["progress"], quest["objectives"]):
                     completable_quests += 1
            
            if completable_quests == 0:
                 embed.add_field(name="No Completed Quests", value="None of your active contracts are ready to turn in.", inline=False)


        view = QuestLogView(self.db, active_quests, self.interaction_user)
        # ensure child view's back returns to this menu
        try:
            view.set_back_button(self.back_to_this_menu, "Back to Quests")
        except Exception:
            pass

        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Rank Check
    # -------------------------
    async def check_rank_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        discord_id = interaction.user.id

        player_data = await asyncio.to_thread(self.rank_system.get_rank_info, discord_id)
        current_rank = player_data.get("rank", "F")
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have reached the highest rank the Guild currently confers.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(self.db, eligible=False, interaction_user=self.interaction_user)
            # set back to this menu
            view.set_back_button(self.back_to_this_menu, "Back to Quests")
            await interaction.edit_original_response(embed=embed, view=view)
            return

        requirements = self.rank_system.RANKS[current_rank].get("requirements", {})
        next_rank_title = self.rank_system.RANKS[next_rank_key]["title"]

        embed = discord.Embed(
            title=f"{E.MEDAL} Promotion Evaluation: {current_rank} → {next_rank_key}",
            description=f"Progress toward the title **{next_rank_title}**.",
            color=discord.Color.blue(),
        )

        progress_text = ""
        eligible = True
        for req, required_value in requirements.items():
            current_value = player_data.get(req, 0)
            progress_text += f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}\n"
            if current_value < required_value:
                eligible = False

        embed.add_field(name="Current Progress", value=progress_text or "No tracked progress.", inline=False)
        embed.set_footer(text="If eligible, request promotion to advance your standing.")

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(text="You meet the requirements. Request promotion when ready.")

        view = RankProgressView(self.db, eligible=eligible, interaction_user=self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")
        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Helper: return to this menu
    # -------------------------
    async def back_to_this_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unfold the Guild’s mission ledger. Inked seals and stamped parchments mark the tasks entrusted to you.*\n\n"
                "From here you may inspect the Quest Board, turn in completed contracts, or review promotion requirements."
            ),
            color=discord.Color.dark_green(),
        )
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# GUILD SERVICES SUB-MENU
# ======================================================================

class GuildServicesView(View):
    """
    Sub-menu for Guild facilities: Exchange, Shop, Infirmary, Skill Trainer.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        # Service buttons
        self.exchange_btn = Button(
            label="Guild Exchange",
            style=discord.ButtonStyle.primary,
            custom_id="guild_exchange",
            emoji=E.EXCHANGE,
            row=0,
        )
        self.exchange_btn.callback = self.guild_exchange_callback
        self.add_item(self.exchange_btn)

        self.shop_btn = Button(
            label="Guild Supply",
            style=discord.ButtonStyle.primary,
            custom_id="guild_shop",
            emoji="🪙",
            row=0,
        )
        self.shop_btn.callback = self.guild_shop_callback
        self.add_item(self.shop_btn)

        self.infirmary_btn = Button(
            label="Infirmary",
            style=discord.ButtonStyle.secondary,
            custom_id="guild_infirmary",
            emoji="❤️‍🩹",
            row=1,
        )
        self.infirmary_btn.callback = self.infirmary_callback
        self.add_item(self.infirmary_btn)

        self.trainer_btn = Button(
            label="Skill Trainer",
            style=discord.ButtonStyle.secondary,
            custom_id="skill_trainer",
            emoji="🧠",
            row=1,
        )
        self.trainer_btn.callback = self.skill_trainer_callback
        self.add_item(self.trainer_btn)

        # Back
        self.back_btn = Button(
            label="Back to Guild Lobby",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_guild_lobby",
            row=2,
        )
        self.back_btn.callback = back_to_guild_hall_callback
        self.add_item(self.back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    # -------------------------
    # Guild Exchange
    # -------------------------
    async def guild_exchange_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        exchange = GuildExchange(self.db)

        total_value, materials = await asyncio.to_thread(exchange.calculate_exchange_value, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description='A clerk raises their eyes from a ledger. "Exchange your gathered materials for Aurum."',
            color=discord.Color.blue(),
        )

        if total_value == 0:
            embed.add_field(name="Materials on Hand", value="You have no materials to exchange.", inline=False)
        else:
            mat_list = [f"• {m['item_name']} x{m['count']}" for m in materials]
            embed.add_field(name="Materials on Hand", value="\n".join(mat_list), inline=False)
            embed.add_field(name="Total Value", value=f"{E.AURUM} **{total_value} Aurum**", inline=False)

        from .guild_hub_cog import GuildExchangeView as LocalExchangeView  # type: ignore
        view = GuildExchangeView(self.db, total_value > 0, self.interaction_user)
        # ensure Back goes to Services menu
        view.set_back_button(self.back_to_services_menu, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Guild Shop
    # -------------------------
    async def guild_shop_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from .shop_cog import ShopView

        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        
        # --- THIS IS THE FIX ---
        # Changed .get("aurum", 0) to ["aurum"]
        current_aurum = player_data["aurum"] if player_data else 0
        # --- END OF FIX ---

        embed = discord.Embed(
            title="🛒 Guild Supply Depot",
            description=(
                "A modest counter stocked with provisions and curatives. Purchase what you need and return to the field.\n\n"
                f"You hold **{current_aurum} {E.AURUM}**."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Items you cannot afford are hidden from the list.")

        view = ShopView(self.db, self.interaction_user, current_aurum)
        view.set_back_button(self.back_to_services_menu, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Infirmary
    # -------------------------
    async def infirmary_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from .infirmary_cog import InfirmaryView
        from game_systems.player.player_stats import PlayerStats

        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)

        embed = InfirmaryView.build_infirmary_embed(player_data, player_stats)
        view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        view.set_back_button(self.back_to_services_menu, "Back to Services")
        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Skill Trainer
    # -------------------------
    async def skill_trainer_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()
        from .skill_trainer_cog import SkillTrainerView

        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)

        embed = SkillTrainerView.build_skill_embed(player_data)
        view = SkillTrainerView(self.db, self.interaction_user, player_data)
        # Make sure back returns here
        try:
            view.back_button.callback = self.back_to_services_menu
            view.back_button.label = "Back to Services"
        except Exception:
            pass

        await interaction.edit_original_response(embed=embed, view=view)

    # -------------------------
    # Helper: return to services menu
    # -------------------------
    async def back_to_services_menu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(
            title="🏦 Guild Services",
            description=(
                "*Lanternlight slides across service counters and ledgers. The Guild maintains many practical services — "
                "each intended to keep you alive for the next contract.*\n\n"
                "**Available Services:**\n"
                "• **Guild Exchange** — Trade gathered materials for Aurum.\n"
                "• **Guild Supply** — Purchase provisions and curatives.\n"
                "• **Infirmary** — Receive medical treatment.\n"
                "• **Skill Trainer** — Refine techniques and learn new arts."
            ),
            color=discord.Color.dark_blue(),
        )
        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================

class RankProgressView(View):
    """
    Shows promotion eligibility and contains the 'Request Promotion' button.
    """

    def __init__(self, db_manager: DatabaseManager, eligible: bool, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        self.promote_btn = Button(
            label="Request Promotion",
            style=discord.ButtonStyle.success,
            custom_id="request_promotion",
            disabled=not eligible,
            row=0,
        )
        self.promote_btn.callback = self.promote_callback
        self.add_item(self.promote_btn)

        self.back_btn = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_btn.callback = back_to_guild_hall_callback
        self.add_item(self.back_btn)

    def set_back_button(self, callback_function, label="Back"):
        self.back_btn.label = label
        self.back_btn.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def promote_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        discord_id = interaction.user.id
        rank_system = RankSystem(self.db)

        await interaction.response.defer()
        success, message = await asyncio.to_thread(rank_system.promote_player, discord_id)

        await interaction.followup.send(message, ephemeral=True)

        if success:
            # If parent overwrote back button, call it to navigate back
            try:
                await self.back_btn.callback(interaction)
            except Exception:
                # fallback: go to guild lobby
                await back_to_guild_hall_callback(interaction)


# ======================================================================
# GUILD EXCHANGE VIEW
# ======================================================================

class GuildExchangeView(View):
    """
    View that handles exchanging materials for Aurum.
    """

    def __init__(self, db_manager: DatabaseManager, can_sell: bool, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.exchange = GuildExchange(self.db)

        self.sell_btn = Button(
            label="Sell All Materials",
            style=discord.ButtonStyle.success,
            custom_id="sell_materials",
            disabled=not can_sell,
            emoji=E.AURUM,
            row=0,
        )
        self.sell_btn.callback = self.sell_materials_callback
        self.add_item(self.sell_btn)

        self.back_btn = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_btn.callback = back_to_guild_hall_callback
        self.add_item(self.back_btn)

    def set_back_button(self, callback_function, label="Back"):
        self.back_btn.label = label
        self.back_btn.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def sell_materials_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        await interaction.response.defer()

        total_earned, sold_items = await asyncio.to_thread(self.exchange.exchange_all_materials, self.interaction_user.id)

        if total_earned == 0:
            await interaction.followup.send("You have nothing to sell.", ephemeral=True)
            return

        sold_list = [f"• {i['item_name']} x{i['count']}" for i in sold_items]
        receipt = discord.Embed(
            title=f"{E.EXCHANGE} Exchange Complete",
            description=(
                'The clerk stamps your ledger. "Payment processed."\n\n'
                f"**Total Earned:** {E.AURUM} **{total_earned}**"
            ),
            color=discord.Color.green(),
        )
        receipt.add_field(name="Sold Materials", value="\n".join(sold_list), inline=False)

        await interaction.followup.send(embed=receipt, ephemeral=True)

        # attempt to return to parent menu via back btn callback
        try:
            await self.back_btn.callback(interaction)
        except Exception:
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