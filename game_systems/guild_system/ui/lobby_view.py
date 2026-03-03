"""
game_systems/guild_system/ui/lobby_view.py
The main entry point for the Guild Hall.
Hardened: Async loading and circular import protection.
"""

import asyncio

import discord
from discord.ui import View

from cogs.utils.ui_helpers import back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.guild_system.advisor import GuildAdvisor

from .components import EmbedBuilder, GuildViewMixin, ViewFactory


class GuildLobbyView(View, GuildViewMixin):
    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        rank: str = "F",
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank = rank
        self._setup_buttons()

    def _setup_buttons(self):
        self.add_item(
            ViewFactory.create_button(
                "Quests",
                discord.ButtonStyle.success,
                "lobby_quests",
                "📜",
                0,
                callback=self._quests_btn_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Guild Services",
                discord.ButtonStyle.primary,
                "lobby_services",
                "🏦",
                0,
                callback=self._services_btn_callback,
            )
        )
        self.add_item(
            ViewFactory.create_button(
                "Return — Character",
                discord.ButtonStyle.grey,
                "lobby_back_profile",
                "⬅️",
                1,
                callback=back_to_profile_callback,
            )
        )

        # New Player Advisor Button (Rank F and E only)
        if self.rank in ["F", "E"]:
            self.add_item(
                ViewFactory.create_button(
                    "Advisor",
                    discord.ButtonStyle.secondary,
                    "lobby_advisor",
                    "🗣️",
                    1,
                    callback=self._advisor_callback,
                )
            )

    async def _quests_btn_callback(self, interaction: discord.Interaction):
        from .quests_menu import QuestsMenuView

        await interaction.response.defer()
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(
            embed=EmbedBuilder.quest_menu(), view=view
        )

    async def _services_btn_callback(self, interaction: discord.Interaction):
        from game_systems.core.world_time import TimePhase, WorldTime

        from .services_menu import GuildServicesView

        await interaction.response.defer()
        view = GuildServicesView(self.db, self.interaction_user)

        dynamic_flavor = ""
        if WorldTime.get_current_phase() == TimePhase.NIGHT:
            dynamic_flavor = "🌙 *The sun has set. The Mystic Merchant has arrived under the cover of darkness.*"

        await interaction.edit_original_response(
            embed=EmbedBuilder.services_menu(dynamic_flavor=dynamic_flavor), view=view
        )

    async def _advisor_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        advisor = GuildAdvisor(self.db, self.interaction_user.id)

        # For Rank F/E, show the interactive checklist
        embed = await asyncio.to_thread(advisor.get_checklist_embed)
        await interaction.followup.send(embed=embed, ephemeral=True)
