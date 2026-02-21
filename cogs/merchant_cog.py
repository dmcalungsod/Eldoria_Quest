"""
cogs/merchant_cog.py

Discord Cog for the Mystic Merchant Event (The Void Trader).
Handles the special merchant shop and interactions.
"""

import asyncio
import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.materials import MATERIALS
from game_systems.events.world_event_system import WorldEventSystem

from .ui_helpers import get_player_or_error

logger = logging.getLogger("eldoria.cogs.merchant")

# Define the Merchant's Inventory
# Item Key -> Price
MERCHANT_INVENTORY = {
    "heroic_potion": 500,
    "elixir_luck": 1000,
    "celestial_dust": 2000,
    "void_heart": 3000,
    "mythic_amber": 5000,
}


class MerchantView(View):
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User, current_aurum: int):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.current_aurum = current_aurum

        self.add_item(self.build_item_select())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id

    def build_item_select(self) -> Select:
        item_select = Select(placeholder="Select rare goods...", min_values=1, max_values=1, row=0)

        can_afford_any = False
        for item_key, price in MERCHANT_INVENTORY.items():
            # Check Consumables first, then Materials
            item_data = CONSUMABLES.get(item_key)
            item_type = "consumable"

            if not item_data:
                # Check Materials if not found in Consumables
                # Materials structure is slightly different, check top-level or search?
                # The MATERIALS dict is flat: "key": {data}
                item_data = MATERIALS.get(item_key)
                item_type = "material"

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
                value=f"{item_key}:{price}:{item_type}",
                description=item_data.get("description", "A rare item from the Void.")[:50],
                emoji=emoji,
            )

        if not can_afford_any:
            item_select.placeholder = "Insufficient Funds"
            if self.current_aurum == 0:
                item_select.disabled = True

        item_select.callback = self.purchase_item_callback
        return item_select

    def _execute_purchase(self, item_key: str, item_type: str) -> tuple[bool, Any, int]:
        """Atomic purchase transaction."""
        try:
            # SECURITY: Fetch price from server inventory, do not trust client
            price = MERCHANT_INVENTORY.get(item_key)
            if price is None:
                return (False, "Item not available.", 0)

            # Resolve item data again
            item_data = CONSUMABLES.get(item_key)
            if not item_data:
                item_data = MATERIALS.get(item_key)

            if not item_data:
                return (False, "Item data missing.", 0)

            # Delegate to DatabaseManager for atomic execution with refund support
            # Now passing item_type to support materials
            success, result, new_balance = self.db.purchase_item(
                self.interaction_user.id, item_key, item_data, price, item_type=item_type
            )

            if success:
                logger.info(f"User {self.interaction_user.id} bought {item_key} for {price} from Merchant")

            return (success, result, new_balance)

        except Exception as e:
            logger.error(f"Purchase error: {e}", exc_info=True)
            return (False, "System error.", 0)

    async def purchase_item_callback(self, interaction: discord.Interaction):
        # Validate player existence first
        if not await get_player_or_error(interaction, self.db):
            return

        await interaction.response.defer()

        # Parse values: key:price:type
        values = interaction.data["values"][0].split(":")
        item_key = values[0]
        # Price is ignored for security, looked up in _execute_purchase
        item_type = values[2] if len(values) > 2 else "consumable"

        success, result, new_aurum = await asyncio.to_thread(self._execute_purchase, item_key, item_type)

        embed = discord.Embed(
            title="🌌 The Void Trader",
            description=(
                "The mysterious figure nods silently as you complete the transaction.\n"
                f"You currently hold **{new_aurum if success else self.current_aurum} {E.AURUM}**."
            ),
            color=discord.Color.purple() if success else discord.Color.red(),
        )

        msg = f"{E.CHECK} Secured **1x {result['name']}**." if success else f"{E.ERROR} {result}"
        embed.add_field(name="Transaction Receipt", value=msg)

        # Check if event is still active
        event_system = WorldEventSystem(self.db)
        active_event = event_system.get_current_event()

        if active_event and active_event["type"] == WorldEventSystem.MYSTIC_MERCHANT:
            new_view = MerchantView(self.db, self.interaction_user, new_aurum if success else self.current_aurum)
            await interaction.edit_original_response(embed=embed, view=new_view)
        else:
             embed.description += "\n\n*The merchant has vanished into the shadows...*"
             await interaction.edit_original_response(embed=embed, view=None)


class MerchantCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.event_system = WorldEventSystem(self.db)
        logger.info("MerchantCog initialized.")

    @app_commands.command(
        name="merchant", description="Visit the Void Trader (Only available during the Mystic Merchant event)."
    )
    async def merchant(self, interaction: discord.Interaction):
        """Opens the Mystic Merchant shop if the event is active."""
        # 1. Check active event
        active_event = self.event_system.get_current_event()

        if not active_event or active_event["type"] != WorldEventSystem.MYSTIC_MERCHANT:
            embed = discord.Embed(
                title="🌑 The Merchant is Gone",
                description="You look around, but the Void Trader is nowhere to be found. He only appears when the veil is thin.",
                color=discord.Color.dark_grey(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 2. Check player existence
        if not await get_player_or_error(interaction, self.db):
            return

        # 3. Get Player Aurum
        player = self.db.get_player(interaction.user.id)
        current_aurum = player["aurum"]

        embed = discord.Embed(
            title="🌌 The Void Trader",
            description=(
                "A cloaked figure stands amidst swirling shadows. His wares are rare, powerful, and expensive.\n"
                f"*\"Gold... or your soul. But today, I accept gold.\"*\n\n"
                f"Your Balance: **{current_aurum} {E.AURUM}**"
            ),
            color=discord.Color.purple(),
        )

        view = MerchantView(self.db, interaction.user, current_aurum)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MerchantCog(bot))
