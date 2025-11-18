"""
cogs/developer_cog.py

Contains all secret developer commands for Eldoria Quest.
These commands are locked to the bot owner and are not visible
to any other user, including server administrators.
"""

import asyncio
import datetime
import sqlite3
from typing import Any, Dict, List  # <-- NEW IMPORT

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

# --- Developer Panel UI ---

class DevPanelView(View):
    """
    An ephemeral UI view containing developer-only actions
    to grant currency, items, or test game systems.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: sqlite3.Row,
        active_boosts: List[Dict[str, Any]] # <-- NEW PARAMETER
    ):
        super().__init__(timeout=180)  # 180-second timeout
        self.db = db_manager
        self.interaction_user = interaction_user
        # We store the data as a dict to safely update it
        self.player_data = dict(player_data)
        self.active_boosts = active_boosts # <-- NEW

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensures only the original command user can interact."""
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message(
                "This is not your developer panel.", ephemeral=True
            )
            return False
        return True

    # --- NEW HELPER: Formats time remaining ---
    @staticmethod
    def _format_time_remaining(end_time_iso: str) -> str:
        """Converts an ISO end time string to a human-readable remaining time."""
        try:
            end_time = datetime.datetime.fromisoformat(end_time_iso)
            now = datetime.datetime.now()
            remaining = end_time - now

            if remaining.total_seconds() <= 0:
                return "Expired"

            # Format as 59m 30s
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            return f"{minutes}m {seconds}s"
        except Exception:
            return "Invalid Time"

    @staticmethod
    def build_dev_embed(
        player_data: dict, active_boosts: List[Dict[str, Any]]
    ) -> discord.Embed:
        """Builds the embed showing the player's current currencies and active boosts."""
        embed = discord.Embed(
            title="Developer Control Panel",
            description="Grant test resources to your character.",
            color=discord.Color.orange(),
        )

        # --- NEW: Active Boosts Field ---
        if not active_boosts:
            boost_status = "No active boosts."
        else:
            boost_lines = []
            for boost in active_boosts:
                key = boost['boost_key'].replace('_', ' ').title()
                mult = f"+{(boost['multiplier'] - 1) * 100:.0f}%"
                time_left = DevPanelView._format_time_remaining(boost['end_time'])
                boost_lines.append(f"• **{key} ({mult})** - `{time_left}`")
            boost_status = "\n".join(boost_lines)

        embed.add_field(
            name="Global Boosts Status",
            value=boost_status,
            inline=False
        )
        # --- END NEW FIELD ---

        embed.add_field(
            name="Current Resources",
            value=(
                f"**EXP:** {player_data['experience']}\n"
                f"**{E.AURUM} Aurum:** {player_data['aurum']}\n"
                f"**{E.VESTIGE} Vestige:** {player_data['vestige_pool']}"
            ),
            inline=False,
        )
        embed.set_footer(text="This panel is visible only to you.")
        return embed

    async def _refresh_view(self, interaction: discord.Interaction):
        """Fetches new player data AND boosts, then edits the message."""

        # Get fresh data from the DB
        player_data_task = asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        boosts_task = asyncio.to_thread(self.db.get_active_boosts)

        refreshed_player_data, refreshed_boosts = await asyncio.gather(
            player_data_task, boosts_task
        )

        self.player_data = dict(refreshed_player_data)
        self.active_boosts = refreshed_boosts

        # Build new embed and view
        new_embed = self.build_dev_embed(self.player_data, self.active_boosts)
        new_view = DevPanelView(
            self.db, self.interaction_user, self.player_data, self.active_boosts
        )

        # Edit the original message
        await interaction.edit_original_response(embed=new_embed, view=new_view)

    def _grant_resources(
        self, discord_id: int, exp: int, aurum: int, vestige: int
    ) -> bool:
        """
        A single, safe database function to add resources.
        This runs in a thread.
        """
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE players
                    SET
                        experience = experience + ?,
                        aurum = aurum + ?,
                        vestige_pool = vestige_pool + ?
                    WHERE discord_id = ?
                    """,
                    (exp, aurum, vestige, discord_id),
                )
            return True
        except Exception as e:
            print(f"Error in _grant_resources: {e}")
            return False

    # --- HELPER FUNCTIONS for boosts (unchanged) ---
    def _set_global_boost(
        self, boost_key: str, multiplier: float, duration_hours: int
    ) -> bool:
        """Sets or updates a global boost in the DB."""
        end_time = (
            datetime.datetime.now() + datetime.timedelta(hours=duration_hours)
        ).isoformat()
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO global_boosts (boost_key, multiplier, end_time)
                    VALUES (?, ?, ?)
                    """,
                    (boost_key, multiplier, end_time),
                )
            return True
        except Exception as e:
            print(f"Error in _set_global_boost: {e}")
            return False

    def _clear_global_boosts(self) -> bool:
        """Clears all global boosts from the DB."""
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM global_boosts")
            return True
        except Exception as e:
            print(f"Error in _clear_global_boosts: {e}")
            return False

    # --- Button Callbacks ---

    @discord.ui.button(
        label="Give 10,000 EXP + Vestige",
        style=discord.ButtonStyle.success,
        emoji="✨",
        row=0
    )
    async def give_exp_callback(self, interaction: discord.Interaction, button: Button):
        """Grants 10k EXP and 10k Vestige."""
        await interaction.response.defer()

        await asyncio.to_thread(
            self._grant_resources, self.interaction_user.id, 10000, 0, 10000
        )

        # Refresh the UI to show new values
        await self._refresh_view(interaction)

    @discord.ui.button(
        label="Give 5,000 Aurum",
        style=discord.ButtonStyle.primary,
        emoji=E.AURUM,
        row=0
    )
    async def give_aurum_callback(self, interaction: discord.Interaction, button: Button):
        """Grants 5k Aurum."""
        await interaction.response.defer()

        await asyncio.to_thread(
            self._grant_resources, self.interaction_user.id, 0, 5000, 0
        )

        await self._refresh_view(interaction)

    @discord.ui.button(
        label="Reset Vitals",
        style=discord.ButtonStyle.danger,
        emoji="❤️",
        row=2 # <-- MOVED TO ROW 2
    )
    async def reset_vitals_callback(self, interaction: discord.Interaction, button: Button):
        """Resets HP and MP to their max values."""
        await interaction.response.defer()

        # This requires fetching stats to know what the max values are
        try:
            stats_json = await asyncio.to_thread(self.db.get_player_stats_json, self.interaction_user.id)
            stats = PlayerStats.from_dict(stats_json)

            await asyncio.to_thread(
                self.db.set_player_vitals, self.interaction_user.id, stats.max_hp, stats.max_mp
            )

            # --- MODIFIED: Call _refresh_view ---
            await self._refresh_view(interaction)
            # --- END MODIFIED ---

            await interaction.followup.send(
                f"HP and MP have been restored to {stats.max_hp}/{stats.max_mp}.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"Error resetting vitals: {e}", ephemeral=True)

    # --- NEW BUTTONS (Callbacks now refresh the view) ---
    @discord.ui.button(
        label="+100% EXP (1 Hr)",
        style=discord.ButtonStyle.success,
        emoji="🚀",
        row=1
    )
    async def give_exp_boost_callback(self, interaction: discord.Interaction, button: Button):
        """Sets EXP boost to 2.0x for 1 hour."""
        await interaction.response.defer()
        await asyncio.to_thread(self._set_global_boost, "exp_boost", 2.0, 1)

        # --- MODIFIED: Call _refresh_view ---
        await self._refresh_view(interaction)
        # --- END MODIFIED ---

    @discord.ui.button(
        label="+50% Loot (1 Hr)",
        style=discord.ButtonStyle.primary,
        emoji=E.LCK,
        row=1
    )
    async def give_loot_boost_callback(self, interaction: discord.Interaction, button: Button):
        """Sets Loot boost to 1.5x for 1 hour."""
        await interaction.response.defer()
        await asyncio.to_thread(self._set_global_boost, "loot_boost", 1.5, 1)

        # --- MODIFIED: Call _refresh_view ---
        await self._refresh_view(interaction)
        # --- END MODIFIED ---

    @discord.ui.button(
        label="Clear All Boosts",
        style=discord.ButtonStyle.danger,
        emoji=E.ERROR,
        row=2 # <-- MOVED TO ROW 2
    )
    async def clear_boosts_callback(self, interaction: discord.Interaction, button: Button):
        """Clears all active boosts."""
        await interaction.response.defer()
        await asyncio.to_thread(self._clear_global_boosts)

        # --- MODIFIED: Call _refresh_view ---
        await self._refresh_view(interaction)
        # --- END MODIFIED ---


# --- Developer Cog ---

class DeveloperCog(commands.Cog):
    """
    A cog that holds developer-only slash commands for testing and debugging.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(name="devpanel", description="Access the developer control panel.")
    @commands.is_owner()  # <-- THIS IS THE SECURITY CHECK
    async def dev_panel(self, interaction: discord.Interaction):
        """
        Displays an ephemeral control panel for the bot owner.
        """
        await interaction.response.defer(ephemeral=True)

        try:
            # --- MODIFIED: Fetch boosts as well ---
            player_data_task = asyncio.to_thread(self.db.get_player, interaction.user.id)
            boosts_task = asyncio.to_thread(self.db.get_active_boosts)

            player_data, active_boosts = await asyncio.gather(player_data_task, boosts_task)
            # --- END MODIFIED ---

            if not player_data:
                await interaction.followup.send(
                    f"{E.ERROR} You do not have a character. Use `/start` first.",
                    ephemeral=True
                )
                return

            # --- MODIFIED: Pass boosts to embed and view ---
            embed = DevPanelView.build_dev_embed(dict(player_data), active_boosts)
            view = DevPanelView(self.db, interaction.user, player_data, active_boosts)
            # --- END MODIFIED ---

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {e}", ephemeral=True
            )

    @dev_panel.error
    async def dev_panel_error(self, interaction: discord.Interaction, error):
        """Catches errors for the dev panel command."""
        if isinstance(error, commands.NotOwner):
            await interaction.response.send_message(
                "You are not authorized to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An unexpected error occurred: {error}", ephemeral=True
            )


# --- Setup Function ---

async def setup(bot: commands.Bot):
    """Adds the DeveloperCog to the bot."""
    await bot.add_cog(DeveloperCog(bot))
