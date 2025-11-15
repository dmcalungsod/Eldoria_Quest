"""
shop_cog.py

Handles the Guild Shop UI:
- Lists consumables for sale
- Handles the purchase transaction (Aurum debit, item credit)
"""

import discord
from discord.ui import View, Button, Select
from discord.ext import commands

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

        for item_key, price in SHOP_INVENTORY.items():
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                continue

            # Check if player can afford this item
            can_afford = self.current_aurum >= price

            item_select.add_option(
                label=f"{item_data['name']} ({price} {E.AURUM})",
                value=f"{item_key}:{price}",  # Pass both key and price
                description=item_data["description"][:100],
                emoji="🧪",
                default=False,
            )

        if self.current_aurum == 0:
            item_select.placeholder = "You have no Aurum to spend."
            item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    async def purchase_item_callback(self, interaction: discord.Interaction):
        """
        Handles the logic for purchasing a single item.
        """
        await interaction.response.defer()

        # Parse the selected value
        item_key, price_str = interaction.data["values"][0].split(":")
        price = int(price_str)

        item_data = CONSUMABLES.get(item_key)
        if not item_data:
            await interaction.followup.send(
                f"{E.ERROR} This item (key: {item_key}) does not exist in the data files.",
                ephemeral=True,
            )
            return

        # --- 1. Transaction Check ---
        # Re-fetch player data to prevent buying with stale info
        player_data = self.db.get_player(self.interaction_user.id)
        if not player_data or player_data["aurum"] < price:
            await interaction.followup.send(
                f"{E.ERROR} You do not have enough {E.AURUM} for this item.",
                ephemeral=True,
            )
            return

        # --- 2. Debit Aurum (The Transaction) ---
        new_aurum = player_data["aurum"] - price
        conn = self.db.connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE players SET aurum = ? WHERE discord_id = ?",
                (new_aurum, self.interaction_user.id),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            await interaction.followup.send(
                f"{E.ERROR} A database error occurred during the transaction.",
                ephemeral=True,
            )
            print(f"Shop purchase error: {e}")
            return
        finally:
            conn.close()

        # --- 3. Credit Item ---
        self.inv_manager.add_item(
            discord_id=self.interaction_user.id,
            item_key=item_key,
            item_name=item_data["name"],
            item_type="consumable",
            rarity=item_data["rarity"],
            amount=1,
        )

        # --- 4. Refresh the UI ---
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
