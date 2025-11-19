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
        active_monster: dict = None,
    ):
        super().__init__(timeout=300) # 5 minutes
        self.db = db
        self.manager = manager
        self.location_id = location_id
        self.log = log or []
        self.interaction_user = interaction_user
        self.player_stats = player_stats
        self.inv_manager = InventoryManager(self.db)
        self.active_monster = active_monster

        # Button Setup
        self._setup_buttons()

    def _setup_buttons(self):
        # Dynamic Forward Button
        label, style, emoji = self._get_button_state()
        self.forward_btn = Button(label=label, style=style, emoji=emoji, row=0, custom_id="forward")
        self.forward_btn.callback = self.explore_callback
        self.add_item(self.forward_btn)

        # Inventory
        self.inv_btn = Button(label="Pack", style=discord.ButtonStyle.secondary, emoji=E.BACKPACK, row=0, custom_id="pack")
        self.inv_btn.callback = self.inventory_callback
        self.add_item(self.inv_btn)

        # Withdraw
        self.leave_btn = Button(label="Withdraw", style=discord.ButtonStyle.danger, emoji="⬅️", row=0, custom_id="leave")
        self.leave_btn.callback = self.leave_callback
        self.add_item(self.leave_btn)

    def _get_button_state(self):
        if self.active_monster:
            return "Battle", discord.ButtonStyle.danger, "⚔️"
        return "Forward", discord.ButtonStyle.success, "🥾"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Not your session.", ephemeral=True)
            return False
        return True

    # --------------------------------------------------------
    # MAIN GAME LOOP
    # --------------------------------------------------------
    async def explore_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # 1. Disable UI immediately
        self._disable_all()
        await interaction.edit_original_response(view=self)

        try:
            # 2. Run Simulation Thread
            result = await asyncio.to_thread(self.manager.simulate_adventure_step, self.interaction_user.id)
            sequence = result.get("sequence", [])
            is_dead = result.get("dead", False)

            # 3. Animation Loop
            for i, block in enumerate(sequence):
                # Update Log
                self.log.extend(block)
                self.log = self.log[-15:] # Keep log manageable

                # Refresh Data
                vitals, session, stats_json = await asyncio.gather(
                    asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id),
                    asyncio.to_thread(self.manager.get_active_session, self.interaction_user.id),
                    asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
                )
                
                self.player_stats = PlayerStats.from_dict(stats_json)
                
                # Check monster state from DB
                try:
                    self.active_monster = json.loads(session["active_monster_json"]) if session["active_monster_json"] else None
                except Exception:
                    self.active_monster = None

                # Prepare UI state
                embed = AdventureEmbeds.build_exploration_embed(
                    self.location_id, self.log, self.player_stats, vitals, session
                )

                is_last_frame = (i == len(sequence) - 1)

                if is_last_frame:
                    # Re-enable buttons
                    self._enable_all()
                    
                    # Update Forward Button Appearance
                    lbl, sty, emo = self._get_button_state()
                    self.forward_btn.label = lbl
                    self.forward_btn.style = sty
                    self.forward_btn.emoji = emo

                    if is_dead:
                        self.forward_btn.disabled = True
                        self.inv_btn.disabled = True
                        embed.color = discord.Color.dark_grey()
                        embed.set_footer(text="You have fallen.")

                # Edit Message
                await interaction.edit_original_response(embed=embed, view=self)

                # Wait if animating
                if not is_last_frame:
                    await asyncio.sleep(1.5)

        except Exception as e:
            logger.error(f"Exploration error: {e}", exc_info=True)
            self._enable_all()
            await interaction.edit_original_response(view=self)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _disable_all(self):
        for item in self.children:
            item.disabled = True
        
        # Show "Thinking/Combat" state
        self.forward_btn.label = "..."
        self.forward_btn.style = discord.ButtonStyle.secondary

    def _enable_all(self):
        for item in self.children:
            item.disabled = False

    # --------------------------------------------------------
    # Inventory Navigation
    # --------------------------------------------------------
    async def inventory_callback(self, interaction: discord.Interaction):
        # Avoid circular import
        from game_systems.character.ui.inventory_view import InventoryView
        await interaction.response.defer()

        items = await asyncio.to_thread(self.inv_manager.get_inventory, self.interaction_user.id)
        embed = build_inventory_embed(items)

        view = InventoryView(
            self.db, 
            self.interaction_user, 
            self.return_from_inventory, 
            "Return to Adventure"
        )
        await interaction.edit_original_response(embed=embed, view=view)

    async def return_from_inventory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Refresh state on return
        vitals = await asyncio.to_thread(self.db.get_player_vitals, self.interaction_user.id)
        session = await asyncio.to_thread(self.manager.get_active_session, self.interaction_user.id)

        embed = AdventureEmbeds.build_exploration_embed(
            self.location_id, self.log, self.player_stats, vitals, session
        )
        
        # Reset my buttons
        self._enable_all()
        
        await interaction.edit_original_response(embed=embed, view=self)

    # --------------------------------------------------------
    # Withdraw
    # --------------------------------------------------------
    async def leave_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await asyncio.to_thread(self.manager.end_adventure, self.interaction_user.id)
        await back_to_profile_callback(interaction, is_new_message=False)