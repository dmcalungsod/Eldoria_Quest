"""
game_systems/guild_system/ui/exchange_view.py
"""
import discord
import asyncio
import game_systems.data.emojis as E
from discord.ui import View, Button
from database.database_manager import DatabaseManager
from .components import ViewFactory, GuildViewMixin, SystemCache
from cogs.ui_helpers import back_to_guild_hall_callback

class GuildExchangeView(View, GuildViewMixin):
    def __init__(self, db_manager: DatabaseManager, can_sell: bool, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.exchange = SystemCache.get_guild_exchange(db_manager)

        self.sell_btn = ViewFactory.create_button(
            "Sell All", discord.ButtonStyle.success, "sell_all", E.AURUM, disabled=not can_sell,
            callback=self.sell_callback
        )
        self.add_item(self.sell_btn)

        self.back_btn = ViewFactory.create_button(
            "Back to Hall", discord.ButtonStyle.secondary, "back_gh", row=1,
            callback=back_to_guild_hall_callback
        )
        self.add_item(self.back_btn)

    async def sell_callback(self, interaction: discord.Interaction, button: Button = None):
        await interaction.response.defer()
        earned, items = await asyncio.to_thread(self.exchange.exchange_all_materials, self.interaction_user.id)
        
        if earned == 0:
            await interaction.followup.send("Nothing to sell.", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.title = "Exchange Complete"
        embed.description = f"Sold materials for **{earned} Aurum**."
        embed.clear_fields()
        
        rows = [f"• {i['item_name']} x{i['count']}" for i in items]
        embed.add_field(name="Receipt", value="\n".join(rows))
        embed.color = discord.Color.green()

        new_view = GuildExchangeView(self.db, False, self.interaction_user)
        new_view.set_back_button(self.back_btn.callback, self.back_btn.label)
        await interaction.edit_original_response(embed=embed, view=new_view)