"""
game_systems/adventure/ui/setup_view.py

The preparation screen where players select their destination.
Hardened: Async initialization and safe session creation.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats

from .adventure_embeds import AdventureEmbeds
from .exploration_view import ExplorationView

logger = logging.getLogger("eldoria.ui.setup")


class AdventureSetupView(View):
    def __init__(
        self, db: DatabaseManager, manager: AdventureManager, interaction_user: discord.User, player_rank: str
    ):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user
        self.player_rank = player_rank

        self.location_select = Select(
            placeholder="Select Destination...",
            min_values=1,
            max_values=1,
            row=0,
        )

        # Populate Locations
        for loc_id, loc_data in LOCATIONS.items():
            # (Optional: Add Rank Check logic here if desired)
            # e.g. if loc_data['min_rank'] > self.player_rank: continue
            self.location_select.add_option(
                label=loc_data["name"],
                value=loc_id,
                description=f"Lv.{loc_data['level_req']} (Rank {loc_data['min_rank']})",
                emoji=loc_data.get("emoji", E.MAP),
            )

        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

        # Back Button
        self.back_btn = Button(label="Return to Ledger", style=discord.ButtonStyle.grey, row=1)
        self.back_btn.callback = self.back_callback
        self.add_item(self.back_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your adventure.", ephemeral=True)
            return False
        return True

    async def back_callback(self, interaction: discord.Interaction):
        await back_to_profile_callback(interaction, is_new_message=False)

    async def location_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            loc_id = self.location_select.values[0]
            loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone"})

            # 1. Start the adventure in DB (Threaded)
            success = await asyncio.to_thread(self.manager.start_adventure, interaction.user.id, loc_id, -1)
            
            if not success:
                await interaction.followup.send("Failed to start adventure. Please try again.", ephemeral=True)
                return

            # 2. Fetch data for the next view (Parallel)
            vitals, session_row, stats_json = await asyncio.gather(
                asyncio.to_thread(self.db.get_player_vitals, interaction.user.id),
                asyncio.to_thread(self.manager.get_active_session, interaction.user.id),
                asyncio.to_thread(self.db.get_player_stats_json, interaction.user.id)
            )
            
            player_stats = PlayerStats.from_dict(stats_json)

            # 3. Initial Log
            initial_log = [
                f"You step beyond the walls into **{loc_data['name']}**.",
                "The air shifts. You are now in the wilds.",
            ]

            # 4. Build Embed
            embed = AdventureEmbeds.build_exploration_embed(loc_id, initial_log, player_stats, vitals, session_row)

            # 5. Transition to Exploration View
            view = ExplorationView(
                self.db, self.manager, loc_id, initial_log, self.interaction_user, player_stats, active_monster=None
            )
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Location setup error: {e}", exc_info=True)
            await interaction.followup.send("An error occurred starting the expedition.", ephemeral=True)