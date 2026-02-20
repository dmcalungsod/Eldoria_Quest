"""
game_systems/adventure/ui/exploration_view.py

The main Adventure UI.
Hardened: Prevents button-mashing race conditions during combat animation.
"""

import asyncio
import json
import logging

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback, build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats

from .adventure_embeds import AdventureEmbeds

logger = logging.getLogger("eldoria.ui.exploration")


class ExplorationView(View):
    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        location_id: str,
        log: list,
        interaction_user: discord.User,
        player_stats: PlayerStats,
        vitals: dict = None,
        active_monster: dict = None,
    ):
        super().__init__(timeout=300)  # 5 minutes
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log or []
        self.interaction_user = interaction_user
        self.player_stats = player_stats
        self.vitals = vitals or {}
        self.inv_manager = InventoryManager(self.db)
        self.active_monster = active_monster
        self.processing = False

        # Button Setup
        self._update_view_state()

    def _update_view_state(self):
        self.clear_items()

        if self.active_monster:
            # --- COMBAT MODE ---

            # 1. Attack
            attack_btn = Button(label="Attack", style=discord.ButtonStyle.danger, emoji=E.SWORDS, row=0, custom_id="attack")
            attack_btn.callback = self.action_attack
            self.add_item(attack_btn)

            # 2. Defend
            defend_btn = Button(label="Defend", style=discord.ButtonStyle.secondary, emoji=E.SHIELD, row=0, custom_id="defend")
            defend_btn.callback = self.action_defend
            self.add_item(defend_btn)

            # 3. Flee
            flee_btn = Button(label="Flee", style=discord.ButtonStyle.secondary, emoji="🏃", row=0, custom_id="flee")
            flee_btn.callback = self.action_flee
            self.add_item(flee_btn)

            # 4. Pack (New Row)
            inv_btn = Button(label="Pack", style=discord.ButtonStyle.secondary, emoji=E.BACKPACK, row=1, custom_id="pack")
            inv_btn.callback = self.inventory_callback
            self.add_item(inv_btn)

        else:
            # --- EXPLORATION MODE ---

            # UX: Warn if HP is critically low (< 30%)
            current_hp = self.vitals.get("current_hp", 0)
            max_hp = max(self.player_stats.max_hp, 1)
            if (current_hp / max_hp) < 0.3:
                label, style, emoji = "Forward", discord.ButtonStyle.danger, "⚠️"
            else:
                label, style, emoji = "Forward", discord.ButtonStyle.success, "🥾"

            # 1. Forward
            forward_btn = Button(label=label, style=style, emoji=emoji, row=0, custom_id="forward")
            forward_btn.callback = self.explore_callback
            self.add_item(forward_btn)

            # 2. Pack
            inv_btn = Button(label="Pack", style=discord.ButtonStyle.secondary, emoji=E.BACKPACK, row=0, custom_id="pack")
            inv_btn.callback = self.inventory_callback
            self.add_item(inv_btn)

            # 3. Return
            leave_btn = Button(label="Return to Town", style=discord.ButtonStyle.primary, emoji="🏠", row=0, custom_id="leave")
            leave_btn.callback = self.leave_callback
            self.add_item(leave_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your session.", ephemeral=True)
            return False
        return True

    # --------------------------------------------------------
    # MAIN GAME LOOP
    # --------------------------------------------------------
    async def explore_callback(self, interaction: discord.Interaction):
        await self._perform_simulation(interaction, action=None)

    async def action_attack(self, interaction: discord.Interaction):
        await self._perform_simulation(interaction, action="attack")

    async def action_defend(self, interaction: discord.Interaction):
        await self._perform_simulation(interaction, action="defend")

    async def action_flee(self, interaction: discord.Interaction):
        await self._perform_simulation(interaction, action="flee")

    async def _perform_simulation(self, interaction: discord.Interaction, action: str = None):
        if self.processing:
            await interaction.response.send_message("Please wait...", ephemeral=True)
            return

        self.processing = True
        try:
            await interaction.response.defer()

            # 1. Disable UI immediately
            self._disable_all()
            await interaction.edit_original_response(view=self)

            # 2. Run Simulation Thread
            result = await asyncio.to_thread(self.manager.simulate_adventure_step, self.interaction_user.id, action)
            sequence = result.get("sequence", [])
            is_dead = result.get("dead", False)

            # Use optimized return data
            vitals = result.get("vitals", {"current_hp": 0, "current_mp": 0})
            self.vitals = vitals
            if result.get("player_stats"):
                self.player_stats = result["player_stats"]
            self.active_monster = result.get("active_monster")

            # 3. Animation Loop
            for i, block in enumerate(sequence):
                # Update Log
                self.log.extend(block)
                self.log = self.log[-15:]  # Keep log manageable

                # Prepare UI state
                embed = AdventureEmbeds.build_exploration_embed(
                    self.location_id, self.log, self.player_stats, vitals, self.active_monster
                )

                is_last_frame = i == len(sequence) - 1

                if is_last_frame:
                    # Refresh Buttons based on new state
                    self._update_view_state()

                    if is_dead:
                        self._disable_all()
                        embed.color = discord.Color.dark_grey()
                        embed.set_footer(text="You have fallen.")

                # Edit Message
                await interaction.edit_original_response(embed=embed, view=self)

                # Wait if animating
                if not is_last_frame:
                    await asyncio.sleep(1.5)

        except Exception as e:
            logger.error(f"Exploration error: {e}", exc_info=True)
            # Restore state
            self._update_view_state()
            await interaction.edit_original_response(view=self)
        finally:
            self.processing = False

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    # --------------------------------------------------------
    # Inventory Navigation
    # --------------------------------------------------------
    async def inventory_callback(self, interaction: discord.Interaction):
        if self.processing:
            await interaction.response.send_message("Please wait...", ephemeral=True)
            return

        self.processing = True
        try:
            # Avoid circular import
            from game_systems.character.ui.inventory_view import InventoryView

            await interaction.response.defer()

            items = await asyncio.to_thread(self.inv_manager.get_inventory, self.interaction_user.id)
            embed = build_inventory_embed(items)

            view = InventoryView(self.db, self.interaction_user, self.return_from_inventory, "Return to Adventure")
            await interaction.edit_original_response(embed=embed, view=view)
        finally:
            self.processing = False

    async def return_from_inventory(self, interaction: discord.Interaction):
        if self.processing:
            await interaction.response.send_message("Please wait...", ephemeral=True)
            return

        self.processing = True
        try:
            await interaction.response.defer()

            # Refresh state on return
            vitals = await asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)
            self.vitals = vitals or {}
            session = await asyncio.to_thread(self.manager.get_active_session, self.interaction_user.id)

            # Update monster state from session
            if session and session.get("active_monster_json"):
                try:
                    self.active_monster = json.loads(session["active_monster_json"])
                except Exception:
                    self.active_monster = None
            else:
                self.active_monster = None

            embed = AdventureEmbeds.build_exploration_embed(
                self.location_id, self.log, self.player_stats, vitals, self.active_monster
            )

            # Reset my buttons
            self._update_view_state()

            await interaction.edit_original_response(embed=embed, view=self)
        finally:
            self.processing = False

    # --------------------------------------------------------
    # Withdraw
    # --------------------------------------------------------
    async def leave_callback(self, interaction: discord.Interaction):
        if self.processing:
            await interaction.response.send_message("Please wait...", ephemeral=True)
            return

        self.processing = True
        try:
            await interaction.response.defer()
            await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)
            await back_to_profile_callback(interaction, is_new_message=False)
        finally:
            self.processing = False
