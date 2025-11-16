"""
shop_cog.py

Handles the Guild Shop UI:
- Lists consumables for sale
- Handles the purchase transaction (Aurum debit, item credit)
"""

import discord
from discord.ui import View, Button, Select
from discord.ext import commands
import asyncio # <-- IMPORT ASYNCIO
from typing import Tuple, Dict, Any # For type hinting

from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.data.consumables import CONSUMABLES
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback

# --- Shop Price List ---
# We define the prices here. (item_key: price)
# You can adjust these prices as you see fit.
SHOP_INVENTORY = {
    "hp_potion_1": 15,  # Dewfall Tonic
    "mp_potion_1": 15,  # Scholar's Draught
    "antidote_basic": 25,  # Thicket Antidote
    "smoke_pellet": 30,  # Whisper-Cloud Pellet
    "food_ration": 10,  # Trailman's Ration
    "hp_potion_2": 50,  # Glade Salve Vial
    "mp_potion_2": 50,  # Lunaris Tonic
    "strength_brew": 75,  # Captains' Ale
    "dex_elixir": 75,  # Starlit Tincture
}


class ShopView(View):
    """
    The main UI for the Guild Shop.
    Displays current Aurum and a dropdown of items to buy.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        current_aurum: int,
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.current_aurum = current_aurum
        self.inv_manager = InventoryManager(self.db)

        # Build the dropdown
        self.add_item(self.build_item_select())

        # Add the back button
        back_button = Button(
            label="Back to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        back_button.callback = back_to_guild_hall_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your shop.", ephemeral=True
            )
            return False
        return True

    def build_item_select(self) -> Select:
        """Creates the Select dropdown for shop items."""
        item_select = Select(
            placeholder="Choose an item to purchase...",
            min_values=1,
            max_values=1,
            row=0,
        )

        if not SHOP_INVENTORY:
            item_select.add_option(
                label="The shop is currently empty.", value="disabled", emoji=E.ERROR
            )
            item_select.disabled = True
            return item_select

        can_afford_any = False
        for item_key, price in SHOP_INVENTORY.items():
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                continue

            if self.current_aurum >= price:
                can_afford_any = True
            
            item_select.add_option(
                label=f"{item_data['name']} ({price} {E.AURUM})",
                value=f"{item_key}:{price}",  # Pass both key and price
                description=item_data["description"][:100],
                emoji="🧪",
                # Don't disable the option, check on callback
            )

        if not can_afford_any and self.current_aurum > 0:
            item_select.placeholder = "You cannot afford any items."
        elif self.current_aurum == 0:
            item_select.placeholder = "You have no Aurum to spend."
            item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    # --- NEW HELPER FUNCTION FOR ASYNC ---
    def _execute_purchase(self, item_key: str, price: int) -> Tuple[bool, Any, int]:
        """
        Runs the blocking DB transaction.
        Returns (success, item_data, new_aurum)
        """
        item_data = CONSUMABLES.get(item_key)
        if not item_data:
            return (False, "Item data not found.", 0)

        # 1. Transaction Check
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT aurum FROM players WHERE discord_id = ?", (self.interaction_user.id,))
            player_data = cur.fetchone()

            if not player_data or player_data["aurum"] < price:
                return (False, f"You do not have enough {E.AURUM} for this item.", 0)

            # 2. Debit Aurum
            new_aurum = player_data["aurum"] - price
            cur.execute(
                "UPDATE players SET aurum = ? WHERE discord_id = ?",
                (new_aurum, self.interaction_user.id),
            )
            
            # 3. Credit Item (run in a separate thread later)
        
        return (True, item_data, new_aurum)
    # --- END HELPER ---

    async def purchase_item_callback(self, interaction: discord.Interaction):
        """
        Handles the logic for purchasing a single item.
        """
        await interaction.response.defer()

        item_key, price_str = interaction.data["values"][0].split(":")
        price = int(price_str)
        
        # --- ASYNC FIX ---
        # Run the DB transaction in a thread
        success, result, new_aurum = await asyncio.to_thread(
            self._execute_purchase, item_key, price
        )
        # --- END FIX ---

        if not success:
            # 'result' contains the error message
            await interaction.followup.send(f"{E.ERROR} {result}", ephemeral=True)
            return
        
        # 'result' contains the item_data
        item_data = result
        
        # --- ASYNC FIX ---
        # Run the inventory write in a separate thread
        await asyncio.to_thread(
            self.inv_manager.add_item,
            self.interaction_user.id,
            item_key,
            item_data["name"],
            "consumable",
            item_data["rarity"],
            1
        )
        # --- END FIX ---

        await interaction.followup.send(
            f"{E.CHECK} You purchased 1x {item_data['name']} for {price} {E.AURUM}.",
            ephemeral=True,
        )

        # Re-build the embed and view with new Aurum total
        new_embed = discord.Embed(
            title=f"Guild Shop",
            description=f"Welcome to the Guild's public shop. Spend your hard-earned Aurum.\n\nYou have: {new_aurum} {E.AURUM}",
            color=discord.Color.green(),
        )
        new_view = ShopView(self.db, self.interaction_user, new_aurum)
        await interaction.edit_original_response(embed=new_embed, view=new_view)


# ======================================================================
# COG LOADER
# ======================================================================


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))