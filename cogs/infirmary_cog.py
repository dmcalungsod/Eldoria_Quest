"""
cogs/infirmary_cog.py

Healing services.
Hardened against concurrency and logic errors.
Atmosphere restored.
"""

import asyncio
import logging
import math

import discord
from discord.ext import commands
from discord.ui import Button, View

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats

from .ui_helpers import back_to_guild_hall_callback, make_progress_bar

logger = logging.getLogger("eldoria.infirmary")


def infirmary_cost(missing_hp: int, missing_mp: int) -> int:
    if missing_hp <= 0 and missing_mp <= 0:
        return 0
    return max(1, math.ceil(missing_hp * 2.0 + missing_mp * 3.0))


class InfirmaryView(View):
    def __init__(self, db: DatabaseManager, user: discord.User, p_data, stats: PlayerStats):
        super().__init__(timeout=180)
        self.db = db
        self.user = user
        self.p_data = dict(p_data) if not isinstance(p_data, dict) else p_data
        self.stats = stats

        current_hp = self.p_data["current_hp"]
        current_mp = self.p_data["current_mp"]
        self.missing_hp = max(0, stats.max_hp - current_hp)
        self.missing_mp = max(0, stats.max_mp - current_mp)
        self.cost = infirmary_cost(self.missing_hp, self.missing_mp)

        # Heal Button
        disabled = self.missing_hp <= 0 and self.missing_mp <= 0
        label = f"Heal ({self.cost} G)" if not disabled else "Fully Restored"
        style = discord.ButtonStyle.primary if not disabled else discord.ButtonStyle.secondary

        # Disable if broke
        if self.p_data["aurum"] < self.cost:
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
            # SECURITY: Fetch fresh stats to avoid stale state exploits
            stats_json = self.db.get_player_stats_json(self.user.id)
            if not stats_json:
                logger.error(f"Heal failed: Could not fetch stats for {self.user.id}")
                return False, "System error: Could not fetch player stats."

            fresh_stats = PlayerStats.from_dict(stats_json)
            max_hp = fresh_stats.max_hp
            max_mp = fresh_stats.max_mp

            # Delegate to DatabaseManager for atomic execution
            return self.db.execute_heal(self.user.id, max_hp, max_mp, cost=0)
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
        p = dict(p_data) if not isinstance(p_data, dict) else p_data
        hp_miss = max(0, stats.max_hp - p["current_hp"])
        mp_miss = max(0, stats.max_mp - p["current_mp"])
        cost = infirmary_cost(hp_miss, mp_miss)

        hp_bar = make_progress_bar(p["current_hp"], stats.max_hp)
        mp_bar = make_progress_bar(p["current_mp"], stats.max_mp)

        # Dynamic Description based on Health
        hp_percent = p["current_hp"] / max(stats.max_hp, 1)
        if hp_percent < 0.3:
            flavor = (
                "The healers rush to your side, their faces grave. Blood soaks your gear, and your "
                "breath comes in ragged gasps. 'Stabilize them, now!' someone shouts."
            )
        elif hp_percent < 0.7:
            flavor = (
                "You limp to a cot, wincing as a Healer inspects your wounds. 'Deep cuts,' they mutter, "
                "reaching for a jar of stinging salve. 'This will not be pleasant.'"
            )
        else:
            flavor = (
                "Soft green lanternlight fills the chamber as a Guild Healer works calmly among "
                "rows of treated bandages and tinctures. Their craft is precise — compassion measured, "
                "but genuine."
            )

        description = (
            f"{flavor}\n\n"
            "**Condition**\n"
            f"> {E.HP} **HP:** `{hp_bar}` {p['current_hp']} / {stats.max_hp}\n"
            f"> {E.MP} **MP:** `{mp_bar}` {p['current_mp']} / {stats.max_mp}\n\n"
            "**Purse**\n"
            f"> {E.AURUM} **Aurum:** {p['aurum']}\n\n"
        )

        if hp_miss > 0 or mp_miss > 0:
            description += (
                f"A full course of treatment will cost **{cost} {E.AURUM}**.\n"
                "*Rates: 2.0 Aurum per HP, 3.0 Aurum per MP (Magic is taxing).*"
            )
        else:
            description += "You stand in peak condition; no treatment is required."

        embed = discord.Embed(
            title="🏥 Adventurer's Guild — Infirmary", description=description, color=discord.Color.dark_grey()
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
