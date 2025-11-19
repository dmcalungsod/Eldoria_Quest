"""
game_systems/guild_system/ui/components.py

Shared UI components, factories, and cached systems used throughout
Guild-related views.
Hardened: Logging added, robust interaction checks.
"""

import logging
from typing import Any, Callable, Dict, Optional

import discord
from discord.ui import Button

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.guild_system.guild_exchange import GuildExchange
from game_systems.guild_system.rank_system import RankSystem

logger = logging.getLogger("eldoria.guild_ui")


# ======================================================
# System Cache
# ======================================================


class SystemCache:
    """
    Singleton-style cache for frequently accessed systems.
    Prevents recreating heavy objects on every button click.
    """

    _cache: Dict[str, Any] = {}

    @classmethod
    def get_rank_system(cls, db: DatabaseManager) -> RankSystem:
        """Returns a cached RankSystem instance, creating it if needed."""
        if "rank_system" not in cls._cache:
            cls._cache["rank_system"] = RankSystem(db)
        return cls._cache["rank_system"]

    @classmethod
    def get_guild_exchange(cls, db: DatabaseManager) -> GuildExchange:
        """Returns a cached GuildExchange instance, creating it if needed."""
        if "guild_exchange" not in cls._cache:
            cls._cache["guild_exchange"] = GuildExchange(db)
        return cls._cache["guild_exchange"]

    @classmethod
    def clear(cls):
        """Clears all cached systems."""
        logger.debug("Clearing SystemCache.")
        cls._cache.clear()


# ======================================================
# Shared View Mixin
# ======================================================


class GuildViewMixin:
    """Mixin providing standardized interaction checks and back-button logic."""

    db: DatabaseManager
    interaction_user: discord.User
    back_btn: Button

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Restricts interaction to the user who opened the view.
        """
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This menu isn't yours to interact with.",
                ephemeral=True,
            )
            return False
        return True

    def set_back_button(self, callback_function: Callable, label: str = "Back"):
        """
        Updates the label and callback of a pre-existing back button.
        """
        if hasattr(self, "back_btn"):
            self.back_btn.label = label
            self.back_btn.callback = callback_function


# ======================================================
# Button Factory
# ======================================================


class ViewFactory:
    """Factory methods for producing standardized UI components."""

    @staticmethod
    def create_button(
        label: str,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
        custom_id: str = "",
        emoji: Optional[str] = None,
        row: int = 0,
        disabled: bool = False,
        callback: Optional[Callable] = None,
    ) -> Button:
        """
        Creates a button with optional preset callback behavior.
        """
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


# ======================================================
# Embed Templates
# ======================================================


class EmbedBuilder:
    """Centralized embed templates for Guild menus."""

    @staticmethod
    def quest_menu() -> discord.Embed:
        return discord.Embed(
            title=f"{E.SCROLL} Quests & Assignments",
            description=(
                "*You unroll the Guild's mission ledger. Intricate seals denote active contracts.*\n\n"
                "Browse the Quest Board, submit completed tasks, or review your promotion standing."
            ),
            color=discord.Color.dark_green(),
        )

    @staticmethod
    def services_menu() -> discord.Embed:
        return discord.Embed(
            title="🏦 Guild Services",
            description=(
                "*The Guild offers a suite of services designed to keep its members alive and capable.*\n\n"
                "**Available Services:**\n"
                "• **Guild Exchange** — Trade materials for Aurum.\n"
                "• **Guild Supply** — Purchase provisions.\n"
                "• **Infirmary** — Receive medical treatment.\n"
                "• **Skill Trainer** — Train and acquire new abilities."
            ),
            color=discord.Color.dark_blue(),
        )

    @staticmethod
    def guild_exchange() -> discord.Embed:
        return discord.Embed(
            title=f"{E.EXCHANGE} Guild Exchange",
            description=(
                'A clerk glances up from their ledger. "If you have materials to trade, I can exchange them for Aurum."'
            ),
            color=discord.Color.blue(),
        )