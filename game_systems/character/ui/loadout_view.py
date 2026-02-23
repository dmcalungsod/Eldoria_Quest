"""
game_systems/character/ui/loadout_view.py

UI for managing Equipment Loadouts.
"""

import discord
from discord.ui import Button, Modal, Select, TextInput, View

from database.database_manager import DatabaseManager
from game_systems.items.equipment_manager import EquipmentManager


class LoadoutNameModal(Modal, title="Save Loadout"):
    name_input = TextInput(
        label="Loadout Name",
        placeholder="e.g., Boss Set, Farming Gear",
        min_length=1,
        max_length=30,
    )

    def __init__(self, db: DatabaseManager, eq_manager: EquipmentManager, parent_view: "LoadoutView"):
        super().__init__()
        self.db = db
        self.eq_manager = eq_manager
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        success, msg = self.eq_manager.save_loadout(interaction.user.id, name)

        # Refresh the parent view's UI
        self.parent_view._setup_ui()

        # Update the message with the refreshed view
        await interaction.response.edit_message(view=self.parent_view)

        # Send confirmation
        if success:
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.followup.send(f"Error: {msg}", ephemeral=True)


class LoadoutView(View):
    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        previous_view_callback,
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.eq_manager = EquipmentManager(self.db)
        self.previous_view_callback = previous_view_callback

        self.selected_loadout = None
        self._setup_ui()

    def _setup_ui(self):
        self.clear_items()

        # 1. Fetch Loadouts
        loadouts = self.db.get_equipment_sets(self.interaction_user.id)

        # 2. Select Menu
        options = []
        for loadout in loadouts:
            name = loadout["name"]
            item_count = len(loadout.get("items", {}))
            is_default = self.selected_loadout == name
            options.append(
                discord.SelectOption(label=name, description=f"{item_count} items", value=name, default=is_default)
            )

        if not options:
            self.select_menu = Select(
                placeholder="No loadouts saved",
                options=[discord.SelectOption(label="---", value="none")],
                disabled=True,
                row=0,
            )
        else:
            self.select_menu = Select(placeholder="Select a loadout...", options=options, row=0)
            self.select_menu.callback = self.select_callback

        self.add_item(self.select_menu)

        # 3. Action Buttons
        self.equip_btn = Button(
            label="Equip Loadout", style=discord.ButtonStyle.success, disabled=not self.selected_loadout, row=1
        )
        self.equip_btn.callback = self.equip_callback
        self.add_item(self.equip_btn)

        self.save_btn = Button(label="Save New", style=discord.ButtonStyle.primary, row=1)
        self.save_btn.callback = self.save_callback
        self.add_item(self.save_btn)

        self.delete_btn = Button(
            label="Delete", style=discord.ButtonStyle.danger, disabled=not self.selected_loadout, row=1
        )
        self.delete_btn.callback = self.delete_callback
        self.add_item(self.delete_btn)

        self.back_btn = Button(label="Back to Inventory", style=discord.ButtonStyle.secondary, row=2)
        self.back_btn.callback = self.previous_view_callback
        self.add_item(self.back_btn)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return

        val = self.select_menu.values[0]
        if val == "none":
            return

        self.selected_loadout = val
        self._setup_ui()  # Rebuild to update button states and default option
        await interaction.response.edit_message(view=self)

    async def equip_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return

        if not self.selected_loadout:
            return

        await interaction.response.defer()
        success, msg = self.eq_manager.equip_loadout(self.interaction_user.id, self.selected_loadout)
        await interaction.followup.send(msg, ephemeral=True)
        # We might want to refresh inventory view, but we are in LoadoutView.
        # User can click "Back" to verify.

    async def save_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return

        # Open Modal
        modal = LoadoutNameModal(self.db, self.eq_manager, self)
        await interaction.response.send_modal(modal)

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return

        if not self.selected_loadout:
            return

        success, msg = self.eq_manager.delete_loadout(self.interaction_user.id, self.selected_loadout)

        self.selected_loadout = None
        self._setup_ui()  # Refresh list
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction_user.id
