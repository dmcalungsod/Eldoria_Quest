"""
character_cog.py

Handles the main character UI hubs for the game:
- CharacterTabView (The main "CHARACTER" tab)
- AbilitiesView (Sub-menu for inventory and skills)
- AdventureView (Sub-menu for quests and travel)
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio 

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
# (Imported inside functions to prevent circular dependencies)


# ======================================================================
# "CHARACTER" TAB (The Main Menu)
# ======================================================================

class CharacterTabView(View):
    """
    The main character profile screen. This is the new "home" UI.
    Shows core stats and buttons to navigate to Abilities & Adventure.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # This view only routes to other views or callbacks
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Arcana & Arms",
        style=discord.ButtonStyle.primary,
        custom_id="profile_abilities",
        emoji="✨",
        row=0,
    )
    async def abilities_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Abilities (Inventory/Skills) sub-menu.
        """
        await interaction.response.defer()
        embed = discord.Embed(
            title="📜 Arcane Ledger of Abilities",
            description=(
                "*A leather-bound tome hums with dormant power as you open it. "
                "Every page reflects the skills you’ve mastered, the tools you carry, "
                "and the relics woven into your fate.*\n\n"
                "**Manage the following:**\n"
                "• **Inventory** — Items, materials, and consumables.\n"
                "• **Equipment** — Weapons and armor currently worn.\n"
                "• **Skills** — Techniques and abilities you've unlocked."
            ),
            color=discord.Color.purple(),
        )

        view = AbilitiesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


    @discord.ui.button(
        label="Adventure",
        style=discord.ButtonStyle.success,
        custom_id="profile_adventure",
        emoji="🗺️",
        row=0,
    )
    async def adventure_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Adventure (Quests/Travel) sub-menu.
        """
        await interaction.response.defer()
        embed = discord.Embed(
            title="🗺️ The Road Ahead",
            description=(
                "*Shadows creep along the edges of the world, awaiting your next move.*\n\n"
                "**Your choices:**\n"
                "• **Quest Log** — Recall the tasks that bind your fate.\n"
                "• **Guild Hall** — Seek aid, rest, or guidance.\n"
                "• **Journey Forth** — Step into dangers untold."
            ),
            color=discord.Color.dark_teal(),
        )

        view = AdventureView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)


    @discord.ui.button(
        label="Status Update",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_status_update",
        # FIX: Use the new standard Unicode E.VESTIGE
        emoji=E.VESTIGE, # Was: E.LEVEL_UP
        row=1, 
    )
    async def status_update_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Status Update UI.
        """
        await interaction.response.defer()
        
        from .status_update_cog import StatusUpdateView
        
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
        
        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        
        player_stats = PlayerStats.from_dict(stats_json)

        embed = StatusUpdateView.build_status_embed(player_data, player_stats)
        
        view = StatusUpdateView(self.db, self.interaction_user, player_data, player_stats)
        # Manually set the back button to point to the main profile
        view.back_button.callback = back_to_profile_callback
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# "ABILITIES" TAB (Sub-Menu)
# ======================================================================

class AbilitiesView(View):
    """
    Sub-menu for Inventory, Skills, and Skill Trainer.
    """
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.inventory_manager = InventoryManager(self.db)
        self.interaction_user = interaction_user

        # --- Back Button ---
        back_btn = Button(
            label="Back to Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
            row=1
        )
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

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
        
        items = await asyncio.to_thread(
            self.inventory_manager.get_inventory, self.interaction_user.id
        )
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            # Set the back button to go all the way to the main profile
            previous_view_callback=back_to_profile_callback,
            previous_view_label="Back to Character",
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
        
        player_skills = await asyncio.to_thread(
            self.db.get_player_skills, self.interaction_user.id
        )

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
        # Set the back button to go all the way to the main profile
        view.back_button.callback = back_to_profile_callback
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# "ADVENTURE" TAB (Sub-Menu)
# ======================================================================

class AdventureView(View):
    """
    Sub-menu for Quest Log, Guild Hall, and Starting Adventures.
    """
    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user
        
        # --- Back Button ---
        back_btn = Button(
            label="Back to Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
            row=2
        )
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Start Adventure",
        style=discord.ButtonStyle.success,
        custom_id="profile_start_adventure",
        emoji="⚔️",
        row=0,
    )
    async def start_adventure_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Adventure Setup (location picker) UI
        OR resumes a stuck adventure if one is found.
        """
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

        active_session_row = await asyncio.to_thread(
            adventure_cog.manager.get_active_session, self.interaction_user.id
        )

        if active_session_row:
            # ... (Resuming adventure logic - unchanged) ...
            if not interaction.response.is_done():
                await interaction.response.defer() 

            loc_id = active_session_row["location_id"]
            loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone", "emoji": E.MAP})

            try:
                log_data = active_session_row["logs"]
                log = json.loads(log_data if log_data else "[]")
            except json.JSONDecodeError:
                log = ["Your adventure log was corrupted, but you can continue."]

            if not isinstance(log, list):
                log = ["Adventure log corrupted. Resuming."]

            log = log[-10:]

            resume_description = (
                "Your previous session has been recovered. You can continue "
                "exploring or return to the city."
            )

            embed = discord.Embed(
                title=f"{loc_data.get('emoji', E.MAP)} Resuming Adventure: {loc_data['name']}",
                description=resume_description,
                color=discord.Color.green(),
            )
            
            stats_json = await asyncio.to_thread(
                self.db.get_player_stats_json, self.interaction_user.id
            )
            player_stats = PlayerStats.from_dict(stats_json)
            vitals = await asyncio.to_thread(
                self.db.get_player_vitals, self.interaction_user.id
            )

            embed.add_field(
                name="Vitals",
                value=(
                    f"> {E.HP} **HP:** {vitals['current_hp']} / {player_stats.max_hp}\n"
                    f"> {E.MP} **MP:** {vitals['current_mp']} / {player_stats.max_mp}"
                ),
                inline=True
            )
            
            embed.set_footer(text="Your previous session was recovered.")

            view = ExplorationView(
                self.db,
                adventure_cog.manager,
                loc_id,
                log,
                self.interaction_user,
                player_stats
            )
            # Make the "Return to City" button go to the main profile
            view.leave_button.callback = back_to_profile_callback
            await interaction.edit_original_response(embed=embed, view=view)
            return

        # --- Original logic: No active session, show setup ---
        await interaction.response.defer()
        
        guild_member = await asyncio.to_thread(self.db.get_guild_member_data, self.interaction_user.id)
        player_rank = guild_member['rank'] if guild_member else 'F'
        
        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description="You stand before the city gates, the Guild's clearance seal in your hand. The wilderness beyond the walls of Ashgrave awaits.\n\nSelect a destination.",
            color=discord.Color.dark_green(),
        )
        
        view = AdventureSetupView(self.db, adventure_cog.manager, self.interaction_user, player_rank)
        # Make the view's back button go to the main profile
        view.back_button.callback = back_to_profile_callback
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Quest Log",
        style=discord.ButtonStyle.primary,
        custom_id="profile_quest_log",
        emoji=E.QUEST_SCROLL,
        row=1,
    )
    async def quest_log_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Quest Log UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem
        from .quest_hub_cog import QuestLogView

        quest_system = QuestSystem(self.db)
        
        active_quests = await asyncio.to_thread(
            quest_system.get_player_quests, self.interaction_user.id
        )

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
            # ... (logic to add quest fields - unchanged) ...
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
        # Set the back button to go all the way to the main profile
        view.set_back_button(back_to_profile_callback, "Back to Character")
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Guild Hall",
        style=discord.ButtonStyle.primary,
        custom_id="profile_guild_hall",
        emoji="🏦",
        row=1,
    )
    async def guild_hall_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        """
        Edits the message to show the Guild Hall (sub-menu) UI.
        """
        # This function is already async!
        await back_to_guild_hall_callback(interaction)


# ======================================================================
# INVENTORY & SKILLS (CHILD VIEWS)
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

        success, message = await asyncio.to_thread(
            self.eq_manager.equip_item, self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.unequip_select.values[0])

        success, message = await asyncio.to_thread(
            self.eq_manager.unequip_item, self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.use_select.values[0])

        success, message = await asyncio.to_thread(
            self.con_manager.use_item, self.interaction_user.id, inv_db_id
        )

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def _refresh_view(self, interaction: discord.Interaction):
        """Re-builds the embed and view to show changes."""

        items = await asyncio.to_thread(
            self.inv_manager.get_inventory, self.interaction_user.id
        )
        embed = await asyncio.to_thread(build_inventory_embed, items)

        new_view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=self.previous_view_callback,
            previous_view_label=self.previous_view_label,
        )

        await interaction.edit_original_response(embed=embed, view=new_view)


class SkillsView(View):
    """
    A simple view that just shows the "Back" button.
    The callback is set by the parent view.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        self.back_button = Button(
            label="Back to Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
        )
        self.add_item(self.back_button)

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