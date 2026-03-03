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
from game_systems.player.player_stats import PlayerStats, calculate_practice_threshold

from .utils.ui_helpers import back_to_profile_callback, make_progress_bar

logger = logging.getLogger("eldoria.status")

# Base costs remain the same, but scaling will be added
BASE_STAT_COSTS = {"STR": 10, "END": 10, "DEX": 10, "AGI": 12, "MAG": 12, "LCK": 20}


class StatusUpdateView(View):
    def __init__(self, db, user, p_data, stats, stats_row, multiplier=1):
        super().__init__(timeout=180)
        self.db = db
        self.user = user
        self.p_data = dict(p_data) if not isinstance(p_data, dict) else p_data
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
        Calculates cost for the NEXT point using an exponential curve.
        Formula: floor(Base * (Invested + 1) ^ 1.5)
        """
        base_cost = BASE_STAT_COSTS.get(stat, 10)
        start_val = self.starting_stats.get(stat, 1)

        # Invested points (current - start)
        diff = max(0, current_val - start_val)
        exponent = 1.5

        # Exponential Scaling
        # We use (diff + 1) because the first point (diff=0) should cost base * 1^1.5
        cost = math.floor(base_cost * ((diff + 1) ** exponent))

        return int(cost)

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
            label="Back to Profile",
            style=discord.ButtonStyle.secondary,
            custom_id="back_prof",
            row=2,
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
                emoji=getattr(E, stat, None),
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
            # Re-fetch stats to ensure atomic calculation validity
            vestige = self.db.get_player_field(self.user.id, "vestige_pool")
            stats_row = self.db.get_player_stats_row(self.user.id)

            if vestige is None or not stats_row:
                return False, "Data sync error.", 0

            # SECURITY FIX: Use Optimistic Locking
            raw_json_str = stats_row["stats_json"]
            current_stats = PlayerStats.from_dict(json.loads(raw_json_str))
            base_val = getattr(current_stats, "_stats")[stat].base

            # Recalculate cost for safety
            total_cost = self._calculate_bulk_cost(stat, base_val, amount)

            # Phase 1: Deduct Vestige Atomically
            if not self.db.deduct_vestige(self.user.id, total_cost):
                return False, "Insufficient Vestige.", 0

            # Apply Upgrade Locally
            old_max_hp = current_stats.max_hp
            old_max_mp = current_stats.max_mp

            current_stats.add_base_stat(stat, amount)

            new_max_hp = current_stats.max_hp
            new_max_mp = current_stats.max_mp

            hp_gain = new_max_hp - old_max_hp
            mp_gain = new_max_mp - old_max_mp

            # Phase 2: Update Stats with Optimistic Lock
            # If the JSON string in DB has changed since we read it, this returns False
            if not self.db.update_player_stats_optimistic(self.user.id, raw_json_str, current_stats.to_dict()):
                # Rollback: Refund the cost
                self.db.refund_vestige(self.user.id, total_cost)
                logger.warning(f"Optimistic lock failed for user {self.user.id} upgrading {stat}")
                return False, "System busy (Race Condition). Try again.", 0

            # Phase 3: Update Vitals (Only add the GAIN, do not full heal)
            # We fetch current vitals fresh to ensure accuracy
            current_vitals = self.db.get_player_vitals(self.user.id)
            if current_vitals:
                current_hp = current_vitals["current_hp"]
                current_mp = current_vitals["current_mp"]

                new_current_hp = min(new_max_hp, current_hp + hp_gain)
                new_current_mp = min(new_max_mp, current_mp + mp_gain)

                self.db.update_player_vitals(self.user.id, new_current_hp, new_current_mp)

            return True, "", vestige - total_cost
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

        new_view = StatusUpdateView(
            self.db,
            self.user,
            self.p_data,
            new_stats_obj,
            new_stats_row,
            self.multiplier,
        )

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
            f"{E.STR} `STR: {base['STR']:<4}` {E.END} `END: {base['END']:<4}` {E.DEX} `DEX: {base['DEX']:<4}`\n"
            f"{E.AGI} `AGI: {base['AGI']:<4}` {E.MAG} `MAG: {base['MAG']:<4}` {E.LCK} `LCK: {base['LCK']:<4}`"
        )
        embed.add_field(name="Base Attributes", value=formatted_stats, inline=False)

        # Practice bars visualization (restored)
        if s_row:
            str_t = calculate_practice_threshold(base["STR"])
            end_t = calculate_practice_threshold(base["END"])
            dex_t = calculate_practice_threshold(base["DEX"])
            agi_t = calculate_practice_threshold(base["AGI"])
            mag_t = calculate_practice_threshold(base["MAG"])
            lck_t = calculate_practice_threshold(base["LCK"])

            str_bar = make_progress_bar(s_row["str_exp"], str_t)
            end_bar = make_progress_bar(s_row["end_exp"], end_t)
            dex_bar = make_progress_bar(s_row["dex_exp"], dex_t)
            agi_bar = make_progress_bar(s_row["agi_exp"], agi_t)
            mag_bar = make_progress_bar(s_row["mag_exp"], mag_t)
            lck_bar = make_progress_bar(s_row["lck_exp"], lck_t)

            practice_bars = (
                f"`STR:` `{str_bar}` {math.floor(s_row['str_exp'])}/{str_t}\n"
                f"`END:` `{end_bar}` {math.floor(s_row['end_exp'])}/{end_t}\n"
                f"`DEX:` `{dex_bar}` {math.floor(s_row['dex_exp'])}/{dex_t}\n"
                f"`AGI:` `{agi_bar}` {math.floor(s_row['agi_exp'])}/{agi_t}\n"
                f"`MAG:` `{mag_bar}` {math.floor(s_row['mag_exp'])}/{mag_t}\n"
                f"`LCK:` `{lck_bar}` {math.floor(s_row['lck_exp'])}/{lck_t}"
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
