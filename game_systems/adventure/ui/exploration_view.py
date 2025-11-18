"""
game_systems/adventure/ui/exploration_view.py

Primary gameplay interface for field exploration.
Refactored to support "Dramatic Timing", dynamic "Start Battle" button state,
and "In Battle" disabled state for ALL buttons during animation.
"""

import asyncio
import json

import discord
from discord.ui import Button, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback, build_inventory_embed
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.player_stats import PlayerStats

from .adventure_embeds import AdventureEmbeds


class ExplorationView(View):
    """
    The core exploration UI for traversing Eldoria’s wilderness.
    """

    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        location_id: str,
        log: list,
        interaction_user: discord.User,
        player_stats: PlayerStats,
        active_monster: dict = None,
    ):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log or []
        self.interaction_user = interaction_user
        self.player_stats = player_stats
        self.inv_manager = InventoryManager(self.db)
        self.active_monster = active_monster

        # -------------------------------------------------------------
        # BUTTONS
        # -------------------------------------------------------------

        # Initialize button state based on active_monster
        label, style, emoji = self._get_button_state(self.active_monster)

        self.forward_btn = Button(label=label, style=style, emoji=emoji, row=0)
        self.forward_btn.callback = self.explore_callback
        self.add_item(self.forward_btn)

        # Open inventory
        self.inventory_btn = Button(label="Field Pack", style=discord.ButtonStyle.secondary, emoji=E.BACKPACK, row=0)
        self.inventory_btn.callback = self.inventory_callback
        self.add_item(self.inventory_btn)

        # Retreat to Astraeon
        self.withdraw_btn = Button(label="Withdraw", style=discord.ButtonStyle.danger, emoji="⬅️", row=0)
        self.withdraw_btn.callback = self.leave_callback
        self.add_item(self.withdraw_btn)

    # -------------------------------------------------------------
    # HELPER: Button State
    # -------------------------------------------------------------
    def _get_button_state(self, active_monster):
        if active_monster:
            return "Start Battle", discord.ButtonStyle.danger, "⚔️"
        else:
            return "Press Forward", discord.ButtonStyle.success, "🥾"

    def _update_forward_button(self, active_monster):
        label, style, emoji = self._get_button_state(active_monster)
        self.forward_btn.label = label
        self.forward_btn.style = style
        self.forward_btn.emoji = emoji
        self.forward_btn.disabled = False

    # -------------------------------------------------------------
    # ACCESS VALIDATION
    # -------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    # -------------------------------------------------------------
    # CORE LOOP
    # -------------------------------------------------------------

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The core step of exploration.
        Simulates advancement and plays back the result with dramatic timing.
        """
        await interaction.response.defer()

        # 1. Run step simulation
        result = await asyncio.to_thread(self.manager.simulate_adventure_step, interaction.user.id)

        sequence = result.get("sequence", [])
        is_dead = result.get("dead", False)

        # Animate if multiple frames (combat)
        animate = len(sequence) > 1

        # 2. Playback Loop
        for index, block in enumerate(sequence):
            # Append to log
            self.log.extend(block)
            self.log = self.log[-15:]

            # 3. Refresh Data
            vitals_task = asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
            session_task = asyncio.to_thread(self.manager.get_active_session, interaction.user.id)
            stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)

            vitals, session_row, stats_json = await asyncio.gather(vitals_task, session_task, stats_json_task)
            self.player_stats = PlayerStats.from_dict(stats_json)

            # Parse active monster for button state
            current_monster = None
            if session_row and session_row["active_monster_json"]:
                try:
                    current_monster = json.loads(session_row["active_monster_json"])
                except Exception:
                    pass

            # --- BUTTON STATE LOGIC ---
            is_last_frame = index == len(sequence) - 1

            if is_dead and is_last_frame:
                # Dead on the last frame
                self.forward_btn.disabled = True
                self.inventory_btn.disabled = True
                self.withdraw_btn.disabled = False
            elif animate and not is_last_frame:
                # Mid-Battle: Disable ALL buttons
                self.forward_btn.label = "In Battle"
                self.forward_btn.style = discord.ButtonStyle.secondary
                self.forward_btn.emoji = "⚔️"
                self.forward_btn.disabled = True

                # Disable Field Pack and Withdraw during combat animation
                self.inventory_btn.disabled = True
                self.withdraw_btn.disabled = True
            else:
                # End of sequence: Restore proper state
                self._update_forward_button(current_monster)
                # Re-enable other buttons
                self.inventory_btn.disabled = False
                self.withdraw_btn.disabled = False

            # 4. Rebuild Embed
            embed = AdventureEmbeds.build_exploration_embed(
                self.location_id, self.log, self.player_stats, vitals, session_row
            )

            if is_dead and is_last_frame:
                embed.color = discord.Color.dark_grey()
                embed.set_footer(text="You collapse. The Adventurer’s Guild dispatches a rescue team.")

            # Update Message
            await interaction.edit_original_response(embed=embed, view=self)

            # Dramatic Pause
            if animate and not is_last_frame:
                await asyncio.sleep(1.5)

    # -------------------------------------------------------------
    # INVENTORY
    # -------------------------------------------------------------

    async def inventory_callback(self, interaction: discord.Interaction):
        """Opens the Field Pack."""
        # FIX: Import from the correct game_systems path, not the cog
        from game_systems.character.ui.inventory_view import InventoryView

        await interaction.response.defer()

        items = await asyncio.to_thread(self.inv_manager.get_inventory, interaction.user.id)
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            self.db,
            self.interaction_user,
            previous_view_callback=self.return_from_inventory,
            previous_view_label="Return to Exploration",
        )

        await interaction.edit_original_response(embed=embed, view=view)

    async def return_from_inventory(self, interaction: discord.Interaction):
        """Restores the exploration view."""
        await interaction.response.defer()

        vitals = await asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
        session_row = await asyncio.to_thread(self.manager.get_active_session, interaction.user.id)

        # Parse monster to restore button state
        current_monster = None
        if session_row and session_row["active_monster_json"]:
            try:
                current_monster = json.loads(session_row["active_monster_json"])
            except Exception:
                pass

        self._update_forward_button(current_monster)

        # Ensure other buttons are enabled when returning
        self.inventory_btn.disabled = False
        self.withdraw_btn.disabled = False

        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id, self.log, self.player_stats, vitals, session_row
        )

        await interaction.edit_original_response(embed=embed, view=self)

    # -------------------------------------------------------------
    # WITHDRAW
    # -------------------------------------------------------------

    async def leave_callback(self, interaction: discord.Interaction):
        """Ends the adventure."""
        await interaction.response.defer()

        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)

        embed = discord.Embed(
            title="Returned to Astraeon",
            description=(
                "The heavy iron gates of Astraeon close behind you, shutting out the wilds. "
                "You breathe the stale, comforting air of the city once more.\n\n"
                "**You have survived.**"
            ),
            color=discord.Color.blue(),
        )

        view = View()
        btn = Button(label="Return to Profile", style=discord.ButtonStyle.primary)

        async def return_callback(inter: discord.Interaction):
            await back_to_profile_callback(inter, is_new_message=False)

        btn.callback = return_callback
        view.add_item(btn)

        await interaction.edit_original_response(embed=embed, view=view)
