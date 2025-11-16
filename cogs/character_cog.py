"""
character_cog.py

Handles the main character UI hubs for the game (Eldoria Quest):
- CharacterTabView (The main "CHARACTER" tab)
- AbilitiesView (Sub-menu for inventory and skills)
- AdventureView (Sub-menu for quests and travel)

This file is a full, thematic rewrite to match Eldoria's dark, guild-driven, survivalist tone.
All embeds, button labels, and flavor text are written to feel like an in-world Guild interface.
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

# Local UI helpers (shared callbacks / embed builders)
from .ui_helpers import (
    back_to_profile_callback,
    back_to_guild_hall_callback,
    build_inventory_embed,
)


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def safe_avatar_url(user: discord.User):
    try:
        return user.avatar.url if getattr(user, "avatar", None) else None
    except Exception:
        return None


# ======================================================================
# CHARACTER TAB (Main "home" UI)
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
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Arcane Ledger",
        style=discord.ButtonStyle.primary,
        custom_id="profile_abilities",
        emoji="📜",
        row=0,
    )
    async def abilities_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show Abilities (Inventory/Skills) sub-menu.
        """
        await interaction.response.defer()

        embed = discord.Embed(
            title="📜 Arcane Ledger of Abilities",
            description=(
                "*You open the ledger — a heavy tome ringed with wax seals. "
                "Each entry details what an adventurer carries and what arts they command.*\n\n"
                "**Manage the following:**\n"
                "• **Inventory** — Items, materials, and consumables.\n"
                "• **Equipment** — Worn gear and relics.\n"
                "• **Skills** — Learned techniques and proven talents."
            ),
            color=discord.Color.purple(),
        )

        view = AbilitiesView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="The Road Ahead",
        style=discord.ButtonStyle.success,
        custom_id="profile_adventure",
        emoji="🗺️",
        row=0,
    )
    async def adventure_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show Adventure (Quests/Travel) sub-menu.
        """
        await interaction.response.defer()

        embed = discord.Embed(
            title="🗺️ The Road Ahead",
            description=(
                "*Beyond the enclave, the world is fractured. Each path is a test of wit, grit, and survival.*\n\n"
                "**Your choices:**\n"
                "• **Quest Log** — Review duties assigned by the Guild.\n"
                "• **Guild Hall** — Return for supplies, contracts, and counsel.\n"
                "• **Begin Expedition** — Step beyond the walls and into the wild." 
            ),
            color=discord.Color.dark_teal(),
        )

        view = AdventureView(self.db, self.interaction_user)
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Vestige & Vitals",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_status_update",
        emoji=E.VESTIGE,
        row=1,
    )
    async def status_update_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show the Status Update UI (Vestige spend / attributes).
        """
        await interaction.response.defer()

        from .status_update_cog import StatusUpdateView

        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)

        player_data, stats_json = await asyncio.gather(player_data_task, stats_json_task)
        player_stats = PlayerStats.from_dict(stats_json)

        embed = StatusUpdateView.build_status_embed(player_data, player_stats)
        view = StatusUpdateView(self.db, self.interaction_user, player_data, player_stats)
        view.back_button.callback = back_to_profile_callback

        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# ABILITIES TAB (Inventory, Skills, Skill Trainer)
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

        # Back to profile
        back_btn = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
            row=2,
        )
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        label="Inventory",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_inventory",
        emoji=E.BACKPACK,
        row=0,
    )
    async def inventory_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show Inventory UI.
        """
        await interaction.response.defer()

        items = await asyncio.to_thread(self.inventory_manager.get_inventory, self.interaction_user.id)
        embed = await asyncio.to_thread(build_inventory_embed, items)

        from .ui_helpers import build_inventory_embed as _unused  # keep import path clear

        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=back_to_profile_callback,
            previous_view_label="Return — Character",
        )
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Tome of Skills",
        style=discord.ButtonStyle.secondary,
        custom_id="profile_skills",
        emoji="✨",
        row=0,
    )
    async def skills_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show Skills UI.
        """
        await interaction.response.defer()

        player_skills = await asyncio.to_thread(self.db.get_player_skills, self.interaction_user.id)

        if not player_skills:
            skills_str = "No recorded techniques. Seek tutors and trials to learn more."
        else:
            skills_str = "\n".join(
                [f"• **{s['name']}** (Lv. {s['skill_level']}) — *{s['type']}*" for s in player_skills]
            )

        embed = discord.Embed(
            title="📖 Tome of Skills",
            description=(
                "*The pages list your practiced arts and the marks of those who taught you.*\n\n"
                f"{skills_str}"
            ),
            color=discord.Color.purple(),
        )

        view = SkillsView(self.db, self.interaction_user)
        view.back_button.callback = back_to_profile_callback
        await interaction.edit_original_response(embed=embed, view=view)


