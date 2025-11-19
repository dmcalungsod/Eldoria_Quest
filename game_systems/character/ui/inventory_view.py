"""
game_systems/character/ui/inventory_view.py

The Adventurer’s Field Kit.
Hardened: Async database operations for equipping/unequipping.
"""

import asyncio
import logging
import discord
from discord.ui import Button, Select, View

from cogs.ui_helpers import build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.items.consumable_manager import ConsumableManager
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.items.inventory_manager import InventoryManager

logger = logging.getLogger("eldoria.ui.inventory")


class InventoryView(View):
    """
    Manage equipment and items.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        previous_view_callback,
        previous_view_label="Return",
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        
        # Managers
        self.inv_manager = InventoryManager(self.db)
        self.eq_manager = EquipmentManager(self.db)
        self.con_manager = ConsumableManager(self.db)

        self.previous_view_callback = previous_view_callback
        self.previous_view_label = previous_view_label

        # UI Components
        self.equip_select = Select(placeholder="Equip...", min_values=1, max_values=1, row=0)
        self.unequip_select = Select(placeholder="Unequip...", min_values=1, max_values=1, row=1)
        self.use_select = Select(placeholder="Use Item...", min_values=1, max_values=1, row=2)
        
        self.back_button = Button(
            label=self.previous_view_label, 
            style=discord.ButtonStyle.secondary, 
            row=3
        )

        self._populate_ui()

        # Callbacks
        self.equip_select.callback = self.equip_callback
        self.unequip_select.callback = self.unequip_callback
        self.use_select.callback = self.use_callback
        self.back_button.callback = self.previous_view_callback

        self.add_item(self.equip_select)
        self.add_item(self.unequip_select)
        self.add_item(self.use_select)
        self.add_item(self.back_button)

    def _populate_ui(self):
        """Populate dropdowns synchronously (safe for view init)."""
        try:
            # Using inventory manager's method which should be efficient enough
            items = self.inv_manager.get_inventory(self.interaction_user.id)
        except Exception:
            items = []

        equip_opts = []
        unequip_opts = []
        use_opts = []

        for item in items:
            val = str(item["id"])
            if item["item_type"] == "equipment":
                label = f"{item['item_name']} ({item['slot']})"
                if item.get("equipped"):
                    unequip_opts.append(discord.SelectOption(label=label, value=val, emoji="🛡️"))
                else:
                    equip_opts.append(discord.SelectOption(label=label, value=val, emoji="⚔️"))
            
            elif item["item_type"] == "consumable":
                label = f"{item['item_name']} (x{item['count']})"
                use_opts.append(discord.SelectOption(label=label, value=val, emoji="🧪"))

        # Configure Dropdowns
        self._set_options(self.equip_select, equip_opts, "No gear to equip.")
        self._set_options(self.unequip_select, unequip_opts, "No gear equipped.")
        self._set_options(self.use_select, use_opts, "No consumables.")

    def _set_options(self, select, options, empty_msg):
        if options:
            select.options = options[:25] # Discord limit
            select.disabled = False
        else:
            select.add_option(label=empty_msg, value="disabled")
            select.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your inventory.", ephemeral=True)
            return False
        return True

    # --------------------------------------------------------
    # Async Callbacks
    # --------------------------------------------------------
    async def equip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])
        
        # Run DB operation in thread
        success, msg = await asyncio.to_thread(
            self.eq_manager.equip_item, self.interaction_user.id, inv_id
        )
        
        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])
        
        success, msg = await asyncio.to_thread(
            self.eq_manager.unequip_item, self.interaction_user.id, inv_id
        )
        
        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])
        
        success, msg = await asyncio.to_thread(
            self.con_manager.use_item, self.interaction_user.id, inv_id
        )
        
        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def _refresh(self, interaction: discord.Interaction):
        items = await asyncio.to_thread(self.inv_manager.get_inventory, self.interaction_user.id)
        embed = build_inventory_embed(items)
        
        new_view = InventoryView(
            self.db, 
            self.interaction_user, 
            self.previous_view_callback, 
            self.previous_view_label
        )
        await interaction.edit_original_response(embed=embed, view=new_view)