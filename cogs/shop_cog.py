"""
cogs/shop_cog.py

Adventurer's Guild Supply Depot.
Hardened with atomic transactions and non-blocking UI.
Atmosphere restored.
"""

import asyncio
import logging
from typing import Any

import discord
from discord.ext import commands
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.shop_data import SHOP_INVENTORY, SHOP_PURCHASE_LIMITS
from game_systems.items.inventory_manager import InventoryManager

from .utils.ui_helpers import back_to_guild_hall_callback, get_player_or_error

logger = logging.getLogger("eldoria.shop")


class ShopView(View):
    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        current_aurum: int,
        inventory: dict = None,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.current_aurum = current_aurum
        self.inventory = inventory or SHOP_INVENTORY
        self.inv_manager = InventoryManager(self.db)

        self.add_item(self.build_item_select())

        self.back_button = Button(
            label="Return to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def set_back_button(self, callback_function, label="Back"):
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id

    def build_item_select(self) -> Select:
        item_select = Select(placeholder="Select provisions...", min_values=1, max_values=1, row=0)

        if not self.inventory:
            item_select.add_option(label="Out of Stock", value="disabled", emoji=E.ERROR)
            item_select.disabled = True
            return item_select

        # Fetch daily usage
        daily_usage = self.db.get_shop_daily_count(self.interaction_user.id)

        has_stock = False
        has_funds_for_stock = False

        for item_key, price in self.inventory.items():
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                continue

            # Check Daily Limit
            limit = SHOP_PURCHASE_LIMITS.get(item_key, 0)
            used = daily_usage.get(item_key, 0)
            remaining = limit - used if limit > 0 else 999
            is_sold_out = limit > 0 and remaining <= 0

            can_afford = self.current_aurum >= price

            if not is_sold_out:
                has_stock = True
                if can_afford:
                    has_funds_for_stock = True

            # Determine Emoji
            if is_sold_out:
                emoji = E.ERROR
            elif can_afford:
                emoji = E.AURUM
            else:
                emoji = E.LOCKED

            # Determine Label Suffix
            suffix = f" — {price} G"
            if is_sold_out:
                suffix += " [Sold Out]"
            elif not can_afford:
                suffix += " [Too Expensive]"
            elif limit > 0:
                suffix += f" ({remaining}/{limit})"

            # Truncate Name
            name = item_data["name"]
            max_name_len = 100 - len(suffix)
            if len(name) > max_name_len:
                name = name[: max_name_len - 1] + "…"

            item_select.add_option(
                label=f"{name}{suffix}",
                value=f"{item_key}:{price}",
                description=item_data["description"][:50],
                emoji=emoji,
            )

        if not has_stock:
            item_select.placeholder = "Daily Rations Exhausted"
            item_select.disabled = True
        elif not has_funds_for_stock:
            item_select.placeholder = "Insufficient Funds"
            if self.current_aurum == 0:
                item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    def _execute_purchase(self, item_key: str) -> tuple[bool, Any, int]:
        """Atomic purchase transaction."""
        try:
            # SECURITY: Fetch price from server inventory, do not trust client
            price = self.inventory.get(item_key)
            if price is None:
                return (False, "Item not available.", 0)

            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                return (False, "Item data missing.", 0)

            limit = SHOP_PURCHASE_LIMITS.get(item_key, 0)

            # Delegate to DatabaseManager for atomic execution with refund support
            success, result, new_balance = self.db.purchase_item(
                self.interaction_user.id,
                item_key,
                item_data,
                price,
                daily_limit=limit,
            )

            if success:
                logger.info(f"User {self.interaction_user.id} bought {item_key} for {price}")

            return (success, result, new_balance)

        except Exception as e:
            logger.error(f"Purchase error: {e}", exc_info=True)
            return (False, "System error.", 0)

    async def purchase_item_callback(self, interaction: discord.Interaction):
        # Validate player existence first
        if not await get_player_or_error(interaction, self.db):
            return

        await interaction.response.defer()

        # Vulnerability Fix: Ignore client-provided price
        # SECURITY: Ensure values are present and formatted correctly
        values = interaction.data.get("values", [])
        if not values or not isinstance(values, list) or not values[0]:
            await interaction.followup.send("❌ Invalid selection.", ephemeral=True)
            return

        item_key = values[0].split(":")[0]

        success, result, new_aurum = await asyncio.to_thread(self._execute_purchase, item_key)

        # SECURITY FIX: Always fetch fresh stats to prevent stale state.
        # This prevents the UI from showing incorrect balance if it changed externally.
        fresh_player = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        current_aurum = fresh_player["aurum"] if fresh_player else 0

        embed = discord.Embed(
            title="🛒 Guild Supply Depot",
            description=(
                "Within the Adventurer's Guild, this modest counter distributes "
                "the essentials needed for survival beyond the safety of its walls.\n\n"
                f"You currently hold **{current_aurum} {E.AURUM}**."
            ),
            color=discord.Color.green() if success else discord.Color.red(),
        )

        msg = f"{E.CHECK} Secured **1x {result['name']}**." if success else f"{E.ERROR} {result}"
        embed.add_field(name="Transaction Receipt", value=msg)

        new_view = ShopView(self.db, self.interaction_user, current_aurum, self.inventory)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        await interaction.edit_original_response(embed=embed, view=new_view)


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot):
    await bot.add_cog(ShopCog(bot))
