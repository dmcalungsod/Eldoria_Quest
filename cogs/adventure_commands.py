"""
cogs/adventure_commands.py

Adventure UI & commands for Eldoria Quest.

This file provides:
- AdventureCommands cog (manages AdventureManager instance)
- AdventureSetupView (choose destination)
- ExplorationView (turn-by-turn exploration UI)

All labels and embeds are written to match the Adventurer's Guild tone:
grim, pragmatic, survivalist — literary but UI-friendly.

Button label theme replacements applied:
- Explore -> Press Forward
- Inventory -> Field Pack
- Return to City -> Withdraw to Astraeon
- Back to Profile -> Return to Ledger
- Back to Adventure -> Return to the Wilds
"""

import json
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import sqlite3  # for typing hints
from typing import Optional, List

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# Local helpers (shared)
from .ui_helpers import back_to_profile_callback, build_inventory_embed


# ---------------------------------------------------------------------
# AdventureCommands Cog
# ---------------------------------------------------------------------
class AdventureCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)
        self.inventory_manager = InventoryManager(self.db)


# ---------------------------------------------------------------------
# Adventure Setup View (choose destination)
# ---------------------------------------------------------------------
class AdventureSetupView(View):
    """
    The player selects their destination. Shown when starting an expedition.
    """

    def __init__(self, db: DatabaseManager, manager: AdventureManager, interaction_user: discord.User, player_rank: str):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user
        self.player_rank = player_rank

        self.location_select = Select(
            placeholder="Choose a Zone...",
            min_values=1,
            max_values=1,
            row=0,
        )

        for loc_id, loc_data in LOCATIONS.items():
            # Only show locations that are available (rank check can be enforced elsewhere)
            self.location_select.add_option(
                label=loc_data["name"],
                value=loc_id,
                description=f"Lv.{loc_data['level_req']} (Rank {loc_data['min_rank']})",
                emoji=loc_data.get("emoji", E.MAP),
            )

        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def location_callback(self, interaction: discord.Interaction):
        """
        Start an adventure session at the selected location and switch to ExplorationView.
        """
        await interaction.response.defer()

        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone", "emoji": E.MAP})

        # Start the adventure (run in thread)
        await asyncio.to_thread(self.manager.start_adventure, interaction.user.id, loc_id, duration_minutes=-1)

        stats_json = await asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = await asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)

        initial_log = [f"You step beyond the enclave into the {loc_data['name']}. The air tastes of old magic and ash."]

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}",
            description="\n".join(initial_log),
            color=discord.Color.dark_green(),
        )

        embed.add_field(
            name="Vitals",
            value=(
                f"> {E.HP} **HP:** {vitals['current_hp']} / {player_stats.max_hp}\n"
                f"> {E.MP} **MP:** {vitals['current_mp']} / {player_stats.max_mp}"
            ),
            inline=True,
        )

        view = ExplorationView(
            self.db,
            self.manager,
            loc_id,
            initial_log,
            self.interaction_user,
            player_stats,
        )

        # Use edit_message to replace the setup with exploration UI
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(
        label="Return to Ledger",
        style=discord.ButtonStyle.grey,
        custom_id="adv_back_to_profile",
        row=1,
    )
    async def back_to_profile(self, interaction: discord.Interaction, button: Button):
        # Return to the main character profile (not a new message)
        await back_to_profile_callback(interaction, is_new_message=False)


