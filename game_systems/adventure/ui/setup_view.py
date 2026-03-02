"""
game_systems/adventure/ui/setup_view.py

The preparation screen where players select their destination and duration.
Hardened: Async initialization and safe session creation.
"""

import asyncio
import logging

import discord
from discord.ui import Button, Select, View

import game_systems.data.emojis as E
from cogs.utils.ui_helpers import back_to_profile_callback, get_player_or_error
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.consumables import CONSUMABLES

from .adventure_embeds import AdventureEmbeds
from .status_view import AdventureStatusView

logger = logging.getLogger("eldoria.ui.setup")

RANK_ORDER = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"]


class AdventureSetupView(View):
    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        interaction_user: discord.User,
        player_rank: str,
        player_level: int,
        supplies: list = None,
        capacity: tuple = None,
    ):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user
        self.player_rank = player_rank
        self.player_level = player_level
        self.supplies_list = supplies or []
        self.capacity = capacity

        self.selected_location = None
        self.selected_duration = None
        self.selected_supplies = []

        # 1. Location Select
        self.location_select = Select(
            placeholder="Select Destination...",
            min_values=1,
            max_values=1,
            row=0,
        )
        # Populate Locations
        for loc_id, loc_data in LOCATIONS.items():
            is_unlocked = self._is_unlocked(loc_data)

            if is_unlocked:
                label = loc_data["name"]
                depth = loc_data.get("floor_depth", "?")
                danger = loc_data.get("danger_level", "?")
                desc = f"Lv.{loc_data['level_req']} (Rank {loc_data['min_rank']}) | Depth {depth} | Danger {danger}"
                emoji = loc_data.get("emoji", E.MAP)
            else:
                label = f"{E.LOCKED} {loc_data['name']}"
                desc = f"[LOCKED] Req: Lv.{loc_data['level_req']}, Rank {loc_data['min_rank']}"
                emoji = E.LOCKED

            self.location_select.add_option(
                label=label,
                value=loc_id,
                description=desc,
                emoji=emoji,
            )

        # Safety check: If no locations are available (e.g. all locked or error), prevent crash
        if not self.location_select.options:
            self.location_select.add_option(
                label="No Destinations Available",
                value="none",
                description="You do not meet requirements for any location.",
                emoji=E.LOCKED,
            )
            self.location_select.disabled = True

        self.location_select.callback = self.location_callback
        self.add_item(self.location_select)

        # 2. Duration Select
        self.duration_select = Select(
            placeholder="Select Duration...",
            min_values=1,
            max_values=1,
            row=1,
            options=[
                discord.SelectOption(
                    label="30 Minutes",
                    value="30",
                    description="Short patrol",
                    emoji="⏲️",
                ),
                discord.SelectOption(
                    label="1 Hour",
                    value="60",
                    description="Standard expedition",
                    emoji="⏲️",
                ),
                discord.SelectOption(
                    label="4 Hours",
                    value="240",
                    description="Extended journey",
                    emoji="⛺",
                ),
                discord.SelectOption(
                    label="8 Hours",
                    value="480",
                    description="Full day trek",
                    emoji="🌙",
                ),
            ],
        )
        self.duration_select.callback = self.duration_callback
        self.add_item(self.duration_select)

        # 3. Supply Select
        self.supply_select = Select(
            placeholder="Select Supplies (Optional)...",
            min_values=0,
            max_values=3,
            row=2,
        )

        # Consolidate supplies
        supply_options = {}
        for item in self.supplies_list:
            key = item["item_key"]
            if key not in supply_options:
                supply_options[key] = {"name": item["item_name"], "count": 0}
            supply_options[key]["count"] += item["count"]

        if supply_options:
            # Enforce 25-option limit for Discord Select menu
            sorted_keys = list(supply_options.keys())[:25]

            for key in sorted_keys:
                data = supply_options[key]
                count = data["count"]
                c_def = CONSUMABLES.get(key)
                c_type = c_def["type"] if c_def else "supply"

                # Logic: Passive supplies take 1. Consumables take bundles.
                if c_type == "supply":
                    value = f"{key}:1"
                    desc = f"Takes 1 {data['name']}."
                    label = f"{data['name']} (x{count})"
                else:
                    # Consumable: Offer bundle of 5 or max
                    bundle = min(5, count)
                    value = f"{key}:{bundle}"
                    desc = f"Takes {bundle} units."
                    label = f"{data['name']} (x{count})"

                self.supply_select.add_option(
                    label=label, value=value, description=desc, emoji="🎒"
                )

            # Dynamically adjust max_values based on available options
            # max_values cannot exceed the number of options
            num_options = len(self.supply_select.options)
            if num_options > 0:
                self.supply_select.max_values = min(3, num_options)
            else:
                self.supply_select.disabled = True
        else:
            self.supply_select.add_option(label="No Supplies", value="none")
            self.supply_select.disabled = True
            self.supply_select.max_values = 1

        self.supply_select.callback = self.supply_callback
        self.add_item(self.supply_select)

        # 4. Start Button
        self.start_btn = Button(
            label="Begin Expedition",
            style=discord.ButtonStyle.secondary,
            row=3,
            disabled=False,
            emoji="⚔️",
        )
        self.start_btn.callback = self.start_callback
        self.add_item(self.start_btn)

        # 5. Back Button
        self.back_btn = Button(
            label="Return to Ledger", style=discord.ButtonStyle.grey, row=3
        )
        self.back_btn.callback = self.back_callback
        self.add_item(self.back_btn)

    def _is_unlocked(self, loc_data: dict) -> bool:
        """Checks if the player meets rank and level requirements."""
        req_rank = loc_data["min_rank"]
        req_level = loc_data["level_req"]

        # Level Check
        if self.player_level < req_level:
            return False

        # Rank Check
        try:
            player_rank_idx = RANK_ORDER.index(self.player_rank)
            req_rank_idx = RANK_ORDER.index(req_rank)
            if player_rank_idx < req_rank_idx:
                return False
        except ValueError:
            # Fallback if rank is unknown (shouldn't happen)
            logger.warning(
                f"Unknown rank encountered: {self.player_rank} or {req_rank}"
            )
            return False

        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your adventure.", ephemeral=True
            )
            return False
        return True

    async def back_callback(self, interaction: discord.Interaction):
        await back_to_profile_callback(interaction, is_new_message=False)

    def _update_start_button(self):
        if self.selected_location and self.selected_duration:
            self.start_btn.style = discord.ButtonStyle.success
        else:
            self.start_btn.style = discord.ButtonStyle.secondary

    async def location_callback(self, interaction: discord.Interaction):
        loc_id = self.location_select.values[0]
        loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone"})

        if not self._is_unlocked(loc_data):
            await interaction.response.send_message(
                f"{E.LOCKED} **Access Denied**\nYou need **Level {loc_data['level_req']}** and **Rank {loc_data['min_rank']}** to enter {loc_data['name']}.",
                ephemeral=True,
            )
            return

        self.selected_location = loc_id
        self._update_start_button()

        await interaction.response.edit_message(view=self)

    async def duration_callback(self, interaction: discord.Interaction):
        self.selected_duration = int(self.duration_select.values[0])
        self._update_start_button()
        await interaction.response.edit_message(view=self)

    async def supply_callback(self, interaction: discord.Interaction):
        if self.supply_select.values and "none" not in self.supply_select.values:
            self.selected_supplies = self.supply_select.values
        else:
            self.selected_supplies = []
        await interaction.response.edit_message(view=self)

    async def start_callback(self, interaction: discord.Interaction):
        # Check requirements (Affordability/Empty State UX Feedback)
        if not self.selected_location or not self.selected_duration:
            missing = []
            if not self.selected_location:
                missing.append("destination")
            if not self.selected_duration:
                missing.append("duration")
            await interaction.response.send_message(
                f"⛔ You must select a **{' and '.join(missing)}** before starting the expedition.",
                ephemeral=True
            )
            return

        # Validate player before starting adventure
        if not await get_player_or_error(interaction, self.db):
            return

        await interaction.response.defer()

        supplies_dict = {}
        for val in self.selected_supplies:
            if val == "none":
                continue
            if ":" in val:
                k, v = val.split(":")
                supplies_dict[k] = int(v)
            else:
                # Legacy fallback
                supplies_dict[val] = 1

        try:
            # 1. Start the adventure in DB (Threaded)
            success = await asyncio.to_thread(
                self.manager.start_adventure,
                interaction.user.id,
                self.selected_location,
                self.selected_duration,
                supplies=supplies_dict,
            )

            if not success:
                await interaction.followup.send(
                    "Failed to start adventure. Please try again.", ephemeral=True
                )
                return

            # 2. Get new session data
            session = await asyncio.to_thread(
                self.manager.get_active_session, interaction.user.id
            )
            if not session:
                await interaction.followup.send(
                    "Error starting session.", ephemeral=True
                )
                return

            # 3. Build Status Embed
            embed = AdventureEmbeds.build_adventure_status_embed(session)

            # 4. Switch View
            view = AdventureStatusView(
                self.db, self.manager, self.interaction_user, session
            )
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Adventure start error: {e}", exc_info=True)
            await interaction.followup.send(
                "An error occurred starting the expedition.", ephemeral=True
            )
