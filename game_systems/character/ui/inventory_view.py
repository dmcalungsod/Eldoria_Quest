"""
game_systems/character/ui/inventory_view.py

The Adventurer’s Field Kit.
Hardened: Async database operations for equipping/unequipping.
Enhanced: Inventory filtering for better UX.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

from cogs.ui_helpers import build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES
from game_systems.data.equipments import EQUIPMENT_DATA
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
        current_filter="All",
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.current_filter = current_filter

        # Managers
        self.inv_manager = InventoryManager(self.db)
        self.eq_manager = EquipmentManager(self.db)
        self.con_manager = ConsumableManager(self.db)

        self.previous_view_callback = previous_view_callback
        self.previous_view_label = previous_view_label

        # Fetch items once
        try:
            self.all_items = self.inv_manager.get_inventory(self.interaction_user.id)
        except Exception:
            self.all_items = []

        # UI Components
        self.create_filter_buttons()

        self.equip_select = Select(placeholder="Equip...", min_values=1, max_values=1, row=1)
        self.unequip_select = Select(placeholder="Unequip...", min_values=1, max_values=1, row=2)
        self.use_select = Select(placeholder="Use Item...", min_values=1, max_values=1, row=3)

        self.back_button = Button(label=self.previous_view_label, style=discord.ButtonStyle.secondary, row=4)

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

    def create_filter_buttons(self):
        """Creates filter buttons for the inventory."""
        filters = ["All", "Weapon", "Armor", "Accessory", "Consumable"]
        for f in filters:
            style = discord.ButtonStyle.primary if f == self.current_filter else discord.ButtonStyle.secondary
            btn = Button(label=f, style=style, custom_id=f"filter_{f}", row=0)
            btn.callback = self.filter_callback
            self.add_item(btn)

    def _get_item_category(self, item):
        """Determines the category of an item for filtering."""
        if item["item_type"] == "consumable":
            return "Consumable"

        # Equipment logic
        slot = item.get("slot", "")
        if slot in EquipmentManager.TWO_HANDED_SLOTS or slot in EquipmentManager.MAIN_HAND_SLOTS:
            return "Weapon"
        if slot in EquipmentManager.OFF_HAND_SLOTS:
            if slot == "shield":
                return "Armor"
            return "Weapon"
        if slot == "accessory":
            return "Accessory"

        return "Armor" # Default fallback for equipment

    def _populate_ui(self):
        """Populate dropdowns based on current filter."""
        try:
            # Fetch player data for validation
            player = self.db.get_player(self.interaction_user.id)
            guild_rank = self.db.get_guild_rank(self.interaction_user.id) or "F"
            allowed_slots = self.eq_manager._get_player_allowed_slots(self.interaction_user.id)
        except Exception:
            player = None
            guild_rank = "F"
            allowed_slots = []

        # Resolve Class Name
        class_name = None
        if player:
            class_id = player.get("class_id")
            class_name = next((k for k, v in CLASSES.items() if v["id"] == class_id), None)

        player_data = {
            "level": player.get("level", 1) if player else 1,
            "rank": guild_rank,
            "class_name": class_name,
        }

        equip_opts = []
        unequip_opts = []
        use_opts = []

        for item in self.all_items:
            # Check Filter
            category = self._get_item_category(item)
            if self.current_filter != "All" and category != self.current_filter:
                continue

            val = str(item["id"])
            if item["item_type"] == "equipment":
                slot_name = self.eq_manager.get_slot_display_name(item["slot"])
                label = f"{item['item_name']} ({slot_name})"
                if item.get("equipped"):
                    unequip_opts.append(discord.SelectOption(label=label, value=val, emoji="🛡️"))
                else:
                    # Check requirements for UI feedback
                    static_data = EQUIPMENT_DATA.get(item["item_key"])
                    full_item_data = (static_data or {}).copy()
                    full_item_data.update(item)

                    can_equip, reason = self.eq_manager.check_requirements(full_item_data, player_data)

                    # Also check slot restrictions
                    if can_equip and item["slot"] not in allowed_slots:
                        can_equip = False
                        reason = f"Class restricted ({slot_name})"

                    if can_equip:
                        equip_opts.append(discord.SelectOption(label=label, value=val, emoji="⚔️"))
                    else:
                        # Greyed-out / Locked UI
                        locked_label = f"🔒 {label[:80]}"  # Truncate to ensure fit
                        equip_opts.append(
                            discord.SelectOption(
                                label=locked_label, value=val, emoji="🚫", description=f"Cannot Equip: {reason}"
                            )
                        )

            elif item["item_type"] == "consumable":
                label = f"{item['item_name']} (x{item['count']})"
                use_opts.append(discord.SelectOption(label=label, value=val, emoji="🧪"))

        # Configure Dropdowns
        # Dynamically enable/disable based on filter context

        # Equip Select: Only for equipment filters or All
        show_equip = self.current_filter in ["All", "Weapon", "Armor", "Accessory"]
        self._set_options(self.equip_select, equip_opts, "No gear to equip.", visible=show_equip)

        # Unequip Select: Always show unless viewing Consumables
        show_unequip = self.current_filter != "Consumable"
        # Note: If filtering by "Weapon", we might only want to show equipped weapons?
        # Current logic iterates ALL items and filters them. So unequip_opts only contains filtered items.
        # This is correct.
        self._set_options(self.unequip_select, unequip_opts, "No gear equipped.", visible=show_unequip)

        # Use Select: Only for Consumables or All
        show_use = self.current_filter in ["All", "Consumable"]
        self._set_options(self.use_select, use_opts, "No consumables.", visible=show_use)

    def _set_options(self, select, options, empty_msg, visible=True):
        if not visible:
             select.disabled = True
             select.placeholder = "---"
             select.options = [discord.SelectOption(label="Disabled", value="disabled")]
             return

        if options:
            select.options = options[:25]  # Discord limit
            select.disabled = False
            select.placeholder = select.placeholder or "Select..."
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
    async def filter_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Custom ID format: filter_Category
        new_filter = interaction.custom_id.split("_")[1]
        self.current_filter = new_filter

        # Update button styles
        for child in self.children:
            if isinstance(child, Button) and child.custom_id and child.custom_id.startswith("filter_"):
                child.style = discord.ButtonStyle.primary if child.custom_id == f"filter_{new_filter}" else discord.ButtonStyle.secondary

        # Re-populate selects
        self._populate_ui()

        await interaction.edit_original_response(view=self)

    async def equip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])

        # Run DB operation in thread
        success, msg = await asyncio.to_thread(self.eq_manager.equip_item, self.interaction_user.id, inv_id)

        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])

        success, msg = await asyncio.to_thread(self.eq_manager.unequip_item, self.interaction_user.id, inv_id)

        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_id = int(interaction.data["values"][0])

        success, msg = await asyncio.to_thread(self.con_manager.use_item, self.interaction_user.id, inv_id)

        await interaction.followup.send(msg, ephemeral=True)
        await self._refresh(interaction)

    async def _refresh(self, interaction: discord.Interaction):
        items = await asyncio.to_thread(self.inv_manager.get_inventory, self.interaction_user.id)
        max_slots = await asyncio.to_thread(self.db.calculate_inventory_limit, self.interaction_user.id)
        embed = build_inventory_embed(items, max_slots)

        # Pass current filter to new view to maintain state
        new_view = InventoryView(
            self.db,
            self.interaction_user,
            self.previous_view_callback,
            self.previous_view_label,
            current_filter=self.current_filter
        )
        await interaction.edit_original_response(embed=embed, view=new_view)
