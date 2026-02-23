"""
cogs/developer_cog.py

Admin/Developer tools.
SECURITY: Strict owner checks and audit logging.
"""

import asyncio
import datetime
import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.world_time import WorldTime
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.admin")


class DevPanelView(View):
    def __init__(
        self,
        db_manager: DatabaseManager,
        interaction_user: discord.User,
        player_data: dict[str, Any],
        active_boosts: list[dict[str, Any]],
    ):
        super().__init__(timeout=180)
        self.db = db_manager
        self.interaction_user = interaction_user
        self.player_data = player_data
        self.active_boosts = active_boosts

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.interaction_user.id:
            await interaction.response.send_message("Access Denied.", ephemeral=True)
            return False
        return True

    @staticmethod
    def _format_time_remaining(end_time_iso: str) -> str:
        try:
            end_time = datetime.datetime.fromisoformat(end_time_iso)
            remaining = end_time - WorldTime.now()
            if remaining.total_seconds() <= 0:
                return "Expired"
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            return f"{mins}m {secs}s"
        except Exception:
            return "Invalid Time"

    @staticmethod
    def build_dev_embed(player_data: dict, active_boosts: list) -> discord.Embed:
        embed = discord.Embed(
            title="🛠️ Developer Control Panel",
            description="Admin controls for game state and economy.",
            color=discord.Color.orange(),
        )

        # Boost Status
        if not active_boosts:
            boost_txt = "No active global boosts."
        else:
            lines = []
            for b in active_boosts:
                name = b["boost_key"].replace("_", " ").title()
                val = f"+{(b['multiplier'] - 1) * 100:.0f}%"
                time = DevPanelView._format_time_remaining(b["end_time"])
                lines.append(f"• **{name} ({val})** - `{time}`")
            boost_txt = "\n".join(lines)

        embed.add_field(name="Global Boosts", value=boost_txt, inline=False)
        embed.add_field(
            name="Your Resources",
            value=(
                f"**EXP:** {player_data.get('experience', 0)}\n"
                f"**Aurum:** {player_data.get('aurum', 0)}\n"
                f"**Vestige:** {player_data.get('vestige_pool', 0)}"
            ),
            inline=False,
        )
        return embed

    async def _refresh_view(self, interaction: discord.Interaction):
        # Fetch fresh data
        p_data = await asyncio.to_thread(self.db.get_player, self.interaction_user.id)
        boosts = await asyncio.to_thread(self.db.get_active_boosts)

        self.player_data = dict(p_data) if p_data else {}
        self.active_boosts = boosts

        embed = self.build_dev_embed(self.player_data, self.active_boosts)
        await interaction.edit_original_response(embed=embed, view=self)

    # --- Actions ---
    def _grant(self, exp=0, aurum=0, vestige=0):
        try:
            self.db.admin_grant(
                self.interaction_user.id, exp=exp, aurum=aurum, vestige=vestige
            )
            logger.warning(
                f"ADMIN GRANT: {self.interaction_user.name} gave self {exp}XP, {aurum}G, {vestige}V"
            )
        except Exception as e:
            logger.error(f"Grant failed: {e}")

    def _set_boost(self, key, multiplier, duration):
        try:
            self.db.set_global_boost(key, multiplier, duration)
        except Exception as e:
            logger.error(f"Set boost failed: {e}")

    def _clear_boosts(self):
        try:
            self.db.clear_global_boosts()
        except Exception as e:
            logger.error(f"Clear boosts failed: {e}")

    # --- Buttons Row 0: Grants ---
    @discord.ui.button(
        label="Give 10k XP/Vestige",
        style=discord.ButtonStyle.success,
        emoji="✨",
        row=0,
    )
    async def exp_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await asyncio.to_thread(self._grant, exp=10000, vestige=10000)
        await self._refresh_view(interaction)

    @discord.ui.button(
        label="Give 5k Aurum", style=discord.ButtonStyle.primary, emoji=E.AURUM, row=0
    )
    async def aurum_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await asyncio.to_thread(self._grant, aurum=5000)
        await self._refresh_view(interaction)

    # --- Buttons Row 1: Boosts ---
    @discord.ui.button(
        label="+100% EXP (1h)", style=discord.ButtonStyle.success, emoji="🚀", row=1
    )
    async def boost_exp_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await asyncio.to_thread(self._set_boost, "exp_boost", 2.0, 1)
        await self._refresh_view(interaction)

    @discord.ui.button(
        label="+50% Loot (1h)", style=discord.ButtonStyle.primary, emoji="📦", row=1
    )
    async def boost_loot_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await asyncio.to_thread(self._set_boost, "loot_boost", 1.5, 1)
        await self._refresh_view(interaction)

    # --- Buttons Row 2: Utility ---
    @discord.ui.button(
        label="Full Heal", style=discord.ButtonStyle.danger, emoji="❤️", row=2
    )
    async def heal_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        try:
            stats_json = await asyncio.to_thread(
                self.db.get_player_stats_json, self.interaction_user.id
            )
            stats = PlayerStats.from_dict(stats_json)
            await asyncio.to_thread(
                self.db.set_player_vitals,
                self.interaction_user.id,
                stats.max_hp,
                stats.max_mp,
            )
            await self._refresh_view(interaction)
        except Exception as e:
            logger.error(f"Admin heal error: {e}")

    @discord.ui.button(
        label="Clear Boosts", style=discord.ButtonStyle.secondary, emoji="🚫", row=2
    )
    async def clear_boost_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await asyncio.to_thread(self._clear_boosts)
        await self._refresh_view(interaction)


class DeveloperCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager()

    @app_commands.command(
        name="devpanel", description="[Owner Only] Developer Controls"
    )
    async def dev_panel(self, interaction: discord.Interaction):
        # SECURITY: Manual check to ensure only the owner can access this panel.
        # This is more robust than relying solely on decorators for app_commands.
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "⛔ You are not the bot owner.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        p_data = await asyncio.to_thread(self.db.get_player, interaction.user.id)
        if not p_data:
            await interaction.followup.send("No character found.", ephemeral=True)
            return

        boosts = await asyncio.to_thread(self.db.get_active_boosts)

        view = DevPanelView(self.db, interaction.user, dict(p_data), boosts)
        embed = view.build_dev_embed(dict(p_data), boosts)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @dev_panel.error
    async def dev_error(self, interaction: discord.Interaction, error):
        logger.error(f"Dev panel error: {error}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ An error occurred while loading the developer panel.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(DeveloperCog(bot))
