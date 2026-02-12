"""
game_systems/adventure/ui/adventure_embeds.py

Handles the creation of Discord embeds for the adventure system.
Hardened: Robust JSON parsing and layout stability.
"""

import json
import logging
import sqlite3

import discord

import game_systems.data.emojis as E
from cogs.ui_helpers import get_health_status_emoji, make_progress_bar
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.ui.embeds")


class AdventureEmbeds:
    @staticmethod
    def build_exploration_embed(
        location_id: str, log: list, player_stats: PlayerStats, vitals: sqlite3.Row, session_row: sqlite3.Row
    ) -> discord.Embed:
        """
        Generates the main game interface embed.
        Adapts based on whether a monster is currently active (Manual Mode) or not.
        """

        loc_data = LOCATIONS.get(location_id, {"name": "Unknown Zone", "emoji": E.MAP})

        # 1. Determine State (Combat vs Exploration)
        active_monster = None
        if session_row and session_row["active_monster_json"]:
            try:
                active_monster = json.loads(session_row["active_monster_json"])
            except json.JSONDecodeError:
                logger.error("Failed to parse active_monster_json for embed.")
                active_monster = None

        # 2. Base Embed Styling
        if active_monster:
            # Manual Combat Mode (Boss/Elite) -> Red Theme
            title = f"{E.COMBAT} Encounter: {active_monster.get('name', 'Enemy')}"
            color = discord.Color.dark_red()
        else:
            # Exploration / Auto-Combat Result -> Green Theme
            title = f"{loc_data.get('emoji', E.MAP)} Exploring: {loc_data['name']}"
            color = discord.Color.dark_green()

        # 3. Create Embed with FIXED HEIGHT LOG
        # We want exactly 12 lines of content to prevent UI jitter
        max_lines = 12

        # Get the last N lines
        current_lines = log[-max_lines:] if log else ["The journey begins..."]

        # Calculate padding needed
        padding_needed = max_lines - len(current_lines)

        # Add invisible characters for padding to maintain height
        if padding_needed > 0:
            padding = ["\u200b"] * padding_needed
            final_log = current_lines + padding
        else:
            final_log = current_lines

        log_text = "\n".join(final_log)

        embed = discord.Embed(
            title=title,
            description=log_text,
            color=color,
        )

        # 4. Player Vitals Field
        # Using emojis for clean layout
        try:
            hp_bar = make_progress_bar(vitals["current_hp"], player_stats.max_hp)
            mp_bar = make_progress_bar(vitals["current_mp"], player_stats.max_mp)

            # Simple status indicator
            status_icon = get_health_status_emoji(vitals["current_hp"], player_stats.max_hp)

            embed.add_field(
                name=f"Adventurer Status {status_icon}",
                value=(
                    f"{E.HP} **HP:** `{hp_bar}` {vitals['current_hp']}/{player_stats.max_hp}\n"
                    f"{E.MP} **MP:** `{mp_bar}` {vitals['current_mp']}/{player_stats.max_mp}"
                ),
                inline=True,
            )
        except Exception:
            embed.add_field(name="Adventurer Status", value="*Data Error*", inline=True)

        # 5. Monster Vitals Field (Only in Manual Mode)
        if active_monster:
            m_hp = active_monster.get("HP", 0)
            m_max = active_monster.get("max_hp", m_hp)  # Fallback
            bar = make_progress_bar(m_hp, m_max, length=12)

            embed.add_field(
                name=f"VS. {active_monster.get('name', 'Enemy')}",
                value=f"**HP:** `{bar}` {m_hp}/{m_max}",
                inline=True,
            )

        # 6. Footer
        embed.set_footer(text="Press Forward to continue • Field Pack to manage items")

        return embed
