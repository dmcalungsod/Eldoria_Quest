"""
game_systems/guild_system/ui/exchange_view.py

The Guild Exchange interface.
Hardened: Uses threaded database calls for material exchange to prevent bot freeze.
"""

import asyncio
import logging
import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_guild_hall_callback
from database.database_manager import DatabaseManager
from .components import GuildViewMixin, SystemCache, ViewFactory

logger = logging.getLogger("eldoria.ui.exchange")


class GuildExchangeView(View, GuildViewMixin):
    def __init__(self, db_manager: DatabaseManager, can_sell: bool, interaction_user: discord.User):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.exchange = SystemCache.get_guild_exchange(db_manager)

        # Sell Button
        self.sell_btn = ViewFactory.create_button(
            "Sell All Materials",
            discord.ButtonStyle.success,
            "sell_all",
            E.AURUM,
            disabled=not can_sell,
            callback=self.sell_callback,
        )
        self.add_item(self.sell_btn)

        # Back Button
        self.back_btn = ViewFactory.create_button(
            "Back to Hall", 
            discord.ButtonStyle.secondary, 
            "back_gh", 
            row=1, 
            callback=back_to_guild_hall_callback
        )
        self.add_item(self.back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This exchange is not for you.", ephemeral=True)
            return False
        return True

    async def sell_callback(self, interaction: discord.Interaction, button: Button = None):
        """
        Executes the sale of all materials.
        """
        await interaction.response.defer()

        try:
            # Run the atomic transaction in a thread
            earned, items = await asyncio.to_thread(self.exchange.exchange_all_materials, self.interaction_user.id)

            if earned == 0:
                await interaction.followup.send("No materials to sell.", ephemeral=True)
                return

            # Rebuild the embed with results
            embed = interaction.message.embeds[0]
            embed.title = "Exchange Complete"
            embed.description = f"Sold materials for **{earned} {E.AURUM}**."
            embed.clear_fields()

            # List sold items
            if items:
                # Limit display to prevent embed errors
                rows = [f"• {i['item_name']} x{i['count']}" for i in items[:15]]
                if len(items) > 15:
                    rows.append(f"...and {len(items) - 15} more.")
                embed.add_field(name="Receipt", value="\n".join(rows))
            
            embed.color = discord.Color.green()

            # Refresh view (Disable sell button since items are gone)
            new_view = GuildExchangeView(self.db, False, self.interaction_user)
            
            # Preserve back button state
            if hasattr(self, 'back_btn'):
                new_view.set_back_button(self.back_btn.callback, self.back_btn.label)

            await interaction.edit_original_response(embed=embed, view=new_view)
            logger.info(f"User {self.interaction_user.id} sold items for {earned} gold.")

        except Exception as e:
            logger.error(f"Exchange UI error for {self.interaction_user.id}: {e}", exc_info=True)
            await interaction.followup.send("An error occurred during the exchange.", ephemeral=True)