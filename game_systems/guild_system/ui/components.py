"""
game_systems/guild_system/ui/components.py
Shared UI components, factories, and caching for Guild Views.
"""

import discord
from discord.ui import Button
from typing import Optional, Callable, Dict, Any
from database.database_manager import DatabaseManager
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.guild_exchange import GuildExchange
import game_systems.data.emojis as E


class SystemCache:
    """Singleton cache for frequently-used systems."""
    _cache: Dict[str, Any] = {}

    @classmethod
    def get_rank_system(cls, db: DatabaseManager) -> RankSystem:
        if "rank_system" not in cls._cache:
            cls._cache["rank_system"] = RankSystem(db)
        return cls._cache["rank_system"]

    @classmethod
    def get_guild_exchange(cls, db: DatabaseManager) -> GuildExchange:
        if "guild_exchange" not in cls._cache:
            cls._cache["guild_exchange"] = GuildExchange(db)
        return cls._cache["guild_exchange"]

    @classmethod
    def clear(cls):
        cls._cache.clear()


class GuildViewMixin:
    """Mixin for shared View behavior."""
    db: DatabaseManager
    interaction_user: discord.User
    back_btn: Button

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    def set_back_button(self, callback_function: Callable, label: str = "Back"):
        if hasattr(self, "back_btn"):
            self.back_btn.label = label
            self.back_btn.callback = callback_function


class ViewFactory:
    """Factory for creating consistent buttons."""
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
        btn = Button(
            label=label, style=style, custom_id=custom_id,
            emoji=emoji, row=row, disabled=disabled
        )
        if callback:
            btn.callback = callback
        return btn


class EmbedBuilder:
    """Centralized embed text for Guild menus."""
    
    @staticmethod
    def quest_menu() -> discord.Embed:
        return discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unfold the Guild's mission ledger. Inked seals mark the tasks entrusted to you.*\n\n"
                "Inspect the Quest Board, turn in contracts, or review promotion requirements."
            ),
            color=discord.Color.dark_green(),
        )

    @staticmethod
    def services_menu() -> discord.Embed:
        return discord.Embed(
            title="🏦 Guild Services",
            description=(
                "*The Guild maintains many practical services intended to keep you alive.*\n\n"
                "**Available Services:**\n"
                "• **Guild Exchange** — Trade materials for Aurum.\n"
                "• **Guild Supply** — Purchase provisions.\n"
                "• **Infirmary** — Medical treatment.\n"
                "• **Skill Trainer** — Learn new arts."
            ),
            color=discord.Color.dark_blue(),
        )

    @staticmethod
    def guild_exchange() -> discord.Embed:
        return discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description='A clerk raises their eyes. "Exchange your gathered materials for Aurum."',
            color=discord.Color.blue(),
        )