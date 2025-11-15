"""
character_cog.py

Handles the main character UI hubs for the game:
- CharacterProfileView (The main "home" screen)
- InventoryView (Interactive inventory)
- SkillsView
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
from game_systems.items.equipment_manager import EquipmentManager
from game_systems.items.consumable_manager import ConsumableManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import (
    back_to_profile_callback,
    back_to_guild_hall_callback,
    build_inventory_embed,
)

# --- View Imports ---
from .quest_hub_cog import QuestLogView

# --- FIX: REMOVED IMPORT from .adventure_commands ---


# ======================================================================
# CHARACTER PROFILE (THE NEW MAIN MENU)
# ======================================================================


class CharacterProfileView(View):
    """
    The main character profile screen. This is the new "home" UI.
    Buttons: Inventory, Skills, Quest Log, Start Adventure, Guild
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.inventory_manager = InventoryManager(self.db)
        self.interaction_user = interaction_user
        self.equipment_manager = EquipmentManager(self.db)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    # --- (Row 1 buttons) ---

    @discord.ui.button(
        label="Inventory",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_inventory",
        emoji=E.BACKPACK,
        row=0,
    )
    async def inventory_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Inventory UI.
        """
        await interaction.response.defer()
        items = self.inventory_manager.get_inventory(interaction.user.id)

        embed = build_inventory_embed(items)

        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=back_to_profile_callback,
            previous_view_label="Back to Profile",
        )
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Skills",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_skills",
        emoji="✨",
        row=0,
    )
    async def skills_callback(self, interaction: discord.Interaction, button: Button):
        """
        Edits the message to show the Skills UI.
        """
        await interaction.response.defer()
        player_skills = self.db.get_player_skills(interaction.user.id)

        if not player_skills:
            skills_str = "You have not learned any skills."
        else:
            skills_str = "\n".join(
                [
                    f"• **{s['name']}** (Lv. {s['skill_level']}) - *{s['type']}*"
                    for s in player_skills
                ]
            )

        embed = discord.Embed(
            title="Acquired Skills",
            description=skills_str,
            color=discord.Color.purple(),
        )

        view = SkillsView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Quest Log",
        style=discord.ButtonStyle.primary,
        custom_id="profile_quest_log",
        emoji=E.QUEST_SCROLL,
        row=0,
    )
    async def quest_log_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Quest Log UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem

        quest_system = QuestSystem(self.db)
        active_quests = quest_system.get_player_quests(interaction.user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventurer's Log",
            description="A review of your currently accepted assignments.",
            color=discord.Color.from_rgb(139, 69, 19),
        )
        if not active_quests:
            embed.add_field(
                name="No Active Quests",
                value="Visit the Guild Hall Quest Board to accept a task.",
            )
        else:
            for quest in active_quests:
                progress_text = []
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})
                for obj_type, tasks in objectives.items():
                    if isinstance(tasks, dict):
                        for task, required in tasks.items():
                            current = progress.get(obj_type, {}).get(task, 0)
                            progress_text.append(f"• {task}: {current} / {required}")
                embed.add_field(
                    name=f"{quest['title']} (ID: {quest['id']})",
                    value="\n".join(progress_text) or "No objectives.",
                    inline=False,
                )

        view = QuestLogView(self.db, active_quests, self.interaction_user)
        view.set_back_button(back_to_profile_callback, "Back to Profile")
        await interaction.edit_original_response(embed=embed, view=view)

    # --- (Row 2 buttons) ---

    @discord.ui.button(
        label="Start Adventure",
        style=discord.ButtonStyle.success,
        custom_id="profile_start_adventure",
        row=1,
    )
    async def start_adventure_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Adventure Setup (location picker) UI
        OR resumes a stuck adventure if one is found.
        """
        # --- Import locally ---
        from .adventure_commands import AdventureSetupView, ExplorationView
        from game_systems.data.adventure_locations import LOCATIONS
        import game_systems.data.emojis as E
        import json

        adventure_cog = interaction.client.get_cog("AdventureCommands")
        if not adventure_cog:
            await interaction.response.send_message(
                f"{E.ERROR} Adventure system is offline.", ephemeral=True
            )
            return

        active_session_row = adventure_cog.manager.get_active_session(
            interaction.user.id
        )

        if active_session_row:
            # --- User is STUCK. Let's RESUME their session ---
            if not interaction.response.is_done():
                await interaction.response.defer()  # Defer to be safe

            loc_id = active_session_row["location_id"]
            loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone", "emoji": E.MAP})

            try:
                log_data = active_session_row["logs"]
                log = json.loads(log_data if log_data else "[]")
            except json.JSONDecodeError:
                log = ["Your adventure log was corrupted, but you can continue."]

            if not isinstance(log, list):
                log = ["Adventure log corrupted. Resuming."]

            # Get last 10 lines for the view's internal log
            log = log[-10:]

            # --- THIS IS THE FIX ---
            # Instead of showing the old log, show a clean resume message.
            # The 'log' variable is still passed to the view to maintain history.
            resume_description = (
                "Your previous session has been recovered. You can continue "
                "exploring or return to the city."
            )
            # --- END OF FIX ---

            embed = discord.Embed(
                title=f"{loc_data.get('emoji', E.MAP)} Resuming Adventure: {loc_data['name']}",
                description=resume_description,  # <-- Use the new clean message
                color=discord.Color.green(),
            )
            embed.set_footer(text="Your previous session was recovered.")

            view = ExplorationView(
                self.db,
                adventure_cog.manager,
                loc_id,
                log,  # <-- Pass the old log history to the view
                self.interaction_user,
            )
            await interaction.edit_original_response(embed=embed, view=view)
            return

        # --- Original logic: No active session, show setup ---
        await interaction.response.defer()  # Defer for the setup view
        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description="You stand before the city gates, the Guild's clearance seal in your hand. The wilderness beyond the walls of Ashgrave awaits.\n\nSelect a destination.",
            color=discord.Color.dark_green(),
        )
        view = AdventureSetupView(self.db, adventure_cog.manager, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Guild Hall",
        style=discord.ButtonStyle.primary,
        custom_id="profile_guild_hall",
        row=1,
    )
    async def guild_hall_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Guild Hall (sub-menu) UI.
        """
        await back_to_guild_hall_callback(interaction)

    # --- THIS IS THE NEW BUTTON (Row 3) ---
    @discord.ui.button(
        label="Status Update",
        style=discord.ButtonStyle.success,
        custom_id="profile_status_update",
        emoji="⬆️",
        row=2,
    )
    async def status_update_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Status Update UI.
        """
        await interaction.response.defer()

        # Import the new cog's view
        from .status_update_cog import StatusUpdateView

        # Get all player data
        player_data = self.db.get_player(self.interaction_user.id)
        stats_json = self.db.get_player_stats_json(self.interaction_user.id)
        player_stats = PlayerStats.from_dict(stats_json)

        # Build the embed using the static method from the view
        # --- THIS IS THE FIX ---
        embed = StatusUpdateView.build_status_embed(player_data, player_stats)
        # --- END OF FIX ---

        view = StatusUpdateView(
            self.db, self.interaction_user, player_data, player_stats
        )
        await interaction.edit_original_response(embed=embed, view=view)

    # --- END OF NEW BUTTON ---


