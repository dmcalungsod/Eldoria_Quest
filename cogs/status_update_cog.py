"""
cogs/status_update_cog.py

Stat allocation system.
Rebalanced: Progressive Vestige costs to prevent early OP builds.
"""

import asyncio
import json
import logging
import math

import discord
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.class_data import CLASSES
from game_systems.player.player_stats import PlayerStats

from .ui_helpers import back_to_profile_callback, make_progress_bar

logger = logging.getLogger("eldoria.status")

# Base costs remain the same, but scaling will be added
BASE_STAT_COSTS = {"STR": 10, "END": 10, "DEX": 10, "AGI": 12, "MAG": 12, "LCK": 20}
STAT_EXP_THRESHOLD = 100


class StatusUpdateView(View):
    def __init__(self, db, user, p_data, stats, stats_row, multiplier=1):
        super().__init__(timeout=180)
        self.db = db
        self.user = user
        self.p_data = dict(p_data)
        self.stats = stats
        self.stats_row = stats_row
        self.vestige = self.p_data["vestige_pool"]
        self.multiplier = multiplier

        # Get starting stats for scaling calculation
        self.starting_stats = self._get_class_starting_stats(p_data["class_id"])

        self._setup_ui()

    def _get_class_starting_stats(self, class_id):
        """Retrieves base stats for the player's class to calculate cost scaling."""
        for data in CLASSES.values():
            if data["id"] == class_id:
                return data["stats"]
        return {"STR": 1, "END": 1, "DEX": 1, "AGI": 1, "MAG": 1, "LCK": 1}

    def _calculate_single_point_cost(self, stat: str, current_val: int) -> int:
        """
        Calculates cost for the NEXT point.
        Formula: Base + floor((Current - Starting) / 5)
        """
        base_cost = BASE_STAT_COSTS.get(stat, 10)
        start_val = self.starting_stats.get(stat, 1)

        # Ensure we don't get negative scaling if current < start (rare/bug fix)
        diff = max(0, current_val - start_val)

        # Progressive Scaling: Cost increases by 1 for every 5 points gained
        scaling = math.floor(diff / 5)

        return base_cost + scaling

    def _calculate_bulk_cost(self, stat: str, current_val: int, amount: int) -> int:
        """Calculates total cost for adding 'amount' points."""
        total_cost = 0
        temp_val = current_val
        for _ in range(amount):
            total_cost += self._calculate_single_point_cost(stat, temp_val)
            temp_val += 1
        return total_cost

    def _setup_ui(self):
        self._add_stat_buttons()

        # Multiplier Toggle
        self.mult_btn = Button(
            label=f"Mode: x{self.multiplier}",
            style=discord.ButtonStyle.primary,
            custom_id="toggle_mult",
            row=2,
            emoji="⚡",
        )
        self.mult_btn.callback = self.toggle_multiplier_callback
        self.add_item(self.mult_btn)

        # Back Button
        self.back_button = Button(
            label="Back to Profile", style=discord.ButtonStyle.secondary, custom_id="back_prof", row=2
        )
        self.back_button.callback = back_to_profile_callback
        self.add_item(self.back_button)

    def _add_stat_buttons(self):
        # Get raw base values from PlayerStats object
        # We need the BASE value (points allocated), not total (with gear)
        base_values = self.stats.get_base_stats_dict()

        stats_list = ["STR", "END", "DEX", "AGI", "MAG", "LCK"]
        for i, stat in enumerate(stats_list):
            row = 0 if i < 3 else 1

            current_val = base_values.get(stat, 1)
            total_cost = self._calculate_bulk_cost(stat, current_val, self.multiplier)

            can_afford = self.vestige >= total_cost

            btn = Button(
                label=f"+{self.multiplier} {stat} ({total_cost}V)",
                custom_id=f"stat_{stat}",
                row=row,
                disabled=not can_afford,
                style=discord.ButtonStyle.secondary,
            )
            btn.callback = self.stat_callback
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    def _execute_upgrade(self, stat: str, amount: int) -> tuple[bool, str, int]:
        try:
            with self.db.get_connection() as conn:
                # Re-fetch stats to ensure atomic calculation validity
                row = conn.execute("SELECT vestige_pool FROM players WHERE discord_id=?", (self.user.id,)).fetchone()
                stats_row = conn.execute("SELECT stats_json FROM stats WHERE discord_id=?", (self.user.id,)).fetchone()

                if not row or not stats_row:
                    return False, "Data sync error.", 0

                # Re-create stats object to get current base
                current_stats = PlayerStats.from_dict(json.loads(stats_row["stats_json"]))
                base_val = getattr(current_stats, "_stats")[stat].base

                # Recalculate cost inside transaction for safety
                total_cost = self._calculate_bulk_cost(stat, base_val, amount)

                if row["vestige_pool"] < total_cost:
                    return False, "Insufficient Vestige.", 0

                # Apply Upgrade
                current_stats.add_base_stat(stat, amount)
                new_vestige = row["vestige_pool"] - total_cost

                conn.execute(
                    "UPDATE players SET vestige_pool=?, current_hp=?, current_mp=? WHERE discord_id=?",
                    (new_vestige, current_stats.max_hp, current_stats.max_mp, self.user.id),
                )
                conn.execute(
                    "UPDATE stats SET stats_json=? WHERE discord_id=?",
                    (json.dumps(current_stats.to_dict()), self.user.id),
                )
                return True, "", new_vestige
        except Exception as e:
            logger.error(f"Stat upgrade error: {e}")
            return False, "System Error.", 0

    async def toggle_multiplier_callback(self, interaction: discord.Interaction):
        if self.multiplier == 1:
            self.multiplier = 5
        elif self.multiplier == 5:
            self.multiplier = 10
        else:
            self.multiplier = 1

        self.clear_items()
        self._setup_ui()
        await interaction.response.edit_message(view=self)

    async def stat_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stat = interaction.data["custom_id"].split("_")[1]

        success, msg, new_vestige = await asyncio.to_thread(self._execute_upgrade, stat, self.multiplier)

        if not success:
            await interaction.followup.send(f"{E.ERROR} {msg}", ephemeral=True)
            return

        # Refresh UI
        self.p_data["vestige_pool"] = new_vestige
        # We need fresh stats to show the new values
        new_stats_row = await asyncio.to_thread(self.db.get_player_stats_row, self.user.id)
        new_stats_obj = PlayerStats.from_dict(json.loads(new_stats_row["stats_json"]))

        embed = self.build_status_embed(self.p_data, new_stats_obj, new_stats_row)

        new_view = StatusUpdateView(self.db, self.user, self.p_data, new_stats_obj, new_stats_row, self.multiplier)

        await interaction.edit_original_response(embed=embed, view=new_view)

    @staticmethod
    def build_status_embed(p_data, stats, s_row):
        embed = discord.Embed(
            title="🜁 Attribute Awakening",
            description=f"Enhance your attributes.\n**Vestige:** {p_data['vestige_pool']} {E.VESTIGE}",
            color=discord.Color.purple(),
        )

        base = stats.get_base_stats_dict()
        formatted_stats = (
            f"`STR: {base['STR']:<4}` `END: {base['END']:<4}` `DEX: {base['DEX']:<4}`\n"
            f"`AGI: {base['AGI']:<4}` `MAG: {base['MAG']:<4}` `LCK: {base['LCK']:<4}`"
        )
        embed.add_field(name="Base Attributes", value=formatted_stats, inline=False)

        # Practice bars visualization (restored)
        if s_row:
            def fmt(val):
                return f"[`{make_progress_bar(val, STAT_EXP_THRESHOLD)}`] {math.floor(val)}/{STAT_EXP_THRESHOLD}"

            practice_bars = (
                f"`STR:` {fmt(s_row['str_exp'])}\n"
                f"`END:` {fmt(s_row['end_exp'])}\n"
                f"`DEX:` {fmt(s_row['dex_exp'])}\n"
                f"`AGI:` {fmt(s_row['agi_exp'])}\n"
                f"`MAG:` {fmt(s_row['mag_exp'])}\n"
                f"`LCK:` {fmt(s_row['lck_exp'])}"
            )
            embed.add_field(name="Practice Progress", value=practice_bars, inline=False)

        embed.set_footer(text="Costs increase as attributes grow higher.")
        return embed


class StatusUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot):
    await bot.add_cog(StatusUpdateCog(bot))
