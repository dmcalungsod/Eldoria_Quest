"""
game_systems/adventure/ui/adventure_embeds.py

Handles the creation of Discord embeds for the adventure system.
Hardened: Robust JSON parsing and layout stability.
"""

import datetime
import json
import logging
import random
import re

import discord

import game_systems.data.emojis as E
from cogs.utils.ui_helpers import get_health_status_emoji, make_progress_bar
from game_systems.core.world_time import WorldTime
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.emojis import get_rarity_ansi
from game_systems.data.narrative_data import MISSION_FLAVOR_TEXT, OUTCOME_FLAVOR_TEXT
from game_systems.player.player_stats import PlayerStats

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
    def build_adventure_status_embed(session: dict) -> discord.Embed:
        """
        Builds the status embed for an active auto-adventure.
        """
        loc_id = session.get("location_id")
        loc_data = LOCATIONS.get(loc_id, {"name": "Unknown Zone", "emoji": E.MAP})

        # Calculate Times
        end_time = datetime.datetime.fromisoformat(session["end_time"])
        now = WorldTime.now()

        remaining = end_time - now

        # Format duration strings
        def fmt_delta(d):
            seconds = int(d.total_seconds())
            if seconds < 0:
                return "0m"
            hours, remainder = divmod(seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"

        remaining_str = fmt_delta(remaining)
        if remaining.total_seconds() <= 0:
            remaining_str = "Complete!"
            status_text = "Ready to Return"
            color = discord.Color.gold()
        else:
            status_text = "In Progress"
            color = discord.Color.blue()

        embed = discord.Embed(
            title=f"{loc_data.get('emoji', '')} {loc_data.get('name')}",
            description=f"**Status:** {status_text}",
            color=color,
        )

        # Calculate expected steps taken based on time elapsed (1 step per minute)
        start_time = datetime.datetime.fromisoformat(session["start_time"])
        elapsed = now - start_time
        elapsed_minutes = max(0, int(elapsed.total_seconds() / 60))

        # Cap elapsed steps to duration limit if bounded
        duration_mins = session.get("duration_minutes", 60)
        if duration_mins > 0:
            elapsed_minutes = min(elapsed_minutes, duration_mins)

        # The DB steps_completed might only update when resolving. Show expected progress.
        display_steps = max(session.get('steps_completed', 0), elapsed_minutes)

        # Progress Bars
        time_bar = make_progress_bar(elapsed_minutes, duration_mins, length=10)
        steps_bar = make_progress_bar(display_steps, duration_mins, length=10)

        embed.add_field(
            name="⏳ Expedition Progress",
            value=(
                f"**Time:** `{time_bar}` {remaining_str} remaining\n"
                f"**Steps:** `{steps_bar}` {display_steps}/{duration_mins}"
            ),
            inline=False
        )

        # Player Vitals
        if "vitals" in session and session["vitals"]:
            hp = session["vitals"].get("current_hp", 0)
            mp = session["vitals"].get("current_mp", 0)
            embed.add_field(name="❤️ Vitals", value=f"**HP:** {hp} | **MP:** {mp}", inline=True)

        # Parses Kills, Exp, Aurum, and Loot
        kills = 0
        try:
            logs_raw = session.get("logs", "[]")
            logs = json.loads(logs_raw) if isinstance(logs_raw, str) else logs_raw
            for log in logs:
                log_lower = log.lower()
                if "defeated" in log_lower or "victory" in log_lower or "slain" in log_lower:
                    kills += 1
        except Exception as e:
            logger.warning(f"Failed to parse logs for kills: {e}", exc_info=True)

        exp_earned = 0
        aurum_earned = 0
        loot_text = "None yet."

        try:
            loot_raw = session.get("loot_collected", "{}")
            loot = json.loads(loot_raw) if isinstance(loot_raw, str) else loot_raw

            exp_earned = loot.get("exp", 0)
            aurum_earned = loot.get("aurum", 0)

            loot_details = []
            item_count = 0
            for item_key, count in list(loot.items()):
                if item_key in ("exp", "aurum"):
                    continue
                if item_count < 5:
                    from game_systems.data.materials import MATERIALS
                    mat = MATERIALS.get(item_key)
                    name = mat["name"] if mat else item_key.replace("_", " ").title()
                    loot_details.append(f"• {name}: {count}")
                item_count += 1

            if item_count > 5:
                loot_details.append(f"...and {item_count - 5} more types")

            if loot_details:
                loot_text = "\n".join(loot_details)
        except Exception as e:
            loot_text = "Data Error"

        # Adventure Summary
        embed.add_field(
            name="📊 Adventure Log",
            value=(
                f"⚔️ **Monsters Slain:** {kills}\n"
                f"✨ **Experience:** +{exp_earned}\n"
                f"🪙 **Aurum:** +{aurum_earned}"
            ),
            inline=True
        )

        embed.add_field(name="🎒 Loot Gathered", value=loot_text, inline=True)

        # Recent Events
        try:
            logs_raw = session.get("logs", "[]")
            logs = json.loads(logs_raw) if isinstance(logs_raw, str) else logs_raw

            if logs:
                # Get the last 3 meaningful logs, strip ANSI codes for display if needed
                recent_logs = logs[-3:]
                log_text = "\n".join(f"• {log.strip()}" for log in recent_logs)
                # Keep it under 1024 chars for embed field
                if len(log_text) > 1000:
                    log_text = log_text[:1000] + "..."
                embed.add_field(name="📜 Recent Events", value=log_text, inline=False)
            else:
                embed.add_field(name="📜 Recent Events", value="The journey has just begun...", inline=False)
        except Exception as e:
            embed.add_field(name="📜 Recent Events", value="Could not load logs.", inline=False)

        # Flavor footer
        embed.set_footer(text="Your party is exploring automatically. Click 'Refresh Status' to update.")

        return embed

    # Alias for compatibility with tests expecting 'build_status_embed'
    build_status_embed = build_adventure_status_embed

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

        # 2. Stats (Steps/Battles) - If available
        if (steps := s.get("steps_completed")) is not None:
            embed.add_field(name="👣 Distance Traveled", value=f"{steps} Steps", inline=True)

        # 3. Rewards
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

        # 7. Penalties (if any)
        if penalty_logs := s.get("penalty_logs"):
            embed.add_field(name="⚠️ Penalties", value="\n".join(penalty_logs), inline=False)

        # 8. Refunded Supplies
        if refund_logs := s.get("refund_logs"):
            embed.add_field(name="🎒 Unused Supplies", value="\n".join(refund_logs), inline=False)

        embed.set_footer(text="Your journey is recorded in the archives.")
        return embed
