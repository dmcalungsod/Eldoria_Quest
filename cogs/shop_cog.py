"""
cogs/shop_cog.py

Adventurer’s Guild Supply Depot Interface for *Eldoria Quest*.
Refined for thematic consistency and adherence to the single-UI policy.
"""

import discord
from discord.ui import View, Button, Select
from discord.ext import commands
import asyncio
from typing import Tuple, Dict, Any

from database.database_manager import DatabaseManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.data.consumables import CONSUMABLES
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_guild_hall_callback


# ======================================================================
# SHOP PRICE LIST
# ======================================================================
SHOP_INVENTORY = {
    "hp_potion_1": 15,      # Dewfall Tonic
    "mp_potion_1": 15,      # Scholar's Draught
    "antidote_basic": 25,   # Thicket Antidote
    "smoke_pellet": 30,     # Whisper-Cloud Pellet
    "food_ration": 10,      # Trailman's Ration
    "hp_potion_2": 50,      # Glade Salve Vial
    "mp_potion_2": 50,      # Lunaris Tonic
    "strength_brew": 75,    # Captain’s Ale
    "dex_elixir": 75,       # Starlit Tincture
}


# ======================================================================
# SHOP VIEW
# ======================================================================

class ShopView(View):
    """
    UI for the Adventurer’s Guild Supply Depot.
    Displays the adventurer's Aurum and permits purchasing provisions.
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

        # Dropdown
        self.add_item(self.build_item_select())

        # Back button
        self.back_button = Button(
            label="Return to Guild Hall",
            style=discord.ButtonStyle.secondary,
            custom_id="back_to_guild_hall",
            row=1,
        )
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def set_back_button(self, callback_function, label="Back"):
        """Allows an external view to override the back button."""
        self.back_button.label = label
        self.back_button.callback = callback_function

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "These provisions are set aside for another adventurer.",
                ephemeral=True,
            )
            return False
        return True

    # ------------------------------------------------------------------
    # BUILD DROPDOWN
    # ------------------------------------------------------------------
    def build_item_select(self) -> Select:
        """Creates the Select dropdown for shop items."""

        item_select = Select(
            placeholder="Select a provision to requisition...",
            min_values=1,
            max_values=1,
            row=0,
        )

        if not SHOP_INVENTORY:
            item_select.add_option(
                label="The shelves are barren.",
                value="disabled",
                emoji=E.ERROR,
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
                label=f"{item_data['name']} — {price} Aurum",
                value=f"{item_key}:{price}",
                description=item_data["description"][:100],
                emoji="🪙",
            )

        if not can_afford_any and self.current_aurum > 0:
            item_select.placeholder = "Insufficient Aurum for any listed provisions."
        elif self.current_aurum == 0:
            item_select.placeholder = "You carry no Aurum."
            item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    # ------------------------------------------------------------------
    # DATABASE PURCHASE EXECUTION
    # ------------------------------------------------------------------
    def _execute_purchase(self, item_key: str, price: int) -> Tuple[bool, Any, int]:
        """
        Handles the DB transaction in a thread.
        Returns: (success, item_data_or_error_msg, new_aurum)
        """
        item_data = CONSUMABLES.get(item_key)
        if not item_data:
            return (False, "The requested item could not be located.", 0)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT aurum FROM players WHERE discord_id = ?",
                (self.interaction_user.id,)
            )
            player_data = cur.fetchone()

            if not player_data or player_data["aurum"] < price:
                return (
                    False,
                    f"You lack sufficient {E.AURUM} to obtain this provision.",
                    0,
                )

            new_aurum = player_data["aurum"] - price

            cur.execute(
                "UPDATE players SET aurum = ? WHERE discord_id = ?",
                (new_aurum, self.interaction_user.id)
            )

        return (True, item_data, new_aurum)

    # ------------------------------------------------------------------
    # PURCHASE CALLBACK
    # ------------------------------------------------------------------
    async def purchase_item_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        item_key, price_str = interaction.data["values"][0].split(":")
        price = int(price_str)

        success, result, new_aurum = await asyncio.to_thread(
            self._execute_purchase, item_key, price
        )

        if not success:
            final_aurum = self.current_aurum
            status_name = "Transaction Declined"
            status_value = f"{E.ERROR} {result}"
        else:
            item_data = result
            final_aurum = new_aurum

            await asyncio.to_thread(
                self.inv_manager.add_item,
                self.interaction_user.id,
                item_key,
                item_data["name"],
                "consumable",
                item_data["rarity"],
                1,
            )

            status_name = "Requisition Complete"
            status_value = (
                f"{E.CHECK} Secured **1× {item_data['name']}** "
                f"for **{price} {E.AURUM}**."
            )

        # ------------------------------------------------------------------
        # REBUILD UI
        # ------------------------------------------------------------------
        embed = discord.Embed(
            title="🛒 Guild Supply Depot",
            description=(
                "Within the Adventurer’s Guild, this modest counter distributes "
                "the essentials needed for survival beyond the safety of its walls.\n\n"
                f"You currently hold **{final_aurum} {E.AURUM}**."
            ),
            color=discord.Color.green() if success else discord.Color.red(),
        )

        embed.add_field(name=status_name, value=status_value, inline=False)

        new_view = ShopView(self.db, self.interaction_user, final_aurum)

        # Preserve return behavior
        new_view.back_button.callback = self.back_button.callback
        new_view.back_button.label = self.back_button.label

        await interaction.edit_original_response(embed=embed, view=new_view)


# ======================================================================
# COG LOADER
# ======================================================================

class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
