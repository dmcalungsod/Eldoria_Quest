"""
game_systems/character/ui/inventory_view.py
"""

import asyncio

import discord
from discord.ui import Button, Select, View

from cogs.ui_helpers import build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.items.consumable_manager import ConsumableManager
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.items.inventory_manager import InventoryManager


class InventoryView(View):
    """
    The Adventurer’s Field Kit interface:
    equip arms, unequip gear, use provisions.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        previous_view_callback,

        previous_view_label="Return",
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        self.inv_manager = InventoryManager(self.db)
        self.eq_manager = EquipmentManager(self.db)
        self.con_manager = ConsumableManager(self.db)

        self.previous_view_callback = previous_view_callback
        self.previous_view_label = previous_view_label

        # --- Dropdowns ---
        self.equip_select = Select(
            placeholder="Equip gear...",
            min_values=1,
            max_values=1,
            row=0
        )
        self.unequip_select = Select(
            placeholder="Remove equipped gear...",
            min_values=1,
            max_values=1,
            row=1
        )
        self.use_select = Select(
            placeholder="Use a provision...",
            min_values=1,
            max_values=1,
            row=2
        )

        # --- Back Button ---
        self.back_button = Button(
            label=self.previous_view_label,
            style=discord.ButtonStyle.secondary,
            row=3
        )

        # Populate selects based on inventory
        self._populate_selects()

        # Assign callbacks
        self.equip_select.callback = self.equip_callback
        self.unequip_select.callback = self.unequip_callback
        self.use_select.callback = self.use_callback
        self.back_button.callback = self.previous_view_callback

        # Add components to view
        self.add_item(self.equip_select)
        self.add_item(self.unequip_select)
        self.add_item(self.use_select)
        self.add_item(self.back_button)

    # ------------------------------------------------------------------
    # Select Population
    # ------------------------------------------------------------------

    def _populate_selects(self):
        """Populate dropdowns with appropriate inventory items."""
        items = self.inv_manager.get_inventory(self.interaction_user.id)

        self.equip_select.options.clear()
        self.unequip_select.options.clear()
        self.use_select.options.clear()

        equip_options = []
        unequip_options = []
        use_options = []

        for item in items:
            item_type = item["item_type"]
            value = str(item["id"])

            # --- Equipment ---
            if item_type == "equipment":
                label = f"{item['item_name']} ({item['slot']})"

                if item.get("equipped") == 1:
                    unequip_options.append(
                        discord.SelectOption(
                            label=label,
                            value=value,
                            emoji="🛡️"  # Equipped gear
                        )
                    )
                else:
                    equip_options.append(
                        discord.SelectOption(
                            label=label,
                            value=value,
                            emoji="⚔️"  # Equipable gear
                        )
                    )

            # --- Consumables ---
            elif item_type == "consumable":
                label = f"{item['item_name']} (x{item['count']})"
                use_options.append(
                    discord.SelectOption(
                        label=label,
                        value=value,
                        emoji="🧪"
                    )
                )

        # Equip Dropdown
        if equip_options:
            self.equip_select.options = equip_options
            self.equip_select.disabled = False
        else:
            self.equip_select.add_option(
                label="No gear available to equip.",
                value="disabled"
            )
            self.equip_select.disabled = True

        # Unequip Dropdown
        if unequip_options:
            self.unequip_select.options = unequip_options
            self.unequip_select.disabled = False
        else:
            self.unequip_select.add_option(
                label="No gear currently equipped.",
                value="disabled"
            )
            self.unequip_select.disabled = True

        # Consumable Dropdown
        if use_options:
            self.use_select.options = use_options
            self.use_select.disabled = False
        else:
            self.use_select.add_option(
                label="No provisions available.",
                value="disabled"
            )
            self.use_select.disabled = True

    # ------------------------------------------------------------------
    # Interaction Check
    # ------------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "These supplies do not belong to you.",
                ephemeral=True
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Action Callbacks
    # ------------------------------------------------------------------

    async def equip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.equip_select.values[0])

        success, message = await asyncio.to_thread(
            self.eq_manager.equip_item,
            self.interaction_user.id,
            inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.unequip_select.values[0])

        success, message = await asyncio.to_thread(
            self.eq_manager.unequip_item,
            self.interaction_user.id,
            inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.use_select.values[0])

        success, message = await asyncio.to_thread(
            self.con_manager.use_item,
            self.interaction_user.id,
            inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def _refresh_view(self, interaction: discord.Interaction):
        items = await asyncio.to_thread(
            self.inv_manager.get_inventory,
            self.interaction_user.id
        )

        embed = await asyncio.to_thread(
            build_inventory_embed,
            items
        )

        new_view = InventoryView(
            self.db,
            self.interaction_user,
            self.previous_view_callback,
            self.previous_view_label
        )

        await interaction.edit_original_response(
            embed=embed,
            view=new_view
        )
