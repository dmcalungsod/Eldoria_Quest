"""
game_systems/adventure/ui/exploration_view.py

The primary gameplay view.
Buttons: [Press Forward] [Field Pack] [Withdraw]
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

        # --- BUTTONS ---
        self.forward_btn = Button(
            label="Press Forward", 
            style=discord.ButtonStyle.success, 
            emoji="⚔️", 
            row=0
        )
        self.forward_btn.callback = self.explore_callback
        self.add_item(self.forward_btn)

        self.inventory_btn = Button(
            label="Field Pack", 
            style=discord.ButtonStyle.secondary, 
            emoji=E.BACKPACK, 
            row=0
        )
        self.inventory_btn.callback = self.inventory_callback
        self.add_item(self.inventory_btn)

        self.withdraw_btn = Button(
            label="Withdraw", 
            style=discord.ButtonStyle.danger, 
            emoji="⬅️", 
            row=0
        )
        self.withdraw_btn.callback = self.leave_callback
        self.add_item(self.withdraw_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def explore_callback(self, interaction: discord.Interaction):
        """
        The Core Loop: Calls the Manager to simulate one step (Auto or Manual).
        """
        await interaction.response.defer()
        
        # 1. Execute Logic
        result = await asyncio.to_thread(self.manager.simulate_adventure_step, interaction.user.id)
        
        # 2. Update Local Log
        new_lines = result.get("log", [])
        self.log.extend(new_lines)
        self.log = self.log[-15:] # Keep context manageable

        # 3. Fetch Data for Re-render
        # We fetch stats again in case level up happened during step
        vitals_task = asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
        session_task = asyncio.to_thread(self.manager.get_active_session, interaction.user.id)
        stats_json_task = asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
        
        vitals, session_row, stats_json = await asyncio.gather(
            vitals_task, session_task, stats_json_task
        )
        self.player_stats = PlayerStats.from_dict(stats_json)

        # 4. Rebuild Embed
        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id, self.log, self.player_stats, vitals, session_row
        )
        
        # 5. Handle Death
        if result.get("dead", False):
            self.forward_btn.disabled = True
            self.inventory_btn.disabled = True
            self.withdraw_btn.disabled = False # Ensure they can leave to reset
            
            embed.color = discord.Color.dark_grey()
            embed.set_footer(text="You have collapsed. The Guild will retrieve you.")
            
            # Overwrite the main message to show death state
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Optional: Send a followup ping
            await interaction.followup.send(
                f"{E.DEFEAT} **Defeated.**\nA rescue team is en route. You retain your items, but your Vestige is lost.", 
                ephemeral=True
            )
            return

        await interaction.edit_original_response(embed=embed, view=self)

    async def inventory_callback(self, interaction: discord.Interaction):
        """Swaps the view to Inventory."""
        # Local import to avoid circular dependency at module level
        from cogs.character_cog import InventoryView 
        
        await interaction.response.defer()
        items = await asyncio.to_thread(self.inv_manager.get_inventory, interaction.user.id)
        embed = await asyncio.to_thread(build_inventory_embed, items)

        view = InventoryView(
            self.db, self.interaction_user, 
            previous_view_callback=self.return_from_inventory, 
            previous_view_label="Return to Combat"
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def return_from_inventory(self, interaction: discord.Interaction):
        """Restores the Exploration view after closing inventory."""
        await interaction.response.defer()
        
        # Refresh data in case they drank a potion
        vitals = await asyncio.to_thread(self.db.get_player_vitals, interaction.user.id)
        session_row = await asyncio.to_thread(self.manager.get_active_session, interaction.user.id)
        
        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id, self.log, self.player_stats, vitals, session_row
        )
        # Re-attach self
        await interaction.edit_original_response(embed=embed, view=self)

    async def leave_callback(self, interaction: discord.Interaction):
        """Ends session and returns to Profile."""
        await interaction.response.defer()
        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)
        
        embed = discord.Embed(
            title="Returned to Astraeon", 
            description="You withdraw to the city and the Guild's relative safety. Prepare for the next contract.", 
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Return to main profile menu
        await back_to_profile_callback(interaction, is_new_message=False)