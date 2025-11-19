"""
cogs/shop_cog.py

Adventurer’s Guild Supply Depot.
Hardened with atomic transactions and non-blocking UI.
"""

import asyncio
import logging
from typing import Any, Tuple

import discord
from discord.ext import commands
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.items.inventory_manager import InventoryManager
from .ui_helpers import back_to_guild_hall_callback

logger = logging.getLogger("eldoria.shop")

SHOP_INVENTORY = {
    "hp_potion_1": 15, "mp_potion_1": 15, "antidote_basic": 25,
    "smoke_pellet": 30, "food_ration": 10, "hp_potion_2": 50,
    "mp_potion_2": 50, "strength_brew": 75, "dex_elixir": 75,
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
            label="Return to Guild Hall", style=discord.ButtonStyle.secondary, 
            custom_id="back_to_guild_hall", row=1
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
            if not item_data: continue

            if self.current_aurum >= price: can_afford_any = True

            item_select.add_option(
                label=f"{item_data['name']} — {price} G",
                value=f"{item_key}:{price}",
                description=item_data["description"][:50],
                emoji="🪙"
            )

        if not can_afford_any:
            item_select.placeholder = "Insufficient Funds"
            if self.current_aurum == 0: item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    def _execute_purchase(self, item_key: str, price: int) -> Tuple[bool, Any, int]:
        """Atomic purchase transaction."""
        try:
            item_data = CONSUMABLES.get(item_key)
            if not item_data: return (False, "Item data missing.", 0)

            with self.db.get_connection() as conn:
                # Lock & Check Funds
                row = conn.execute("SELECT aurum FROM players WHERE discord_id = ?", (self.interaction_user.id,)).fetchone()
                if not row or row["aurum"] < price:
                    return (False, "Insufficient Aurum.", 0)

                new_aurum = row["aurum"] - price
                
                # Deduct Funds
                conn.execute("UPDATE players SET aurum = ? WHERE discord_id = ?", (new_aurum, self.interaction_user.id))
                
                # Add Item (Inline logic to keep transaction atomic)
                existing = conn.execute(
                    "SELECT id FROM inventory WHERE discord_id=? AND item_key=? AND rarity=? AND equipped=0 LIMIT 1",
                    (self.interaction_user.id, item_key, item_data["rarity"])
                ).fetchone()

                if existing:
                    conn.execute("UPDATE inventory SET count=count+1 WHERE id=?", (existing["id"],))
                else:
                    conn.execute(
                        "INSERT INTO inventory (discord_id, item_key, item_name, item_type, rarity, count, equipped) VALUES (?, ?, ?, 'consumable', ?, 1, 0)",
                        (self.interaction_user.id, item_key, item_data["name"], item_data["rarity"])
                    )

            logger.info(f"User {self.interaction_user.id} bought {item_key} for {price}")
            return (True, item_data, new_aurum)

        except Exception as e:
            logger.error(f"Purchase error: {e}", exc_info=True)
            return (False, "System error.", 0)

    async def purchase_item_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        item_key, price_str = interaction.data["values"][0].split(":")
        price = int(price_str)

        success, result, new_aurum = await asyncio.to_thread(self._execute_purchase, item_key, price)

        embed = discord.Embed(
            title="🛒 Guild Supply",
            description=f"**Funds:** {new_aurum if success else self.current_aurum} {E.AURUM}",
            color=discord.Color.green() if success else discord.Color.red()
        )
        
        msg = f"{E.CHECK} Purchased **{result['name']}**." if success else f"{E.ERROR} {result}"
        embed.add_field(name="Receipt", value=msg)

        new_view = ShopView(self.db, self.interaction_user, new_aurum if success else self.current_aurum)
        new_view.set_back_button(self.back_button.callback, self.back_button.label)
        
        await interaction.edit_original_response(embed=embed, view=new_view)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()

async def setup(bot):
    await bot.add_cog(ShopCog(bot))