# ======================================================================
# ADVENTURE TAB (Quest Log, Guild Hall, Expedition)
# ======================================================================

class AdventureView(View):
    """
    Sub-menu for Quest Log, Guild Hall, and Starting Adventures.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        back_btn = Button(
            label="Return — Character",
            style=discord.ButtonStyle.grey,
            custom_id="back_to_profile",
            row=2,
        )
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        label="Begin Expedition",
        style=discord.ButtonStyle.success,
        custom_id="profile_start_adventure",
        emoji="⚔️",
        row=0,
    )
    async def start_adventure_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show Expedition setup or resume an active adventure.
        """
        from .adventure_commands import AdventureSetupView, ExplorationView
        from game_systems.data.adventure_locations import LOCATIONS
        import game_systems.data.emojis as E
        import json

        adventure_cog = interaction.client.get_cog("AdventureCommands")
        if not adventure_cog:
            await interaction.response.send_message(f"{E.ERROR} Adventure system is offline.", ephemeral=True)
            return

        active_session_row = await asyncio.to_thread(adventure_cog.manager.get_active_session, self.interaction_user.id)

        if active_session_row:
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
                "*Your last expedition was recovered from the Guild's archives. "
                "You may continue where you left or return to the enclave.*"
            )

            embed = discord.Embed(
                title=f"{loc_data.get('emoji', E.MAP)} Resuming Expedition: {loc_data['name']}",
                description=resume_description,
                color=discord.Color.green(),
            )

            stats_json = await asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
            player_stats = PlayerStats.from_dict(stats_json)
            vitals = await asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)

            embed.add_field(
                name="Vitals",
                value=(
                    f"> {E.HP} **HP:** {vitals['current_hp']} / {player_stats.max_hp}\n"
                    f"> {E.MP} **MP:** {vitals['current_mp']} / {player_stats.max_mp}"
                ),
                inline=True,
            )

            embed.set_footer(text="Your previous session was recovered.")

            view = ExplorationView(
                self.db,
                adventure_cog.manager,
                loc_id,
                log,
                self.interaction_user,
                player_stats,
            )
            
            # --- THIS IS THE FIX ---
            # The button on ExplorationView is named 'withdraw_btn'
            view.withdraw_btn.callback = back_to_profile_callback
            # --- END OF FIX ---
            
            await interaction.edit_original_response(embed=embed, view=view)
            return

        # No active session: show setup
        await interaction.response.defer()

        guild_member = await asyncio.to_thread(self.db.get_guild_member_data, self.interaction_user.id)
        player_rank = guild_member['rank'] if guild_member else 'F'

        embed = discord.Embed(
            title=f"{E.MAP} Prepare for Expedition",
            description=(
                "*The city gates stand heavy. You check your clearance and consider the threats beyond —"
                " the ash-swept wilds, the Veil-rifts, and things shaped by The Sundering.*\n\n"
                "Select a destination and ready your provisions."
            ),
            color=discord.Color.dark_green(),
        )

        view = AdventureSetupView(self.db, adventure_cog.manager, self.interaction_user, player_rank)
        
        # --- THIS IS THE FIRST FIX (which you already applied) ---
        # The button on AdventureSetupView is named 'back_to_profile'
        view.back_to_profile.callback = back_to_profile_callback
        # --- END OF FIX ---
        
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Quest Ledger",
        style=discord.ButtonStyle.primary,
        custom_id="profile_quest_log",
        emoji=E.QUEST_SCROLL,
        row=1,
    )
    async def quest_log_callback(self, interaction: discord.Interaction, button: Button):
        """
        Show the Quest Log UI.
        """
        await interaction.response.defer()
        from game_systems.guild_system.quest_system import QuestSystem
        from .quest_hub_cog import QuestLogView

        quest_system = QuestSystem(self.db)
        active_quests = await asyncio.to_thread(quest_system.get_player_quests, self.interaction_user.id)

        embed = discord.Embed(
            title=f"{E.QUEST_SCROLL} Adventurer's Ledger",
            description=(
                "*You unfurl the ledger entries that bind you to the Guild's tasks.*\n\n"
                "A review of your currently accepted assignments."
            ),
            color=discord.Color.from_rgb(139, 69, 19),
        )

        if not active_quests:
            embed.add_field(
                name="No Active Contracts",
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
        view.set_back_button(back_to_profile_callback, "Return — Character")
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Guild Hall",
        style=discord.ButtonStyle.primary,
        custom_id="profile_guild_hall",
        emoji="🏦",
        row=1,
    )
    async def guild_hall_callback(self, interaction: discord.Interaction, button: Button):
        """
        Route to the Guild Hall (sub-menu).
        """
        await back_to_guild_hall_callback(interaction)


