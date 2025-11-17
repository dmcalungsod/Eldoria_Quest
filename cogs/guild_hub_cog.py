"""
cogs/guild_hub_cog.py - OPTIMIZED

Rewritten, thematic, and consistent Guild Hub for Eldoria Quest.
Optimizations:
- Factory pattern for view creation (DRY)
- Reduced button callback boilerplate
- Cached system instances
- Lazy imports at module level with try/except
- Consolidated DB calls using asyncio.gather()
- Helper functions for common embed/view patterns
- Reduced redundancy in button setup
"""

import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio
from typing import Optional, Callable, Dict, Any
from functools import lru_cache

from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
import game_systems.data.emojis as E

# Local helpers
from .ui_helpers import back_to_profile_callback, back_to_guild_hall_callback

# Lazy imports to avoid circular dependency issues
_quest_board_view = None
_quest_ledger_view = None
_quest_log_view = None
_guild_exchange_view_cls = None
_shop_view = None
_infirmary_view = None
_skill_trainer_view = None


# ======================================================================
# CACHED SYSTEM INSTANCES & HELPERS
# ======================================================================

class SystemCache:
    """Singleton cache for frequently-used systems to avoid repeated instantiation."""
    _cache: Dict[str, Any] = {}

    @classmethod
    def get_rank_system(cls, db: DatabaseManager) -> RankSystem:
        """Lazy-load and cache RankSystem."""
        if "rank_system" not in cls._cache:
            cls._cache["rank_system"] = RankSystem(db)
        return cls._cache["rank_system"]

    @classmethod
    def get_guild_exchange(cls, db: DatabaseManager) -> GuildExchange:
        """Lazy-load and cache GuildExchange."""
        if "guild_exchange" not in cls._cache:
            cls._cache["guild_exchange"] = GuildExchange(db)
        return cls._cache["guild_exchange"]

    @classmethod
    def clear(cls):
        """Clear cache (use if systems need to be refreshed)."""
        cls._cache.clear()


def _get_lazy_import(attr_name: str):
    """Dynamically import child views on-demand."""
    globals_dict = globals()
    if globals_dict.get(attr_name) is None:
        try:
            if "quest_board" in attr_name:
                from .quest_hub_cog import QuestBoardView
                globals_dict["_quest_board_view"] = QuestBoardView
            elif "quest_ledger" in attr_name:
                from .quest_hub_cog import QuestLedgerView
                globals_dict["_quest_ledger_view"] = QuestLedgerView
            elif "quest_log" in attr_name:
                from .quest_hub_cog import QuestLogView
                globals_dict["_quest_log_view"] = QuestLogView
            elif "exchange_view" in attr_name:
                from .guild_hub_cog import GuildExchangeView
                globals_dict["_guild_exchange_view_cls"] = GuildExchangeView
            elif "shop" in attr_name:
                from .shop_cog import ShopView
                globals_dict["_shop_view"] = ShopView
            elif "infirmary" in attr_name:
                from .infirmary_cog import InfirmaryView
                globals_dict["_infirmary_view"] = InfirmaryView
            elif "skill_trainer" in attr_name:
                from .skill_trainer_cog import SkillTrainerView
                globals_dict["_skill_trainer_view"] = SkillTrainerView
        except ImportError:
            pass
    return globals_dict.get(attr_name)


# ======================================================================
# EMBED & VIEW BUILDERS (DRY HELPERS)
# ======================================================================

