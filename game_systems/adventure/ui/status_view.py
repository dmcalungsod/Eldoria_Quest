"""
game_systems/adventure/ui/status_view.py

View for monitoring active background adventures.
Allows refreshing status or retreating early.
"""

import datetime
import logging

import discord
from discord.ui import Button, View, Select

import game_systems.data.emojis as E
from cogs.ui_helpers import back_to_profile_callback
from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.adventure.ui.adventure_embeds import AdventureEmbeds
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.world_time import WorldTime

logger = logging.getLogger("eldoria.ui.status")


class TacticsView(View):
    def __init__(self, manager: AdventureManager, discord_id: int):
        super().__init__(timeout=60)
        self.manager = manager
        self.discord_id = discord_id

        self.select = Select(
            placeholder="Choose your Combat Stance...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Aggressive",
                    value="aggressive",
                    description="High Damage, High Risk (+20% Dmg Dealt/Taken)",
                    emoji="⚔️"
                ),
                discord.SelectOption(
                    label="Balanced",
                    value="balanced",
                    description="Standard Combat (No modifiers)",
                    emoji="⚖️",
                    default=True
                ),
                discord.SelectOption(
                    label="Defensive",
                    value="defensive",
                    description="Safety First (-20% Dmg Dealt/Taken)",
                    emoji="🛡️"
                ),
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        stance = self.select.values[0]

        try:
            # Simulate step with stance change action
            # Note: This is synchronous, matching local pattern
            result = self.manager.simulate_adventure_step(self.discord_id, action=f"set_stance:{stance}")

            # Check result for confirmation
            if result and result.get("sequence"):
                # sequence is [[msg]]
                # Flatten log to find relevant message
                msgs = [m for sublist in result["sequence"] for m in sublist]
                last_msg = msgs[-1] if msgs else "Stance updated."

                # Check if it was actually a stance update or an error/generic msg
                if "shift into" in last_msg or "stance" in last_msg:
                    await interaction.followup.send(f"✅ {last_msg}", ephemeral=True)
                else:
                    await interaction.followup.send("Stance update processed, but combat state may have changed.", ephemeral=True)
            else:
                await interaction.followup.send("Failed to update stance. Are you in active combat?", ephemeral=True)
        except Exception as e:
            logger.error(f"Tactics error: {e}")
            await interaction.followup.send("An error occurred while changing tactics.", ephemeral=True)


class AdventureStatusView(View):
    def __init__(
        self,
        db: DatabaseManager,
        manager: AdventureManager,
        interaction_user: discord.User,
        session_id: str = None # Optional, mainly for verification if needed
    ):
        super().__init__(timeout=180)
        self.db = db
        self.manager = manager
        self.interaction_user = interaction_user

        # Refresh Button
        self.btn_refresh = Button(
            label="Refresh Status",
            style=discord.ButtonStyle.primary,
            custom_id="adv_refresh",
            emoji="🔄",
            row=0
        )
        self.btn_refresh.callback = self.refresh_callback
        self.add_item(self.btn_refresh)

        # Tactics Button
        self.btn_tactics = Button(
            label="Tactics",
            style=discord.ButtonStyle.secondary,
            custom_id="adv_tactics",
            emoji="⚔️",
            row=0
        )
        self.btn_tactics.callback = self.tactics_callback
        self.add_item(self.btn_tactics)

        # Retreat Button
        self.btn_retreat = Button(
            label="Retreat (End Early)",
            style=discord.ButtonStyle.danger,
            custom_id="adv_retreat",
            emoji="🏳️",
            row=0
        )
        self.btn_retreat.callback = self.retreat_callback
        self.add_item(self.btn_retreat)

        # Back Button
        self.btn_back = Button(
            label="Return to Profile",
            style=discord.ButtonStyle.grey,
            custom_id="adv_back",
            row=1
        )
        self.btn_back.callback = back_to_profile_callback
        self.add_item(self.btn_back)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("This is not your expedition.", ephemeral=True)
            return False
        return True

    async def refresh_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fetch latest session data
        session = await asyncio.to_thread(self.manager.get_active_session, self.user.id)

        if not session:
            await interaction.followup.send(
                "Adventure session not found or already ended.", ephemeral=True
            )
            # Disable buttons since session is gone
            for item in self.children:
                if item != self.back_btn:
                    item.disabled = True
            await interaction.edit_original_response(view=self)
            return

        self.session_data = session

        try:
            embed = AdventureEmbeds.build_adventure_status_embed(session)
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Failed to refresh status embed: {e}", exc_info=True)
            await interaction.followup.send("Error refreshing status.", ephemeral=True)

    async def retreat_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # End adventure
        summary = await asyncio.to_thread(self.manager.end_adventure, self.user.id)

        if not summary:
            await interaction.followup.send("Failed to retrieve adventure results.", ephemeral=True)
            return

        # Build summary embed
        loc_id = self.session_data.get("location_id")
        embed = AdventureEmbeds.build_summary_embed(summary, loc_id)

        # Update message, remove view (replace with simple back button)
        self.clear_items()

        back_btn = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
        back_btn.callback = back_to_profile_callback
        self.add_item(back_btn)

        await interaction.edit_original_response(embed=embed, view=self)
        session = self.db.get_active_adventure(self.interaction_user.id)
        if not session or session.get("status") != "in_progress":
            await interaction.followup.send("Expedition has ended or is no longer active.", ephemeral=True)
            # Disable buttons?
            return

        # Calculate time remaining
        try:
            end_time = datetime.datetime.fromisoformat(session["end_time"])
            now = WorldTime.now()
            remaining = end_time - now

            if remaining.total_seconds() <= 0:
                time_str = "Complete!"
            else:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}h {minutes}m"
        except Exception:
            time_str = "Unknown"

        loc_data = LOCATIONS.get(session["location_id"], {})
        steps = session.get("steps_completed", 0)

        embed = AdventureEmbeds.build_status_embed(session, loc_data, time_str, steps)
        await interaction.edit_original_response(embed=embed, view=self)

    async def tactics_callback(self, interaction: discord.Interaction):
        # Ephemeral view to choose stance
        view = TacticsView(self.manager, interaction.user.id)
        await interaction.response.send_message("Select your combat stance:", view=view, ephemeral=True)

    async def retreat_callback(self, interaction: discord.Interaction):
        # Confirm retreat? For now, direct action as per ONE UI (fast interaction)
        await interaction.response.defer()

        session = self.db.get_active_adventure(self.interaction_user.id)
        if not session:
            await interaction.followup.send("No active expedition found.", ephemeral=True)
            return

        # Attempt to end adventure
        summary = self.manager.end_adventure(self.interaction_user.id)

        if summary:
            embed = AdventureEmbeds.build_summary_embed(summary, session["location_id"])
            # Remove view or provide back button
            # We can reuse self, but remove retreat/refresh
            self.clear_items()

            btn_back = Button(label="Return to Profile", style=discord.ButtonStyle.grey)
            btn_back.callback = back_to_profile_callback
            self.add_item(btn_back)

            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.followup.send("Failed to retreat. Try again.", ephemeral=True)
