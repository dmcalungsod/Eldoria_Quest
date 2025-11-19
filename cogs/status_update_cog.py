"""
cogs/status_update_cog.py

Stat allocation system.
Hardened against transaction anomalies.
"""

import asyncio
import logging
import json
import sqlite3
import discord
from typing import Tuple
from discord.ext import commands
from discord.ui import Button, View
import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from .ui_helpers import back_to_profile_callback

logger = logging.getLogger("eldoria.status")

STAT_COSTS = {"STR": 10, "END": 10, "DEX": 10, "AGI": 12, "MAG": 12, "LCK": 20}
STAT_EXP_THRESHOLD = 100

class StatusUpdateView(View):
    def __init__(self, db, user, p_data, stats, stats_row):
        super().__init__(timeout=180)
        self.db = db
        self.user = user
        self.p_data = dict(p_data)
        self.stats = stats
        self.stats_row = stats_row
        self.vestige = self.p_data["vestige_pool"]
        
        self._add_buttons()
        
        self.back_btn = Button(label="Back to Profile", style=discord.ButtonStyle.secondary, row=2)
        self.back_btn.callback = back_to_profile_callback
        self.add_item(self.back_btn)

    def _add_buttons(self):
        for i, stat in enumerate(["STR", "END", "DEX", "AGI", "MAG", "LCK"]):
            row = 0 if i < 3 else 1
            cost = STAT_COSTS[stat]
            btn = Button(
                label=f"+1 {stat} ({cost}V)", 
                custom_id=f"stat_{stat}", 
                row=row,
                disabled=(self.vestige < cost),
                style=discord.ButtonStyle.primary
            )
            btn.callback = self.stat_callback
            self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    def _execute_upgrade(self, stat: str) -> Tuple[bool, str, int]:
        cost = STAT_COSTS.get(stat, 999999)
        try:
            with self.db.get_connection() as conn:
                # Lock & Verify
                row = conn.execute("SELECT vestige_pool FROM players WHERE discord_id=?", (self.user.id,)).fetchone()
                if not row or row["vestige_pool"] < cost:
                    return False, "Insufficient Vestige.", 0
                
                # Update Memory Stats
                self.stats.add_base_stat(stat, 1)
                new_vestige = row["vestige_pool"] - cost
                
                # Atomic Update
                conn.execute(
                    "UPDATE players SET vestige_pool=?, current_hp=?, current_mp=? WHERE discord_id=?",
                    (new_vestige, self.stats.max_hp, self.stats.max_mp, self.user.id)
                )
                conn.execute(
                    "UPDATE stats SET stats_json=? WHERE discord_id=?",
                    (json.dumps(self.stats.to_dict()), self.user.id)
                )
                return True, "", new_vestige
        except Exception as e:
            logger.error(f"Stat upgrade error: {e}")
            return False, "System Error.", 0

    async def stat_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stat = interaction.data["custom_id"].split("_")[1]
        
        success, msg, new_vestige = await asyncio.to_thread(self._execute_upgrade, stat)
        
        if not success:
            await interaction.followup.send(f"{E.ERROR} {msg}", ephemeral=True)
            return

        # Refresh View Data
        self.p_data["vestige_pool"] = new_vestige
        # Re-fetch exp bars
        new_stats_row = await asyncio.to_thread(self.db.get_player_stats_row, self.user.id)
        
        embed = self.build_embed(self.p_data, self.stats, new_stats_row)
        view = StatusUpdateView(self.db, self.user, self.p_data, self.stats, new_stats_row)
        view.back_btn.callback = self.back_btn.callback
        
        await interaction.edit_original_response(embed=embed, view=view)

    @staticmethod
    def build_embed(p_data, stats, s_row):
        embed = discord.Embed(
            title="🜁 Attribute Awakening",
            description=f"Enhance your core attributes.\n**Vestige:** {p_data['vestige_pool']} {E.VESTIGE}",
            color=discord.Color.purple()
        )
        
        # Simple Stat Block
        base = stats.get_base_stats_dict()
        block = "\n".join([f"**{k}:** {v}" for k, v in base.items()])
        embed.add_field(name="Current Stats", value=block, inline=True)
        
        return embed

class StatusUpdateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()

async def setup(bot):
    await bot.add_cog(StatusUpdateCog(bot))