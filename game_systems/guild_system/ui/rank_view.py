"""
game_systems/guild_system/ui/rank_view.py
"""
import discord
import asyncio
from discord.ui import View
from database.database_manager import DatabaseManager
from .components import ViewFactory, GuildViewMixin, SystemCache
from cogs.ui_helpers import back_to_guild_hall_callback

class RankProgressView(View, GuildViewMixin):
    def __init__(self, db_manager: DatabaseManager, eligible: bool, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.rank_system = SystemCache.get_rank_system(db_manager)

        self.promote_btn = ViewFactory.create_button(
            "Request Promotion", discord.ButtonStyle.success, "req_promo", disabled=not eligible,
            callback=self.promote_callback
        )
        self.add_item(self.promote_btn)

        self.back_btn = ViewFactory.create_button(
            "Back to Guild Hall", discord.ButtonStyle.secondary, "back_gh", row=1,
            callback=back_to_guild_hall_callback
        )
        self.add_item(self.back_btn)

    async def promote_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, msg = await asyncio.to_thread(self.rank_system.promote_player, self.interaction_user.id)
        await interaction.followup.send(msg, ephemeral=True)
        
        if success:
            # Try to go back to previous menu
            try: await self.back_btn.callback(interaction)
            except: pass