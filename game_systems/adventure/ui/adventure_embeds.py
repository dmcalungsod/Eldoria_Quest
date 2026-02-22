"""
game_systems/adventure/ui/adventure_embeds.py

Handles the creation of Discord embeds for the adventure system.
Hardened: Robust JSON parsing and layout stability.
"""

import logging
import random

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
    def build_exploration_embed(
        location_id: str, log: list, player_stats: PlayerStats, vitals: dict, active_monster: dict | None
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
            title, color = f"{E.LEVEL_UP} Level Up! Expedition Complete", discord.Color.gold()
        else:
            title, color = f"{E.VICTORY} Expedition Complete: {location_name}", discord.Color.dark_green()

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
            embed.add_field(name=f"{E.ITEM_BOX} Gathered Loot", value="*No resources found.*", inline=False)

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
            embed.add_field(name=f"{E.WARNING} Lost Items (Full Pack)", value=", ".join(names), inline=False)

        # 6. Achievements
        if new_titles := s.get("new_titles"):
            embed.add_field(name="🏆 Achievements Unlocked", value=new_titles, inline=False)

        embed.set_footer(text="Your journey is recorded in the archives.")
        return embed
