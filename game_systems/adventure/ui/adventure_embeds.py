"""
game_systems/adventure/ui/adventure_embeds.py

Handles the creation of Discord embeds for the adventure system.
Hardened: Robust JSON parsing and layout stability.
"""

import json
import logging
import random
import re

import discord

import game_systems.data.emojis as E
from cogs.ui_helpers import get_health_status_emoji, make_progress_bar
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.emojis import get_rarity_ansi
from game_systems.data.narrative_data import MISSION_FLAVOR_TEXT, OUTCOME_FLAVOR_TEXT
from game_systems.player.player_stats import PlayerStats
from game_systems.world_time import WorldTime

logger = logging.getLogger("eldoria.ui.embeds")


class AdventureEmbeds:
    @staticmethod
    def _format_log_line(line: str) -> str:
        """
        Applies ANSI coloring to adventure log lines.
        Replaces Markdown **bold** with ANSI Bold.
        """
        if not line or line == "\u200b":
            return line

        # 1. Determine Base Color
        line_lower = line.lower()

        # ANSI Constants
        ESC = "\u001b"
        RESET = f"{ESC}[0m"
        BOLD = f"{ESC}[1m"

        # Default: Reset (let Discord handle it, usually white/gray)
        color_code = f"{ESC}[0;37m"

        # Check context for color
        if any(
            x in line_lower
            for x in [
                "you take",
                "strikes you",
                "ambush",
                "defeated",
                "fallen",
                "fail",
                "miss",
            ]
        ):
            color_code = f"{ESC}[0;31m"  # Red
        elif any(x in line_lower for x in ["you hit", "you deal", "critical", "cast", "attack", "shift into"]):
            color_code = f"{ESC}[0;36m"  # Cyan
        elif any(x in line_lower for x in ["heal", "recover", "restored", "buff"]):
            color_code = f"{ESC}[0;32m"  # Green
        elif any(x in line_lower for x in ["found", "gained", "looted", "victory", "level up", "xp", "aurum"]):
            color_code = f"{ESC}[0;33m"  # Yellow/Gold
        elif any(x in line_lower for x in ["fled", "escape"]):
            color_code = f"{ESC}[0;34m"  # Blue

        # 2. Replace Markdown Bold (**text**) with ANSI Bold
        def replacer(match):
            return f"{BOLD}{match.group(1)}{RESET}{color_code}"

        formatted_line = re.sub(r"\*\*(.*?)\*\*", replacer, line)

        # 3. Wrap line in color
        return f"{color_code}{formatted_line}{RESET}"

    @staticmethod
    def build_exploration_embed(
        location_id: str,
        log: list,
        player_stats: PlayerStats,
        vitals: dict,
        active_monster: dict | None,
    ) -> discord.Embed:
        """
        Generates the main game interface embed.
        Adapts based on whether a monster is currently active (Manual Mode) or not.
        """

        loc_data = LOCATIONS.get(location_id, {"name": "Unknown Zone", "emoji": E.MAP})

        # 1. Determine State (Combat vs Exploration)
        # active_monster is now passed directly, decoupling from DB session row

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

        # Apply ANSI Formatting
        formatted_log = [AdventureEmbeds._format_log_line(line) for line in final_log]
        log_text = "```ansi\n" + "\n".join(formatted_log) + "\n```"

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

            # Check for charged skill telegraph
            charged_skill = active_monster.get("charged_skill")
            if charged_skill:
                warning = f"\n⚠️ **CHARGING:** {charged_skill.get('name', 'Unknown Skill')}"
                val = f"**HP:** `{bar}` {m_hp}/{m_max}{warning}"
            else:
                val = f"**HP:** `{bar}` {m_hp}/{m_max}"

            embed.add_field(
                name=f"VS. {active_monster.get('name', 'Enemy')}",
                value=val,
                inline=True,
            )

        # 6. World Time Field
        time_flavor = WorldTime.get_phase_flavor()
        embed.add_field(name="🕒 World Time", value=time_flavor, inline=False)

        # 7. Footer
        if active_monster:
            embed.set_footer(text="Choose your combat action • Field Pack to use items")
        else:
            embed.set_footer(text="Press Forward to continue • Field Pack to manage items")

        return embed

    @staticmethod
    def build_summary_embed(summary: dict, location_id: str) -> discord.Embed:
        """Constructs the mission report embed."""
        s = summary
        loc_data = LOCATIONS.get(location_id, {})
        location_name = loc_data.get("name", "Unknown Zone")

        # 1. Title & Color
        if s.get("leveled_up"):
            title, color = (
                f"{E.LEVEL_UP} Level Up! Expedition Complete",
                discord.Color.gold(),
            )
        else:
            title, color = (
                f"{E.VICTORY} Expedition Complete: {location_name}",
                discord.Color.dark_green(),
            )

        # 2. Determine Flavor Text
        if s.get("leveled_up"):
            flavor_text = random.choice(OUTCOME_FLAVOR_TEXT["level_up"])
        else:
            # Try to get location-specific flavor
            loc_flavors = MISSION_FLAVOR_TEXT.get(location_id)
            if loc_flavors:
                flavor_text = random.choice(loc_flavors)
            else:
                flavor_text = random.choice(OUTCOME_FLAVOR_TEXT["default"])

        embed = discord.Embed(title=title, description=f"*{flavor_text}*", color=color)

        # 2. Rewards
        rewards = []
        if (xp := s.get("xp_gained", 0)) > 0:
            rewards.append(f"{E.EXP} **+{xp} XP**")
        if (au := s.get("aurum_gained", 0)) > 0:
            rewards.append(f"{E.AURUM} **+{au} Aurum**")
        if logs := s.get("faction_logs"):
            rewards.extend(f"• {log_entry}" for log_entry in logs)

        if rewards:
            embed.add_field(name="Rewards", value="\n".join(rewards), inline=False)

        # 3. Loot
        loot_lines = []
        for i in s.get("loot", []):
            item_text = f"{i['name']} (x{i['amount']})"
            loot_lines.append(f"• {get_rarity_ansi(i.get('rarity'), item_text)}")

        if loot_lines:
            val = "```ansi\n" + "\n".join(loot_lines[:15]) + ("\n...and more" if len(loot_lines) > 15 else "") + "\n```"
            embed.add_field(name=f"{E.ITEM_BOX} Gathered Loot", value=val, inline=False)
        else:
            embed.add_field(
                name=f"{E.ITEM_BOX} Gathered Loot",
                value="*No resources found.*",
                inline=False,
            )

        # 4. Level Up
        if s.get("leveled_up"):
            embed.add_field(
                name="🌟 Ascension",
                value=f"**Level {s.get('old_level')}** ➜ **Level {s.get('new_level')}**",
                inline=False,
            )

        # 5. Full Inventory Warning
        if failed := s.get("failed_items"):
            names = sorted(list(set(f["item_name"] for f in failed)))
            embed.add_field(
                name=f"{E.WARNING} Lost Items (Full Pack)",
                value=", ".join(names),
                inline=False,
            )

        # 6. Achievements
        if new_titles := s.get("new_titles"):
            embed.add_field(name="🏆 Achievements Unlocked", value=new_titles, inline=False)

        embed.set_footer(text="Your journey is recorded in the archives.")
        return embed

    @staticmethod
    def build_status_embed(
        session: dict,
        location_data: dict,
        time_remaining: str,
        steps_completed: int,
    ) -> discord.Embed:
        """
        Displays the status of an active background adventure.
        """
        location_name = location_data.get("name", "Unknown Zone")
        emoji = location_data.get("emoji", E.MAP)

        embed = discord.Embed(
            title=f"{emoji} Expedition in Progress: {location_name}",
            description="*The party is currently exploring the wilds...*",
            color=discord.Color.blue(),
        )

        embed.add_field(name="⏳ Time Remaining", value=f"**{time_remaining}**", inline=True)
        embed.add_field(name="👣 Progress", value=f"**{steps_completed} Steps**", inline=True)

        # Loot Preview
        try:
            loot_collected = json.loads(session.get("loot_collected", "{}"))
            loot_count = sum(loot_collected.values())
            embed.add_field(
                name=f"{E.ITEM_BOX} Loot Gathered",
                value=f"**{loot_count} Items**",
                inline=True,
            )
        except Exception:
            embed.add_field(name=f"{E.ITEM_BOX} Loot Gathered", value="*Unknown*", inline=True)

        # Show last log entry for flavor
        try:
            logs = json.loads(session.get("logs", "[]"))
            if logs:
                last_log = logs[-1]
                # If it's a list (combat sequence), take the last string
                if isinstance(last_log, list):
                    last_log = last_log[-1]
                embed.add_field(name="📝 Latest Report", value=f"*{last_log}*", inline=False)
        except Exception:
            pass

        embed.set_footer(text="Check back later for the full report.")
        return embed

    @staticmethod
    def build_death_embed(session: dict, location_data: dict) -> discord.Embed:
        """
        Displays the death report for a failed adventure.
        """
        location_name = location_data.get("name", "Unknown Zone")

        embed = discord.Embed(
            title=f"{E.SKULL} Expedition Failed: {location_name}",
            description="**You have fallen in battle.**\n*Your body was recovered, but at a great cost.*",
            color=discord.Color.dark_red(),
        )

        # Parse logs to find the death cause (or show last few lines)
        try:
            logs = json.loads(session.get("logs", "[]"))
            # Get last few lines to show what happened
            death_log = []

            # Walk backwards to find relevant logs
            count = 0
            for entry in reversed(logs):
                if count >= 5:
                    break
                if isinstance(entry, list):
                    for sub_entry in reversed(entry):
                         if count >= 5:
                             break
                         death_log.insert(0, AdventureEmbeds._format_log_line(sub_entry))
                         count += 1
                else:
                    death_log.insert(0, AdventureEmbeds._format_log_line(entry))
                    count += 1

            log_text = "```ansi\n" + "\n".join(death_log) + "\n```"
            embed.add_field(name="💀 Cause of Death", value=log_text, inline=False)

        except Exception:
            embed.add_field(name="💀 Cause of Death", value="*The records are lost...*", inline=False)

        embed.set_footer(text="Rest and recover at the Infirmary.")
        return embed