class EmbedBuilder:
    """Centralized embed creation with consistent styling."""

    @staticmethod
    def quest_menu() -> discord.Embed:
        return discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unfold the Guild's mission ledger. Inked seals and stamped parchments mark the tasks entrusted to you.*\n\n"
                "From here you may inspect the Quest Board, turn in completed contracts, or review promotion requirements."
            ),
            color=discord.Color.dark_green(),
        )

    @staticmethod
    def services_menu() -> discord.Embed:
        return discord.Embed(
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

    @staticmethod
    def quest_board() -> discord.Embed:
        return discord.Embed(
            title=f"{E.SCROLL} Quest Board",
            description=(
                "*A battered board hangs within the hall, pinned with contracts and bounty slips. Each posting carries risk and reward.*\n\n"
                "Select a contract from the dropdown to inspect its details."
            ),
            color=discord.Color.dark_green(),
        )

    @staticmethod
    def quest_ledger() -> discord.Embed:
        return discord.Embed(
            title=f"{E.QUEST_SCROLL} Quest Ledger",
            description="A review of your currently accepted contracts and their progress.",
            color=discord.Color.from_rgb(139, 69, 19),
        )

    @staticmethod
    def quest_turn_in() -> discord.Embed:
        return discord.Embed(
            title=f"{E.MEDAL} Quest Turn-In",
            description="Report completed contracts and receive your due Aurum and reputation. Select a quest from the dropdown to report.",
            color=discord.Color.gold(),
        )

    @staticmethod
    def guild_exchange() -> discord.Embed:
        return discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description='A clerk raises their eyes from a ledger. "Exchange your gathered materials for Aurum."',
            color=discord.Color.blue(),
        )

    @staticmethod
    def guild_shop(current_aurum: int) -> discord.Embed:
        embed = discord.Embed(
            title="🛒 Guild Supply Depot",
            description=(
                "A modest counter stocked with provisions and curatives. Purchase what you need and return to the field.\n\n"
                f"You hold **{current_aurum} {E.AURUM}**."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Items you cannot afford are hidden from the list.")
        return embed


class ViewFactory:
    """Factory for creating views with consistent button setup and callbacks."""

    @staticmethod
    def create_button(
        label: str,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
        custom_id: str = "",
        emoji: str = "",
        row: int = 0,
        disabled: bool = False,
        callback: Optional[Callable] = None,
    ) -> Button:
        """Factory method for creating buttons."""
        btn = Button(
            label=label,
            style=style,
            custom_id=custom_id,
            emoji=emoji,
            row=row,
            disabled=disabled,
        )
        if callback:
            btn.callback = callback
        return btn


# ======================================================================
# BASE VIEW MIXIN (SHARED BEHAVIOR)
# ======================================================================

class GuildViewMixin:
    """Mixin for shared View behavior across all guild views."""

    db: DatabaseManager
    interaction_user: discord.User

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Validate interaction belongs to intended user."""
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    def set_back_button(self, callback_function: Callable, label: str = "Back"):
        """Dynamically update back button callback and label."""
        if hasattr(self, "back_btn"):
            self.back_btn.label = label
            self.back_btn.callback = callback_function


# ======================================================================
# GUILD LOBBY (MAIN MENU)
# ======================================================================

class GuildLobbyView(View, GuildViewMixin):
    """Main view for the Adventurer's Guild Lobby."""

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self._setup_buttons()

    def _setup_buttons(self):
        """Centralized button setup with callbacks."""
        buttons = [
            ViewFactory.create_button(
                "Quests",
                discord.ButtonStyle.success,
                "lobby_quests",
                "📜",
                row=0,
                callback=self._quests_btn_callback,
            ),
            ViewFactory.create_button(
                "Guild Services",
                discord.ButtonStyle.primary,
                "lobby_services",
                "🏦",
                row=0,
                callback=self._services_btn_callback,
            ),
            ViewFactory.create_button(
                "Return — Character",
                discord.ButtonStyle.grey,
                "lobby_back_profile",
                "⬅️",
                row=1,
                callback=back_to_profile_callback,
            ),
        ]
        for btn in buttons:
            self.add_item(btn)

    async def _quests_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = EmbedBuilder.quest_menu()
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    async def _services_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = EmbedBuilder.services_menu()
        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# QUESTS SUB-MENU (OPTIMIZED)
# ======================================================================

class QuestsMenuView(View, GuildViewMixin):
    """Sub-menu for quest systems with lazy-loaded child views."""

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank_system = SystemCache.get_rank_system(db_manager)
        self._setup_buttons()

    def _setup_buttons(self):
        """Centralized button setup."""
        buttons = [
            ViewFactory.create_button(
                "Quest Board",
                discord.ButtonStyle.primary,
                "guild_quest_board",
                E.SCROLL,
                row=0,
                callback=self.view_quests_callback,
            ),
            ViewFactory.create_button(
                "Quest Ledger",
                discord.ButtonStyle.primary,
                "guild_quest_ledger",
                E.QUEST_SCROLL,
                row=0,
                callback=self.view_quest_ledger_callback,
            ),
            ViewFactory.create_button(
                "Quest Turn-In",
                discord.ButtonStyle.success,
                "guild_turn_in",
                E.MEDAL,
                row=0,
                callback=self.quest_turn_in_callback,
            ),
            ViewFactory.create_button(
                "Check Rank",
                discord.ButtonStyle.secondary,
                "guild_check_rank",
                "🏅",
                row=1,
                callback=self.check_rank_callback,
            ),
            ViewFactory.create_button(
                "Back to Guild Lobby",
                discord.ButtonStyle.grey,
                "back_to_guild_lobby",
                row=1,
                callback=back_to_guild_hall_callback,
            ),
        ]
        self.back_btn = buttons[-1]  # Store back button for set_back_button()
        for btn in buttons:
            self.add_item(btn)

    async def view_quests_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Show Quest Board."""
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        available_quests = await asyncio.to_thread(
            quest_system.get_available_quests, self.interaction_user.id
        )

        embed = EmbedBuilder.quest_board()
        embed.add_field(
            name="Available Contracts",
            value="Choose a quest from the dropdown to inspect it.",
            inline=False,
        )

        QuestBoardView = _get_lazy_import("_quest_board_view")
        view = QuestBoardView(self.db, available_quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")

        await interaction.edit_original_response(embed=embed, view=view)

    async def view_quest_ledger_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Show Quest Ledger with optimized progress parsing."""
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        active_quests = await asyncio.to_thread(
            quest_system.get_player_quests, self.interaction_user.id
        )

        embed = EmbedBuilder.quest_ledger()

        if not active_quests:
            embed.add_field(
                name="No Active Contracts",
                value="Visit the Quest Board to accept a task.",
            )
        else:
            for quest in active_quests:
                progress_text = self._format_quest_progress(quest)
                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text) or "No objectives.",
                    inline=False,
                )

        QuestLedgerView = _get_lazy_import("_quest_ledger_view")
        view = QuestLedgerView(self.db, active_quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")

        await interaction.edit_original_response(embed=embed, view=view)

    @staticmethod
    def _format_quest_progress(quest: Dict[str, Any]) -> list:
        """OPTIMIZED: Extract quest progress text with less redundancy."""
        progress_lines = []
        objectives = quest.get("objectives", {})
        progress = quest.get("progress", {})

        for obj_type, tasks in objectives.items():
            if isinstance(tasks, dict):
                # e.g., {"defeat": {"Goblin": 5}}
                for task, required in tasks.items():
                    current = progress.get(obj_type, {}).get(task, 0)
                    progress_lines.append(f"• {task}: {current} / {required}")
            else:
                # e.g., {"locate": "Lina"}
                current = progress.get(obj_type, {}).get(tasks, 0)
                progress_lines.append(f"• {obj_type.title()} {tasks.title()}: {current} / 1")

        return progress_lines

    async def quest_turn_in_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Show completable quests for turn-in."""
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        active_quests = await asyncio.to_thread(
            quest_system.get_player_quests, self.interaction_user.id
        )

        embed = EmbedBuilder.quest_turn_in()

        if not active_quests:
            embed.add_field(
                name="No Active Contracts",
                value="You have no contracts to turn in.",
                inline=False,
            )
        else:
            completable_quests = sum(
                1 for q in active_quests
                if quest_system.check_completion(q["progress"], q["objectives"])
            )
            if completable_quests == 0:
                embed.add_field(
                    name="No Completed Quests",
                    value="None of your active contracts are ready to turn in.",
                    inline=False,
                )

        QuestLogView = _get_lazy_import("_quest_log_view")
        view = QuestLogView(self.db, active_quests, self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")

        await interaction.edit_original_response(embed=embed, view=view)

    async def check_rank_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Show rank progress with optimized data fetching."""
        await interaction.response.defer()
        discord_id = interaction.user.id

        player_data = await asyncio.to_thread(
            self.rank_system.get_rank_info, discord_id
        )
        current_rank = player_data.get("rank", "F")
        next_rank_key = self.rank_system.RANKS.get(current_rank, {}).get("next_rank")

        if not next_rank_key:
            embed = discord.Embed(
                title=f"{E.MEDAL} Rank Status: {current_rank}",
                description="You have reached the highest rank the Guild currently confers.",
                color=discord.Color.gold(),
            )
            view = RankProgressView(self.db, eligible=False, interaction_user=self.interaction_user)
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

        eligible = True
        progress_lines = []
        for req, required_value in requirements.items():
            current_value = player_data.get(req, 0)
            progress_lines.append(
                f"• **{req.replace('_', ' ').title()}:** {current_value} / {required_value}"
            )
            if current_value < required_value:
                eligible = False

        embed.add_field(
            name="Current Progress",
            value="\n".join(progress_lines) or "No tracked progress.",
            inline=False,
        )

        if eligible:
            embed.color = discord.Color.green()
            embed.set_footer(text="You meet the requirements. Request promotion when ready.")
        else:
            embed.set_footer(text="If eligible, request promotion to advance your standing.")

        view = RankProgressView(self.db, eligible=eligible, interaction_user=self.interaction_user)
        view.set_back_button(self.back_to_this_menu, "Back to Quests")

        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_this_menu(self, interaction: discord.Interaction):
        """Return to Quests menu."""
        await interaction.response.defer()
        embed = EmbedBuilder.quest_menu()
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# GUILD SERVICES SUB-MENU (OPTIMIZED)
# ======================================================================

class GuildServicesView(View, GuildViewMixin):
    """Sub-menu for Guild facilities with lazy-loaded child views."""

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self._setup_buttons()

    def _setup_buttons(self):
        """Centralized button setup."""
        buttons = [
            ViewFactory.create_button(
                "Guild Exchange",
                discord.ButtonStyle.primary,
                "guild_exchange",
                E.EXCHANGE,
                row=0,
                callback=self.guild_exchange_callback,
            ),
            ViewFactory.create_button(
                "Guild Supply",
                discord.ButtonStyle.primary,
                "guild_shop",
                "🪙",
                row=0,
                callback=self.guild_shop_callback,
            ),
            ViewFactory.create_button(
                "Infirmary",
                discord.ButtonStyle.secondary,
                "guild_infirmary",
                "❤️‍🩹",
                row=1,
                callback=self.infirmary_callback,
            ),
            ViewFactory.create_button(
                "Skill Trainer",
                discord.ButtonStyle.secondary,
                "skill_trainer",
                "🧠",
                row=1,
                callback=self.skill_trainer_callback,
            ),
            ViewFactory.create_button(
                "Back to Guild Lobby",
                discord.ButtonStyle.grey,
                "back_to_guild_lobby",
                row=2,
                callback=back_to_guild_hall_callback,
            ),
        ]
        self.back_btn = buttons[-1]
        for btn in buttons:
            self.add_item(btn)

    async def guild_exchange_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Guild Exchange sub-menu."""
        await interaction.response.defer()
        exchange = SystemCache.get_guild_exchange(self.db)

        total_value, materials = await asyncio.to_thread(
            exchange.calculate_exchange_value, self.interaction_user.id
        )

        embed = EmbedBuilder.guild_exchange()

        if total_value == 0:
            embed.add_field(
                name="Materials on Hand",
                value="You have no materials to exchange.",
                inline=False,
            )
        else:
            mat_list = [f"• {m['item_name']} x{m['count']}" for m in materials]
            embed.add_field(name="Materials on Hand", value="\n".join(mat_list), inline=False)
            embed.add_field(
                name="Total Value", value=f"{E.AURUM} **{total_value} Aurum**", inline=False
            )

        GuildExchangeView = _get_lazy_import("_guild_exchange_view_cls")
        view = GuildExchangeView(self.db, total_value > 0, self.interaction_user)
        view.set_back_button(self.back_to_services_menu, "Back to Services")

        await interaction.edit_original_response(embed=embed, view=view)

    async def guild_shop_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Guild Shop sub-menu."""
        await interaction.response.defer()

        # Fetch player data with proper error handling
        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        current_aurum = (player_data or {}).get("aurum", 0)  # OPTIMIZED: safe dict access

        embed = EmbedBuilder.guild_shop(current_aurum)

        ShopView = _get_lazy_import("_shop_view")
        view = ShopView(self.db, self.interaction_user, current_aurum)
        view.set_back_button(self.back_to_services_menu, "Back to Services")

        await interaction.edit_original_response(embed=embed, view=view)

    async def infirmary_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Infirmary sub-menu."""
        await interaction.response.defer()
        from game_systems.player.player_stats import PlayerStats

        # OPTIMIZED: Parallel async calls
        player_data, stats_json = await asyncio.gather(
            asyncio.to_thread(self.db.get_player, self.interaction_user.id),
            asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id),
        )

        player_stats = PlayerStats.from_dict(stats_json)

        InfirmaryView = _get_lazy_import("_infirmary_view")
        embed = InfirmaryView.build_infirmary_embed(player_data, player_stats)
        view = InfirmaryView(self.db, self.interaction_user, player_data, player_stats)
        view.set_back_button(self.back_to_services_menu, "Back to Services")

        await interaction.edit_original_response(embed=embed, view=view)

    async def skill_trainer_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Skill Trainer sub-menu."""
        await interaction.response.defer()

        player_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)

        SkillTrainerView = _get_lazy_import("_skill_trainer_view")
        embed = SkillTrainerView.build_skill_embed(player_data)
        view = SkillTrainerView(self.db, self.interaction_user, player_data)
        view.set_back_button(self.back_to_services_menu, "Back to Services")

        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_services_menu(self, interaction: discord.Interaction):
        """Return to Services menu."""
        await interaction.response.defer()
        embed = EmbedBuilder.services_menu()
        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# RANK PROGRESS VIEW