# ---------------------------------------------------------------------
# Exploration View (main exploration UI)
# ---------------------------------------------------------------------
class ExplorationView(View):
    """
    The main exploration UI used while an expedition is active.
    Buttons:
      - Press Forward (advance/explore)
      - Field Pack (open inventory)
      - Withdraw to Astraeon (end expedition and return)
    """

    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        location_id: str,
        log: List[str],
        interaction_user: discord.User,
        player_stats: PlayerStats,
    ):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log or []
        self.log_limit = 10
        self.interaction_user = interaction_user
        self.inv_manager = InventoryManager(self.db)
        self.player_stats = player_stats

        # Thematic button labels
        self.press_forward_btn = Button(
            label="Press Forward",
            style=discord.ButtonStyle.success,
            custom_id="adv_press_forward",
            emoji="⚔️",
            row=0,
        )
        self.field_pack_btn = Button(
            label="Field Pack",
            style=discord.ButtonStyle.secondary,
            custom_id="adv_field_pack",
            emoji=E.BACKPACK,
            row=0,
        )
        self.withdraw_btn = Button(
            label="Withdraw to Astraeon",
            style=discord.ButtonStyle.danger,
            custom_id="adv_withdraw",
            emoji="⬅️",
            row=0,
        )

        self.press_forward_btn.callback = self.explore_callback
        self.field_pack_btn.callback = self.inventory_callback
        self.withdraw_btn.callback = self.leave_callback

        self.add_item(self.press_forward_btn)
        self.add_item(self.field_pack_btn)
        self.add_item(self.withdraw_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    # Helper: re-draw vitals & monster fields on an embed
    def _update_embed_fields(self, embed: discord.Embed, vitals_row: sqlite3.Row, session_row: Optional[sqlite3.Row]):
        """
        Clears existing fields and draws up-to-date Vitals and Monster Vitals (if present).
        """
        embed.clear_fields()

        # Player vitals
        embed.add_field(
            name="Vitals",
            value=(
                f"> {E.HP} **HP:** {vitals_row['current_hp']} / {self.player_stats.max_hp}\n"
                f"> {E.MP} **MP:** {vitals_row['current_mp']} / {self.player_stats.max_mp}"
            ),
            inline=True,
        )

        # Monster vitals if active monster present
        active_monster = None
        if session_row and session_row.get("active_monster_json"):
            try:
                active_monster = json.loads(session_row["active_monster_json"])
            except Exception:
                active_monster = None

        if active_monster:
            embed.add_field(
                name="Monster Vitals",
                value=f"> 👹 **HP:** {active_monster.get('HP', '?')} / {active_monster.get('max_hp', '?')}",
                inline=True,
            )

    async def explore_callback(self, interaction: discord.Interaction):
        """
        Advance the expedition one 'step'. Streams log entries, then updates vitals.
        """
        await interaction.response.defer()

        # Disable buttons while processing
        self.press_forward_btn.disabled = True
        self.field_pack_btn.disabled = True
        self.withdraw_btn.disabled = True
        await interaction.edit_original_response(view=self)

        # Snapshot vitals & session BEFORE the step
        prev_vitals, prev_session = await asyncio.gather(
            asyncio.to_thread(self.db.get_player_vitals, interaction.user.id),
            asyncio.to_thread(self.manager.get_active_session, interaction.user.id),
        )

        prev_mon_hp = None
        if prev_session and prev_session.get("active_monster_json"):
            try:
                prev_mon_hp = json.loads(prev_session["active_monster_json"]).get("HP")
            except Exception:
                prev_mon_hp = None

        # Perform the adventure step (may be blocking -> run in thread)
        result = await asyncio.to_thread(self.manager.simulate_adventure_step, interaction.user.id)

        log_entries = result.get("log", ["The shadows do nothing."])
        is_dead = result.get("dead", False)

        # Copy original embed static parts to preserve title/color
        original_embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else None
        base_title = original_embed.title if original_embed else f"{LOCATIONS.get(self.location_id, {}).get('emoji', E.MAP)} Exploring"
        base_color = original_embed.color if original_embed else discord.Color.dark_green()

        # Stream logs for readability
        for entry in log_entries:
            self.log.append(entry)
            if len(self.log) > self.log_limit:
                self.log = self.log[-self.log_limit :]

            embed = discord.Embed(title=base_title, description="\n".join(self.log), color=base_color)

            # Re-add vitals/monster fields from the previous snapshot to avoid flicker
            if prev_vitals and prev_session:
                try:
                    self._update_embed_fields(embed, prev_vitals, prev_session)
                except Exception:
                    # fallback: skip
                    pass

            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.2)  # pacing for readability

        # Fetch final vitals & session after the step
        final_vitals, final_session = await asyncio.gather(
            asyncio.to_thread(self.db.get_player_vitals, interaction.user.id),
            asyncio.to_thread(self.manager.get_active_session, interaction.user.id),
        )

        final_mon_hp = None
        if final_session and final_session.get("active_monster_json"):
            try:
                final_mon_hp = json.loads(final_session["active_monster_json"]).get("HP")
            except Exception:
                final_mon_hp = None

        player_hp_changed = final_vitals["current_hp"] != prev_vitals["current_hp"]
        player_mp_changed = final_vitals["current_mp"] != prev_vitals["current_mp"]
        monster_hp_changed = final_mon_hp != prev_mon_hp

        # Build final embed (use the updated player_stats in case max changed)
        try:
            stats_json = await asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
            self.player_stats = PlayerStats.from_dict(stats_json)
        except Exception:
            # keep existing if parse fails
            pass

        embed = discord.Embed(title=base_title, description="\n".join(self.log), color=base_color)

        if player_hp_changed or player_mp_changed or monster_hp_changed:
            self._update_embed_fields(embed, final_vitals, final_session)
        else:
            # Re-add previous fields if present
            if prev_vitals and prev_session:
                try:
                    self._update_embed_fields(embed, prev_vitals, prev_session)
                except Exception:
                    pass

        # Handle death
        if is_dead:
            embed.color = discord.Color.red()
            embed.set_footer(text="You have been defeated. The Guild will recover you.")

            self.press_forward_btn.disabled = True
            self.field_pack_btn.disabled = True
            self.withdraw_btn.disabled = False
            await interaction.edit_original_response(embed=embed, view=self)

            death_embed = discord.Embed(
                title=f"{E.DEFEAT} Defeated!",
                description="You were recovered by the Adventurer's Guild. Your expedition ends here.",
                color=discord.Color.dark_red(),
            )
            await interaction.followup.send(embed=death_embed, ephemeral=False)
            return

        # Re-enable buttons and persist view
        self.press_forward_btn.disabled = False
        self.field_pack_btn.disabled = False
        self.withdraw_btn.disabled = False
        await interaction.edit_original_response(embed=embed, view=self)

    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Open the inventory (Field Pack) while exploring.
        The back button inside the InventoryView will return to this exploration view.
        """
        from .character_cog import InventoryView  # local import to avoid circular import

        await interaction.response.defer()

        items = await asyncio.to_thread(self.inv_manager.get_inventory, interaction.user.id)
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=self.back_to_exploration_callback,
            previous_view_label="Return to the Wilds",
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_exploration_callback(self, interaction: discord.Interaction):
        """
        Return from inventory to this Exploration view. Rebuilds embed with current vitals.
        """
        await interaction.response.defer()

        vitals_task = asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)
        session_task = asyncio.to_thread(self.manager.get_active_session, self.interaction_user.id)
        vitals, session_row = await asyncio.gather(vitals_task, session_task)

        loc_data = LOCATIONS.get(self.location_id, {"name": "Unknown", "emoji": E.MAP})

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}",
            description="\n".join(self.log),
            color=discord.Color.dark_green(),
        )

        # update vitals/monster fields
        try:
            self._update_embed_fields(embed, vitals, session_row)
        except Exception:
            pass

        new_view = ExplorationView(
            self.db,
            self.manager,
            self.location_id,
            self.log,
            self.interaction_user,
            self.player_stats,
        )
        await interaction.edit_original_response(embed=embed, view=new_view)

    async def leave_callback(self, interaction: discord.Interaction):
        """
        End the expedition and return to the character profile / guild hall.
        """
        await interaction.response.defer()

        # End adventure in a thread
        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)

        embed = discord.Embed(
            title="Returned to Astraeon",
            description="You withdraw to the city and the Guild's relative safety. Prepare for the next contract.",
            color=discord.Color.blue(),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)
        # Return to profile (not a new message)
        await back_to_profile_callback(interaction, is_new_message=False)


# ---------------------------------------------------------------------
# Cog setup
# ---------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(AdventureCommands(bot))
