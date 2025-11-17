"""
game_systems/guild_system/ui/lobby_view.py
The main entry point for the Guild Hall.
"""

import discord
from discord.ui import View
from database.database_manager import DatabaseManager

from .components import ViewFactory, GuildViewMixin, EmbedBuilder
from cogs.ui_helpers import back_to_profile_callback

# Lazy imports inside methods to avoid circular deps
# from .quests_menu import QuestsMenuView
# from .services_menu import GuildServicesView

class GuildLobbyView(View, GuildViewMixin):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self._setup_buttons()

    def _setup_buttons(self):
        self.add_item(ViewFactory.create_button(
            "Quests", discord.ButtonStyle.success, "lobby_quests", "📜", 0, 
            callback=self._quests_btn_callback
        ))
        self.add_item(ViewFactory.create_button(
            "Guild Services", discord.ButtonStyle.primary, "lobby_services", "🏦", 0,
            callback=self._services_btn_callback
        ))
        self.add_item(ViewFactory.create_button(
            "Return — Character", discord.ButtonStyle.grey, "lobby_back_profile", "⬅️", 1,
            callback=back_to_profile_callback
        ))

    async def _quests_btn_callback(self, interaction: discord.Interaction):
        from .quests_menu import QuestsMenuView
        await interaction.response.defer()
        view = QuestsMenuView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=EmbedBuilder.quest_menu(), view=view)

    async def _services_btn_callback(self, interaction: discord.Interaction):
        from .services_menu import GuildServicesView
        await interaction.response.defer()
        view = GuildServicesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=EmbedBuilder.services_menu(), view=view)