# ======================================================================
# INVENTORY & SKILLS CHILD VIEWS
# ======================================================================

class InventoryView(View):
    """
    Dynamic view for the inventory: equip, unequip, use items.
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

        self.equip_select = Select(placeholder="Equip an item...", min_values=1, max_values=1, row=0)
        self.unequip_select = Select(placeholder="Unequip an item...", min_values=1, max_values=1, row=1)
        self.use_select = Select(placeholder="Use an item...", min_values=1, max_values=1, row=2)
        self.back_button = Button(label=self.previous_view_label, style=discord.ButtonStyle.secondary, row=3)

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
        # Synchronous call intentionally; selects are populated on initialization.
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
                label = f"{item['item_name']} ({item['slot']})"
                if item.get("equipped") == 1:
                    unequip_options.append(discord.SelectOption(label=label, value=value, emoji="🛡️"))
                else:
                    equip_options.append(discord.SelectOption(label=label, value=value, emoji="⚔️"))

            elif item_type == "consumable":
                use_options.append(discord.SelectOption(label=label, value=value, emoji="🧪"))

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
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def equip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.equip_select.values[0])

        success, message = await asyncio.to_thread(self.eq_manager.equip_item, self.interaction_user.id, inv_db_id)

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def unequip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.unequip_select.values[0])

        success, message = await asyncio.to_thread(self.eq_manager.unequip_item, self.interaction_user.id, inv_db_id)

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def use_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        inv_db_id = int(self.use_select.values[0])

        success, message = await asyncio.to_thread(self.con_manager.use_item, self.interaction_user.id, inv_db_id)

        await interaction.followup.send(message, ephemeral=True)
        await self._refresh_view(interaction)

    async def _refresh_view(self, interaction: discord.Interaction):
        """Re-builds the embed and view to show changes."""
        items = await asyncio.to_thread(self.inv_manager.get_inventory, self.interaction_user.id)
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
    A simple view that shows the player's skills and a back button.
    """

    def __init__(self, db_manager: DatabaseManager, interaction_user: discord.User):
        super().__init__(timeout=None)
        self.db = db_manager
        self.interaction_user = interaction_user

        self.back_button = Button(label="Return — Character", style=discord.ButtonStyle.grey, custom_id="back_to_profile")
        self.add_item(self.back_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
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