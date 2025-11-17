"""
game_systems/adventure/ui/exploration_view.py

Primary gameplay interface for field exploration.

Buttons:
- Press Forward
- Field Pack
- Withdraw
"""

import discord
from discord.ui import View, Button
import asyncio
import json

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.player.player_stats import PlayerStats
from game_systems.items.inventory_manager import InventoryManager

from cogs.ui_helpers import back_to_profile_callback, build_inventory_embed
from .adventure_embeds import AdventureEmbeds
import game_systems.data.emojis as E


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
    ):
        super().__init__(timeout=None)
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log or []
        self.interaction_user = interaction_user
        self.player_stats = player_stats

        self.inv_manager = InventoryManager(self.db)

        # -------------------------------------------------------------
        # BUTTONS
        # -------------------------------------------------------------

        # Advance deeper into the region
        self.forward_btn = Button(
            label="Press Forward",
            style=discord.ButtonStyle.success,
            emoji="⚔️",
            row=0
        )
        self.forward_btn.callback = self.explore_callback
        self.add_item(self.forward_btn)

        # Open inventory
        self.inventory_btn = Button(
            label="Field Pack",
            style=discord.ButtonStyle.secondary,
            emoji=E.BACKPACK,
            row=0
        )
        self.inventory_btn.callback = self.inventory_callback
        self.add_item(self.inventory_btn)

        # Retreat to Astraeon
        self.withdraw_btn = Button(
            label="Withdraw",
            style=discord.ButtonStyle.danger,
            emoji="⬅️",
            row=0
        )
        self.withdraw_btn.callback = self.leave_callback
        self.add_item(self.withdraw_btn)

    # -------------------------------------------------------------
    # ACCESS VALIDATION
    # -------------------------------------------------------------

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    # -------------------------------------------------------------
    # CORE LOOP
    # -------------------------------------------------------------

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The core step of exploration.
        Simulates one advancement into the wilderness (encounters, events, etc.).
        """
        await interaction.response.defer()

        # 1. Run step simulation
        result = await asyncio.to_thread(
            self.manager.simulate_adventure_step, interaction.user.id
        )

        # 2. Append new log lines
        new_lines = result.get("log", [])
        self.log.extend(new_lines)
        self.log = self.log[-15:]  # Keep log concise but contextual

        # 3. Refresh all vital data
        vitals_task = asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
        session_task = asyncio.to_thread(self.manager.get_active_session, interaction.user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)

        vitals, session_row, stats_json = await asyncio.gather(
            vitals_task, session_task, stats_json_task
        )
        self.player_stats = PlayerStats.from_dict(stats_json)

        # 4. Rebuild the exploration embed
        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id,
            self.log,
            self.player_stats,
            vitals,
            session_row
        )

        # ---------------------------------------------------------
        # Handle Death
        # ---------------------------------------------------------
        if result.get("dead", False):
            self.forward_btn.disabled = True
            self.inventory_btn.disabled = True
            self.withdraw_btn.disabled = False  # Still allow retreat

            embed.color = discord.Color.dark_grey()
            embed.set_footer(text="You collapse. The Adventurer’s Guild dispatches a rescue team.")

            # Update main message
            await interaction.edit_original_response(embed=embed, view=self)
            
            # We purposefully avoid an ephemeral message here, as the embed
            # state ("You collapse") is sufficient and persistent.
            return

        await interaction.edit_original_response(embed=embed, view=self)

    # -------------------------------------------------------------
    # INVENTORY
    # -------------------------------------------------------------

    async def inventory_callback(self, interaction: discord.Interaction):
        """
        Opens the Field Pack (Inventory View).
        """
        from cogs.character_cog import InventoryView  # avoid circular import

        await interaction.response.defer()

        items = await asyncio.to_thread(self.inv_manager.get_inventory, interaction.user.id)
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            self.db,
            self.interaction_user,
            previous_view_callback=self.return_from_inventory,
            previous_view_label="Return to Exploration"
        )

        await interaction.edit_original_response(embed=embed, view=view)

    async def return_from_inventory(self, interaction: discord.Interaction):
        """
        Restores the exploration view after closing the inventory.
        """
        await interaction.response.defer()

        vitals = await asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
        session_row = await asyncio.to_thread(self.manager.get_active_session, interaction.user.id)

        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id,
            self.log,
            self.player_stats,
            vitals,
            session_row
        )

        await interaction.edit_original_response(embed=embed, view=self)

    # -------------------------------------------------------------
    # WITHDRAW
    # -------------------------------------------------------------

    async def leave_callback(self, interaction: discord.Interaction):
        """
        Ends the adventure session and transitions to a persistent summary view.
        """
        await interaction.response.defer()

        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)

        embed = discord.Embed(
            title="Returned to Astraeon",
            description=(
                "The heavy iron gates of Astraeon close behind you, shutting out the wilds. "
                "You breathe the stale, comforting air of the city once more.\n\n"
                "**You have survived.**"
            ),
            color=discord.Color.blue()
        )
        
        # Create a temporary, minimal view just to get back to the profile
        # This replaces the ephemeral message.
        view = View()
        btn = Button(label="Return to Profile", style=discord.ButtonStyle.primary)
        
        async def return_callback(inter: discord.Interaction):
            await back_to_profile_callback(inter, is_new_message=False)
            
        btn.callback = return_callback
        view.add_item(btn)

        await interaction.edit_original_response(embed=embed, view=view)