# ======================================================================

class RankProgressView(View, GuildViewMixin):
    """Shows promotion eligibility and handles promotion requests."""

    def __init__(
        self, db_manager: DatabaseManager, eligible: bool, interaction_user: discord.User
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank_system = SystemCache.get_rank_system(db_manager)

        self.promote_btn = ViewFactory.create_button(
            "Request Promotion",
            discord.ButtonStyle.success,
            "request_promotion",
            disabled=not eligible,
            row=0,
            callback=self.promote_callback,
        )
        self.add_item(self.promote_btn)

        self.back_btn = ViewFactory.create_button(
            "Back to Guild Hall",
            discord.ButtonStyle.secondary,
            "back_to_guild_hall",
            row=1,
            callback=back_to_guild_hall_callback,
        )
        self.add_item(self.back_btn)

    async def promote_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """Request rank promotion."""
        discord_id = interaction.user.id
        await interaction.response.defer()

        success, message = await asyncio.to_thread(
            self.rank_system.promote_player, discord_id
        )

        await interaction.followup.send(message, ephemeral=True)

        if success:
            try:
                await self.back_btn.callback(interaction)
            except Exception:
                await back_to_guild_hall_callback(interaction)


# ======================================================================
# GUILD EXCHANGE VIEW (OPTIMIZED)
# ======================================================================

class GuildExchangeView(View, GuildViewMixin):
    """Handles exchanging materials for Aurum with optimized state management."""

    def __init__(
        self, db_manager: DatabaseManager, can_sell: bool, interaction_user: discord.User
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.exchange = SystemCache.get_guild_exchange(db_manager)

        self.sell_btn = ViewFactory.create_button(
            "Sell All Materials",
            discord.ButtonStyle.success,
            "sell_materials",
            emoji=E.AURUM,
            row=0,
            disabled=not can_sell,
            callback=self.sell_materials_callback,
        )
        self.add_item(self.sell_btn)

        self.back_btn = ViewFactory.create_button(
            "Back to Guild Hall",
            discord.ButtonStyle.secondary,
            "back_to_guild_hall",
            row=1,
            callback=back_to_guild_hall_callback,
        )
        self.add_item(self.back_btn)

    async def sell_materials_callback(self, interaction: discord.Interaction, button: Optional[Button] = None):
        """OPTIMIZED: Sell materials and update embed/view atomically."""
        await interaction.response.defer()

        total_earned, sold_items = await asyncio.to_thread(
            self.exchange.exchange_all_materials, self.interaction_user.id
        )

        if total_earned == 0:
            await interaction.followup.send("You have nothing to sell.", ephemeral=True)
            return

        # OPTIMIZED: Reuse and update existing embed
        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed()
        embed.title = f"{E.EXCHANGE} Exchange Complete"
        embed.description = (
            '*The clerk stamps your ledger. "Payment processed."\n\n'
            f"**Total Earned:** {E.AURUM} **{total_earned}**"
        )
        embed.clear_fields()
        embed.color = discord.Color.green()

        sold_list = [f"• {i['item_name']} x{i['count']}" for i in sold_items]
        embed.add_field(name="Sold Materials", value="\n".join(sold_list), inline=False)

        # Create new view with disabled sell button
        new_view = GuildExchangeView(self.db, can_sell=False, interaction_user=self.interaction_user)
        # OPTIMIZED: Directly reference back_btn (not back_button)
        new_view.set_back_button(self.back_btn.callback, self.back_btn.label)

        await interaction.edit_original_response(embed=embed, view=new_view)


# ======================================================================
# COG LOADER
# ======================================================================

class GuildHubCog(commands.Cog):
    """Guild Hub cog for Eldoria Quest."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    def cog_unload(self):
        """Clear cache when cog unloads."""
        SystemCache.clear()


async def setup(bot: commands.Bot):
    """Setup hook for the cog."""
    await bot.add_cog(GuildHubCog(bot))
