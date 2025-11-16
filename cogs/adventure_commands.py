"""
adventure_commands.py

This cog initializes the AdventureManager and provides the UI
views for starting and managing active, turn-by-turn exploration.
"""

import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
import sqlite3 # <-- Added for type hinting

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager
import game_systems.data.emojis as E

# --- Local Imports ---
from .ui_helpers import back_to_profile_callback, build_inventory_embed

# --- View Imports ---
# (Import moved into callbacks to prevent circular import)


class AdventureCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.manager = AdventureManager(self.db, bot)
        self.inventory_manager = InventoryManager(self.db)

    # --- NO COMMANDS ---


class AdventureSetupView(View):
    """
    View 1: The player selects their destination.
    This view is shown when "Start Adventure" is clicked on the profile.
    """

    def __init__(self, db, manager, interaction_user: discord.User, player_rank: str):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user

        self.location_select = Select(
            placeholder="Choose a Zone...", min_values=1, max_values=1, row=0
        )

        for loc_id, loc_data in LOCATIONS.items():
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
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def location_callback(self, interaction: discord.Interaction):
        """
        Callback for when a location is selected.
        This edits the message to show the main ExplorationView.
        """
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS[loc_id]

        await asyncio.to_thread(
            self.manager.start_adventure,
            interaction.user.id,
            loc_id,
            duration_minutes=-1
        )

        stats_json = await asyncio.to_thread(
            self.db.get_player_stats_json, interaction.user.id
        )
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = await asyncio.to_thread(
            self.db.get_player_vitals, interaction.user.id
        )

        initial_log = [
            f"You step past the threshold into the {loc_data['name']}. The air feels different."
        ]

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}",
            description="\n".join(initial_log),
            color=discord.Color.green(),
        )

        # Add the Vitals field (with user's formatting)
        embed.add_field(
            name="Vitals",
            value=(
                f"> {E.HP} **HP:** {vitals['current_hp']} / {player_stats.max_hp}\n"
                f"> {E.MP} **MP:** {vitals['current_mp']} / {player_stats.max_mp}"
            ),
            inline=True
        )

        view = ExplorationView(
            self.db,
            self.manager,
            loc_id,
            initial_log,
            self.interaction_user,
            player_stats
        )

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        label="Back to Profile",
        style=discord.ButtonStyle.grey,
        custom_id="back_to_profile",
        row=1,
    )
    async def back_to_profile(self, interaction: discord.Interaction, button: Button):
        await back_to_profile_callback(interaction, is_new_message=False)


