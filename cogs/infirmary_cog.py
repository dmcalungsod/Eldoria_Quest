"""
cogs/infirmary_cog.py

Healing services.
Hardened against concurrency and logic errors.
Atmosphere restored.
"""

import asyncio
import json
import logging
import math
import sqlite3

import discord
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

from .ui_helpers import back_to_guild_hall_callback, make_progress_bar

logger = logging.getLogger("eldoria.infirmary")


def infirmary_cost(missing_hp: int) -> int:
    return max(1, math.ceil(missing_hp * 0.5)) if missing_hp > 0 else 0


class InfirmaryView(View):
    def __init__(self, db: DatabaseManager, user: discord.User, p_data: sqlite3.Row, stats: PlayerStats):
        super().__init__(timeout=180)
        self.db = db
        self.user = user
        self.p_data = p_data
        self.stats = stats

        current_hp = p_data["current_hp"]
        current_mp = p_data["current_mp"]
        self.missing_hp = max(0, stats.max_hp - current_hp)
        self.missing_mp = max(0, stats.max_mp - current_mp)
        self.cost = infirmary_cost(self.missing_hp)

        # Heal Button
        disabled = self.missing_hp <= 0 and self.missing_mp <= 0
        label = f"Heal ({self.cost} G)" if not disabled else "Fully Restored"
        style = discord.ButtonStyle.primary if not disabled else discord.ButtonStyle.secondary

        # Disable if broke
        if p_data["aurum"] < self.cost:
            disabled = True
            label = "Insufficient Funds"

        self.heal_btn = Button(label=label, style=style, custom_id="heal_btn", emoji="❤️", row=0, disabled=disabled)
        self.heal_btn.callback = self.heal_callback
        self.add_item(self.heal_btn)

        # Back Button
        self.back_button = Button(label="Return to Hall", style=discord.ButtonStyle.grey, custom_id="back", row=1)
        self.back_button.callback = back_to_guild_hall_callback
        self.add_item(self.back_button)

    def set_back_button(self, cb, label="Back"):
        self.back_button.callback = cb
        self.back_button.label = label

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    def _execute_heal(self) -> tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                # Re-fetch to ensure atomic accuracy
                row = conn.execute(
                    "SELECT current_hp, current_mp, aurum FROM players WHERE discord_id=?", (self.user.id,)
                ).fetchone()

                # SECURITY: Fetch fresh stats to avoid stale state exploits
                # (e.g. equipping gear in another tab then healing for cheap)
                stats_row = conn.execute(
                    "SELECT stats_json FROM stats WHERE discord_id=?", (self.user.id,)
                ).fetchone()

                if stats_row and stats_row["stats_json"]:
                    fresh_stats = PlayerStats.from_dict(json.loads(stats_row["stats_json"]))
                    max_hp = fresh_stats.max_hp
                    max_mp = fresh_stats.max_mp
                else:
                    max_hp = self.stats.max_hp
                    max_mp = self.stats.max_mp

                # Re-calculate costs dynamically
                missing = max(0, max_hp - row["current_hp"])
                cost = infirmary_cost(missing)

                if missing == 0 and row["current_mp"] >= max_mp:
                    return False, "You are already healthy."

                if row["aurum"] < cost:
                    return False, "Insufficient funds."

                # Apply
                conn.execute(
                    "UPDATE players SET current_hp=?, current_mp=?, aurum=? WHERE discord_id=?",
                    (max_hp, max_mp, row["aurum"] - cost, self.user.id),
                )
                return True, f"Restored HP/MP for {cost} Aurum."
        except Exception as e:
            logger.error(f"Heal error: {e}")
            return False, "System error."

    async def heal_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, msg = await asyncio.to_thread(self._execute_heal)

        # Refresh Data
        tasks = [
            asyncio.to_thread(self.db.get_player, self.user.id),
            asyncio.to_thread(self.db.get_player_stats_json, self.user.id),
        ]
        new_p_data, stats_json = await asyncio.gather(*tasks)
        new_stats = PlayerStats.from_dict(stats_json)

        embed = self.build_infirmary_embed(new_p_data, new_stats, msg, success)
        view = InfirmaryView(self.db, self.user, new_p_data, new_stats)
        view.set_back_button(self.back_button.callback, self.back_button.label)

        await interaction.edit_original_response(embed=embed, view=view)

    @staticmethod
    def build_infirmary_embed(p_data, stats, msg=None, success=True) -> discord.Embed:
        hp_miss = max(0, stats.max_hp - p_data["current_hp"])
        cost = infirmary_cost(hp_miss)

        hp_bar = make_progress_bar(p_data["current_hp"], stats.max_hp)
        mp_bar = make_progress_bar(p_data["current_mp"], stats.max_mp)

        description = (
            "Soft green lanternlight fills the chamber as a Guild Healer works calmly among "
            "rows of treated bandages and tinctures. Their craft is precise — compassion measured, "
            "but genuine.\n\n"
            "**Condition**\n"
            f"> {E.HP} **HP:** `{hp_bar}` {p_data['current_hp']} / {stats.max_hp}\n"
            f"> {E.MP} **MP:** `{mp_bar}` {p_data['current_mp']} / {stats.max_mp}\n\n"
            "**Purse**\n"
            f"> {E.AURUM} **Aurum:** {p_data['aurum']}\n\n"
        )

        if hp_miss > 0:
            description += f"A full course of treatment will cost **{cost} {E.AURUM}** (0.5 Aurum per missing HP)."
        else:
            description += "You stand in peak condition; no treatment is required."

        embed = discord.Embed(
            title="🏥 Adventurer’s Guild — Infirmary", description=description, color=discord.Color.dark_grey()
        )

        if msg:
            field_name = "Treatment Complete" if success else "Treatment Declined"
            icon = E.CHECK if success else E.ERROR
            embed.add_field(name=field_name, value=f"{icon} {msg}", inline=False)
            embed.color = discord.Color.green() if success else discord.Color.red()

        return embed


class InfirmaryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()


async def setup(bot):
    await bot.add_cog(InfirmaryCog(bot))
