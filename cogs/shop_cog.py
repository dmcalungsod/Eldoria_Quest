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
from game_systems.items.inventory_manager import InventoryManager

from .ui_helpers import back_to_guild_hall_callback, get_player_or_error

logger = logging.getLogger("eldoria.shop")

SHOP_INVENTORY = {
    "hp_potion_1": 40,
    "mp_potion_1": 40,
    "antidote_basic": 40,
    "smoke_pellet": 45,
    "food_ration": 15,
    "hp_potion_2": 90,
    "mp_potion_2": 90,
    "strength_brew": 120,
    "dex_elixir": 120,
}


class ShopView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User, current_aurum: int):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.current_aurum = current_aurum
        self.inv_manager = InventoryManager(self.db)

        self.add_item(self.build_item_select())

        self.back_button = Button(
            label="Return to Guild Hall", style=discord.ButtonStyle.secondary, custom_id="back_to_guild_hall", row=1
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

        if not SHOP_INVENTORY:
            item_select.add_option(label="Out of Stock", value="disabled", emoji=E.ERROR)
            item_select.disabled = True
            return item_select

        can_afford_any = False
        for item_key, price in SHOP_INVENTORY.items():
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                continue

            can_afford = self.current_aurum >= price
            if can_afford:
                can_afford_any = True

            emoji = E.AURUM if can_afford else E.LOCKED

            # Ensure label does not exceed 100 characters
            suffix = f" — {price} G"
            if not can_afford:
                suffix += " [Too Expensive]"

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

        if not can_afford_any:
            item_select.placeholder = "Insufficient Funds"
            if self.current_aurum == 0:
                item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    def _execute_purchase(self, item_key: str) -> tuple[bool, Any, int]:
        """Atomic purchase transaction."""
        try:
            # SECURITY: Fetch price from server inventory, do not trust client
            price = SHOP_INVENTORY.get(item_key)
            if price is None:
                return (False, "Item not available.", 0)

            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                return (False, "Item data missing.", 0)

            # 1. Atomic Deduction
            new_aurum = self.db.deduct_aurum(self.interaction_user.id, price)
            if new_aurum is None:
                return (False, "Insufficient Aurum.", 0)

            # 2. Add item to inventory
            self.db.add_inventory_item(
                self.interaction_user.id,
                item_key,
                item_data["name"],
                "consumable",
                item_data["rarity"],
                1,
            )

            logger.info(f"User {self.interaction_user.id} bought {item_key} for {price}")
            return (True, item_data, new_aurum)

        except Exception as e:
            logger.error(f"Purchase error: {e}", exc_info=True)
            return (False, "System error.", 0)

    async def purchase_item_callback(self, interaction: discord.Interaction):
        # Validate player existence first
        if not await get_player_or_error(interaction, self.db):
            return

        await interaction.response.defer()

        # Vulnerability Fix: Ignore client-provided price
        item_key = interaction.data["values"][0].split(":")[0]

        success, result, new_aurum = await asyncio.to_thread(self._execute_purchase, item_key)

        embed = discord.Embed(
            title="🛒 Guild Supply Depot",
            description=(
                "Within the Adventurer's Guild, this modest counter distributes "
                "the essentials needed for survival beyond the safety of its walls.\n\n"
                f"You currently hold **{new_aurum if success else self.current_aurum} {E.AURUM}**."
            ),
            color=discord.Color.green() if success else discord.Color.red(),
        )

        msg = f"{E.CHECK} Secured **1x {result['name']}**." if success else f"{E.ERROR} {result}"
        embed.add_field(name="Transaction Receipt", value=msg)

        new_view = ShopView(self.db, self.interaction_user, new_aurum if success else self.current_aurum)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)

        await interaction.edit_original_response(embed=embed, view=new_view)


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot):
    await bot.add_cog(ShopCog(bot))