class ExplorationView(View):
    """
    View 2: This is the main exploration UI.
    """

    def __init__(
        self,
        db,
        manager,
        location_id,
        log: list,
        interaction_user: discord.User,
        player_stats: PlayerStats
    ):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log
        self.log_limit = 10
        self.interaction_user = interaction_user
        self.inv_manager = InventoryManager(self.db)
        self.player_stats = player_stats

        self.explore_button = Button(
            label="Explore",
            style=discord.ButtonStyle.success,
            custom_id="adv_explore",
            emoji="⚔️",
            row=0,
        )
        self.inventory_button = Button(
            label="Inventory",
            style=discord.ButtonStyle.secondary,
            custom_id="adv_inventory",
            emoji=E.BACKPACK,
            row=0,
        )
        self.leave_button = Button(
            label="Return to City",
            style=discord.ButtonStyle.danger,
            custom_id="adv_leave",
            emoji="⬅️",
            row=0,
        )
        
        self.explore_button.callback = self.explore_callback
        self.add_item(self.explore_button)
        self.inventory_button.callback = self.inventory_callback
        self.add_item(self.inventory_button)
        self.leave_button.callback = self.leave_callback
        self.add_item(self.leave_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    # --- NEW HELPER FUNCTION ---
    def _update_embed_fields(
        self,
        embed: discord.Embed,
        vitals: sqlite3.Row,
        session_row: sqlite3.Row
    ):
        """Clears and redraws the embed fields for Vitals and Monster Vitals."""
        embed.clear_fields()
        
        # 1. Add Player Vitals
        embed.add_field(
            name="Vitals",
            value=(
                f"> {E.HP} **HP:** {vitals['current_hp']} / {self.player_stats.max_hp}\n"
                f"> {E.MP} **MP:** {vitals['current_mp']} / {self.player_stats.max_mp}"
            ),
            inline=True
        )

        # 2. Add Monster Vitals (if one is active)
        active_monster = None
        if session_row and session_row["active_monster_json"]:
            try:
                active_monster = json.loads(session_row["active_monster_json"])
            except json.JSONDecodeError:
                active_monster = None

        if active_monster:
            embed.add_field(
                name="Monster Vitals",
                value=(
                    f"> 👹 **HP:** {active_monster['HP']} / {active_monster['max_hp']}"
                ),
                inline=True
            )
    # --- END HELPER FUNCTION ---

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The player takes an action (step) in the dungeon.

        Behavior implemented:
        - Show step log entries one-by-one for pacing.
        - Vitals (player HP/MP and monster HP) are updated ONLY AFTER the step completes,
          and only if they actually changed compared to the snapshot taken before the step.
        """
        await interaction.response.defer()

        # Disable buttons while action is processed
        self.explore_button.disabled = True
        self.inventory_button.disabled = True
        self.leave_button.disabled = True
        await interaction.edit_original_response(view=self)

        # --- Snapshot vitals and session BEFORE the step ---
        prev_vitals, prev_session = await asyncio.gather(
            asyncio.to_thread(self.db.get_player_vitals, interaction.user.id),
            asyncio.to_thread(self.manager.get_active_session, interaction.user.id),
        )

        # Extract previous monster HP if present
        prev_mon_hp = None
        if prev_session and prev_session.get("active_monster_json"):
            try:
                prev_mon_hp = json.loads(prev_session["active_monster_json"]).get("HP")
            except Exception:
                prev_mon_hp = None

        # --- Run the step (this may produce multiple log lines) ---
        result = await asyncio.to_thread(
            self.manager.simulate_adventure_step,
            interaction.user.id
        )

        log_entries = result.get("log", ["An unknown error occurred."])
        is_dead = result.get("dead", False)

        # We'll need the original embed to copy its static fields while we stream logs
        original_embed = interaction.message.embeds[0]
        original_fields = list(original_embed.fields)  # copy so we can re-add them each update

        # --- Stream log entries (pacing) but DO NOT change vitals yet ---
        for entry in log_entries:
            self.log.append(entry)
            if len(self.log) > self.log_limit:
                self.log = self.log[-self.log_limit:]

            # Rebuild a fresh embed for reliability and to avoid caching quirks
            embed = discord.Embed(
                title=original_embed.title,
                description="\n".join(self.log),
                color=original_embed.color
            )

            # Re-add original fields (these still show the previous vitals until we update them below)
            for f in original_fields:
                # Use the field's attributes to re-add (name, value, inline)
                embed.add_field(name=f.name, value=f.value, inline=f.inline)

            # Push this log update
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.2)  # pacing for readability

        # --- After the entire step finishes, fetch final vitals & session once ---
        final_vitals, final_session = await asyncio.gather(
            asyncio.to_thread(self.db.get_player_vitals, interaction.user.id),
            asyncio.to_thread(self.manager.get_active_session, interaction.user.id),
        )

        # Extract final monster HP if present
        final_mon_hp = None
        if final_session and final_session.get("active_monster_json"):
            try:
                final_mon_hp = json.loads(final_session["active_monster_json"]).get("HP")
            except Exception:
                final_mon_hp = None

        # Compare snapshots to determine whether to update vitals fields
        player_hp_changed = final_vitals["current_hp"] != prev_vitals["current_hp"]
        player_mp_changed = final_vitals["current_mp"] != prev_vitals["current_mp"]
        monster_hp_changed = final_mon_hp != prev_mon_hp

        # Only rebuild fields if there's a change (Option C)
        embed = discord.Embed(
            title=original_embed.title,
            description="\n".join(self.log),
            color=original_embed.color
        )

        if player_hp_changed or player_mp_changed or monster_hp_changed:
            # Refresh player_stats in case max_hp/max_mp changed during the step
            stats_json = await asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
            try:
                self.player_stats = PlayerStats.from_dict(stats_json)
            except Exception:
                # keep existing if parse fails
                pass

            # Update the fields to reflect final vitals & monster
            self._update_embed_fields(embed, final_vitals, final_session)
        else:
            # No vitals changed — re-add the original fields as-is
            for f in original_fields:
                embed.add_field(name=f.name, value=f.value, inline=f.inline)

        # --- End of step — if dead, handle defeat specially ---
        if is_dead:
            embed.color = discord.Color.red()
            embed.set_footer(text="You have been defeated! Your adventure is over.")

            self.explore_button.disabled = True
            self.inventory_button.disabled = True
            self.leave_button.disabled = False  # allow leaving

            await interaction.edit_original_response(embed=embed, view=self)

            death_embed = discord.Embed(
                title=f"{E.DEFEAT} Defeated!",
                description="You were recovered by the Guild. Your adventure is over.",
                color=discord.Color.dark_red(),
            )
            # Send non-ephemeral death message so the user notices
            await interaction.followup.send(embed=death_embed, ephemeral=False)
            return

        # --- If not dead, re-enable buttons and persist final display ---
        self.explore_button.disabled = False
        self.inventory_button.disabled = False
        self.leave_button.disabled = False
        await interaction.edit_original_response(embed=embed, view=self)

    # --- END OF explore_callback ---

    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Opens the inventory UI from the exploration view.
        """
        from .character_cog import InventoryView

        await interaction.response.defer()
        
        items = await asyncio.to_thread(
            self.inv_manager.get_inventory, interaction.user.id
        )
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            db_manager=self.db,
            interaction_user=self.interaction_user,
            previous_view_callback=self.back_to_exploration_callback,
            previous_view_label="Back to Adventure",
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def back_to_exploration_callback(self, interaction: discord.Interaction):
        """
        A custom callback function that returns to *this* exploration view.
        """
        await interaction.response.defer()

        # --- MODIFIED: Must fetch all data to rebuild embed correctly ---
        vitals_task = asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)
        session_row_task = asyncio.to_thread(self.manager.get_active_session, self.interaction_user.id)
        
        vitals, session_row = await asyncio.gather(vitals_task, session_row_task)
        # --- END MODIFIED ---

        embed = discord.Embed(
            title=f"{LOCATIONS[self.location_id].get('emoji', E.MAP)} Exploring: {LOCATIONS[self.location_id]['name']}",
            description="\n".join(self.log),
            color=discord.Color.green(),
        )

        # --- NEW: Rebuild fields using the helper ---
        # We can re-use self.player_stats as it's stored on the view
        self._update_embed_fields(embed, vitals, session_row)
        # --- END NEW ---

        new_view = ExplorationView(
            self.db,
            self.manager,
            self.location_id,
            self.log,
            self.interaction_user,
            self.player_stats
        )

        await interaction.edit_original_response(embed=embed, view=new_view)

    async def leave_callback(self, interaction: discord.Interaction):
        """
        The player decides to leave the adventure and return to the Guild Hall.
        """
        await interaction.response.defer()

        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)

        embed = discord.Embed(
            title="Returned to City",
            description="You safely return to Ashgrave City. Your journey is over... for now.",
            color=discord.Color.blue(),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)
        
        await back_to_profile_callback(interaction, is_new_message=False)


async def setup(bot):
    await bot.add_cog(AdventureCommands(bot))