# ======================================================================
# INVENTORY & SKILLS VIEWS
# ======================================================================


class InventoryView(View):
    """
    A dynamic view for the inventory.
    Allows equipping, unequipping, and using items.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        previous_view_callback,
        previous_view_label="Back",
    ):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.inv_manager = InventoryManager(self.db)
        self.eq_manager = EquipmentManager(self.db)
        self.con_manager = ConsumableManager(self.db)

        self.previous_view_callback = previous_view_callback
        self.previous_view_label = previous_view_label

        self.equip_select = Select(
            placeholder="Equip an item...", min_values=1, max_values=1, row=0
        )
        self.unequip_select = Select(
            placeholder="Unequip an item...", min_values=1, max_values=1, row=1
        )
        self.use_select = Select(
            placeholder="Use an item...", min_values=1, max_values=1, row=2
        )
        self.back_button = Button(
            label=self.previous_view_label,
            style=discord.ButtonStyle.secondary,
            row=3,
        )

        self._populate_selects()

        self.equip_select.callback = self.equip_callback
        self.unequip_select.callback = self.unequip_callback
        self.use_select.callback = self.use_callback
        self.back_button.callback = self.previous_view_callback

        self.add_item(self.equip_select)
        self.add_item(self.unequip_select)
        self.add_item(self.use_select)
        self.add_item(self.back_button)

    def _populate_selects(self):
        """Fetches inventory and populates the dropdowns."""
        items = self.inv_manager.get_inventory(self.interaction_user.id)

        self.equip_select.options.clear()
        self.unequip_select.options.clear()
        self.use_select.options.clear()

        equip_options = []
        unequip_options = []
        use_options = []

        for item in items:
            item_type = item["item_type"]
            label = f"{item['item_name']} (x{item['count']})"
            value = str(item["id"])

            if item_type == "equipment":
                label = f"{item['item_name']} (Slot: {item['slot']})"
                if item["equipped"] == 1:
                    unequip_options.append(
                        discord.SelectOption(label=label, value=value, emoji="🛡️")
                    )
                else:
                    equip_options.append(
                        discord.SelectOption(label=label, value=value, emoji="⚔️")
                    )

            elif item_type == "consumable":
                use_options.append(
                    discord.SelectOption(label=label, value=value, emoji="🧪")
                )

        if equip_options:
            self.equip_select.options = equip_options
            self.equip_select.disabled = False
        else:
            self.equip_select.add_option(label="No unequipped items.", value="disabled")
            self.equip_select.disabled = True

        if unequip_options:
            self.unequip_select.options = unequip_options
            self.unequip_select.disabled = False
        else:
            self.unequip_select.add_option(label="No items equipped.", value="disabled")
            self.unequip_select.disabled = True

        if use_options:
            self.use_select.options = use_options
            self.use_select.disabled = False
        else:
            self.use_select.add_option(label="No usable items.", value="disabled")
            self.use_select.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def equip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.equip_select.values[0])

        success, message = self.eq_manager.equip_item(
            self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.unequip_select.values[0])

        success, message = self.eq_manager.unequip_item(
            self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.use_select.values[0])

        success, message = self.con_manager.use_item(
            self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def _refresh_view(self, interaction: discord.Interaction):
        """Re-builds the embed and view to show changes."""

        items = self.inv_manager.get_inventory(self.interaction_user.id)
        embed = build_inventory_embed(items)

        new_view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=self.previous_view_callback,
            previous_view_label=self.previous_view_label,
        )

        await interaction.edit_original_response(embed=embed, view=new_view)


class SkillsView(View):
    """
    A simple view that just shows the "Back to Profile" button.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        back_button = Button(
            label="Back to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
        )
        back_button.callback = back_to_profile_callback
        self.add_item(back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True


# ======================================================================
# COG LOADER
# ======================================================================


class CharacterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCog(bot))
