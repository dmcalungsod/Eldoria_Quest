"""
adventure_rewards.py

Handles post-battle reward distribution, including:
- Loot generation
- Quest progression
- Stat EXP & automatic stat growth
- Skill EXP & skill level-ups
- Promotion trial results
- Guild kill counters

All messages and logs have been rewritten for clarity and thematic consistency.
"""

import random
import logging
import json

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.data.materials import MATERIALS
from game_systems.items.item_manager import item_manager
from game_systems.data.emojis import get_rarity_ansi
from game_systems.guild_system.rank_system import RankSystem
import game_systems.data.emojis as E

logger = logging.getLogger("discord")

# ----------------------------
# CONSTANTS & CONFIG
# ----------------------------

HIGH_RARITY_TIERS = {"Epic", "Legendary", "Mythical"}

STAT_EXP_THRESHOLD = 100
SKILL_EXP_THRESHOLD = 100
SKILL_EXP_PER_USE = 2.5

STAT_UP_MESSAGES = {
    "STR": f"{E.STR} Your arms feel stronger after the clash. (**STR +1**)",
    "END": f"{E.CON} You endured the blows and emerged tougher. (**END +1**)",
    "DEX": f"{E.DEX} Your precision sharpens, striking with newfound accuracy. (**DEX +1**)",
    "AGI": f"{E.AGI} Your movements feel lighter and quicker. (**AGI +1**)",
    "MAG": f"{E.INT} Your understanding of the arcane deepens. (**MAG +1**)",
    "LCK": f"{E.LCK} Fortune seems to favor you more than before. (**LCK +1**)",
}

# How much EXP each stat receives from battle activity
STAT_EXP_GAINS = {
    "str_exp": lambda br: br.get("str_hits", 0) * 0.5,
    "dex_exp": lambda br: (br.get("dex_hits", 0) * 0.5) + (br.get("player_crit", 0) * 2.0),
    "agi_exp": lambda br: br.get("player_dodge", 0) * 1.5,
    "end_exp": lambda br: br.get("damage_taken", 0) * 0.2,
    "mag_exp": lambda br: br.get("mag_hits", 0) * 1.0,
    "lck_exp": lambda br: 0.5,
}


# ----------------------------
# MAIN CLASS
# ----------------------------

class AdventureRewards:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id
        self.rank_system = RankSystem(db)

    # ------------------------------------------------------------
    # MASTER REWARD PROCESSOR
    # ------------------------------------------------------------
    def process_victory(
        self,
        battle_report: dict,
        report_list: list,
        combat_result: dict,
        quest_system,
        inventory_manager,
        session_loot,
    ):
        """
        Top-level reward handler. Called once after a victorious battle.

        Handles:
        - Promotion trial results
        - Loot & quest updates
        - Stat EXP and automatic stat increases
        - Skill EXP and level-ups
        - Guild kill statistics

        Returns: A list of log strings describing all rewards.
        """
        logs = []

        # ----------------------------
        # PROMOTION TRIAL CHECK
        # ----------------------------
        monster_data = combat_result.get("monster_data", {})
        promo_rank = monster_data.get("promotion_target")

        if promo_rank:
            success, msg = self.rank_system.finalize_promotion(self.discord_id, promo_rank)
            if success:
                logs.append(
                    f"\n{E.MEDAL} **PROMOTION SUCCESSFUL!**\n"
                    f"You have proven your strength. You are now **Rank {promo_rank}**."
                )

        # ----------------------------
        # LOOT & QUESTS
        # ----------------------------
        self._process_loot_and_quests(
            combat_result, quest_system, inventory_manager, session_loot, logs
        )

        # ----------------------------
        # STAT EXP (practice-based growth)
        # ----------------------------
        self._process_stat_exp(battle_report, logs)

        # ----------------------------
        # SKILL EXP
        # ----------------------------
        self._process_skill_exp(report_list, logs)

        # ----------------------------
        # GUILD KILL COUNTERS
        # ----------------------------
        self._increment_kill_counter(combat_result["monster_data"]["tier"])

        return logs

    # ------------------------------------------------------------
    # LOOT + QUEST LOGIC
    # ------------------------------------------------------------
    def _process_loot_and_quests(self, combat_result, quest_system, inventory_manager, session_loot, logs):
        loot_lines = []

        # RAW EXP REWARD
        exp_gain = combat_result["exp"]
        self._add_loot_to_session(session_loot, "exp", exp_gain)
        loot_lines.append(get_rarity_ansi("Common", f"• {exp_gain} EXP"))

        # Player luck affects rare drops
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        luck_bonus = (stats.luck / 999) * 50.0

        loot_boost = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # MATERIAL DROPS
        for drop_key, base_chance in combat_result["drops"]:
            mat = MATERIALS.get(drop_key, {})
            rarity = mat.get("rarity", "Common")
            name = mat.get("name", drop_key)

            final_chance = base_chance * loot_boost
            if rarity in HIGH_RARITY_TIERS:
                final_chance += luck_bonus

            if random.randint(1, 100) <= final_chance:
                self._add_loot_to_session(session_loot, drop_key, 1)
                loot_lines.append(get_rarity_ansi(rarity, f"• {name}"))

        # EQUIPMENT DROPS
        eq_list = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in eq_list:
            try:
                inventory_manager.add_item(
                    self.discord_id,
                    str(item["id"]),
                    item["name"],
                    "equipment",
                    item["rarity"],
                    1,
                    item["slot"],
                    item["source"],
                )
                loot_lines.append(get_rarity_ansi(item["rarity"], f"• {item['name']}"))
            except Exception as e:
                logger.error(f"Equipment add error: {e}")

        if loot_lines:
            block = "\n".join(loot_lines)
            logs.append(f"\n{E.ITEM_BOX} **Loot Acquired**\n```ansi\n{block}\n```")

        # QUEST UPDATES
        self._update_quests(
            quest_system,
            combat_result["monster_data"]["name"],
            combat_result["drops"],
            logs,
        )

    # ------------------------------------------------------------
    # QUEST PROGRESS
    # ------------------------------------------------------------
    def _update_quests(self, quest_system, monster_name, drops, logs):
        updated = []
        quests = quest_system.get_player_quests(self.discord_id)

        for q in quests:
            progress_made = False
            objs = q.get("objectives", {})

            if "defeat" in objs and monster_name in objs["defeat"]:
                quest_system.update_progress(self.discord_id, q["id"], "defeat", monster_name)
                progress_made = True

            if "collect" in objs:
                for dk, _ in drops:
                    if dk in objs["collect"]:
                        quest_system.update_progress(self.discord_id, q["id"], "collect", dk)
                        progress_made = True

            if progress_made:
                updated.append(q["title"])

        if updated:
            logs.append(f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(updated)}*")

    # ------------------------------------------------------------
    # STAT EXP & AUTO-LEVELING
    # ------------------------------------------------------------
    def _process_stat_exp(self, br, logs):
        """
        Practice-based stat growth system.
        """
        gains = {k: fn(br) for k, fn in STAT_EXP_GAINS.items()}

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp
                    FROM stats WHERE discord_id=?
                    """,
                    (self.discord_id,)
                )
                row = cur.fetchone()
                if not row:
                    return

                stats_data = json.loads(row["stats_json"])

                # Base stats (STR, END, etc.)
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}

                # Current EXP pools
                curr_exp = {
                    "str_exp": row["str_exp"],
                    "end_exp": row["end_exp"],
                    "dex_exp": row["dex_exp"],
                    "agi_exp": row["agi_exp"],
                    "mag_exp": row["mag_exp"],
                    "lck_exp": row["lck_exp"],
                }

                level_up_msgs = []

                # Apply EXP gains
                for exp_key, gain in gains.items():
                    if gain <= 0:
                        continue

                    stat_key = exp_key.split("_")[0].upper()
                    curr_exp[exp_key] += gain

                    # Apply stat increases
                    while curr_exp[exp_key] >= STAT_EXP_THRESHOLD:
                        curr_exp[exp_key] -= STAT_EXP_THRESHOLD
                        base_stats[stat_key] += 1

                        if stat_key in STAT_UP_MESSAGES:
                            level_up_msgs.append(STAT_UP_MESSAGES[stat_key])

                # Save updated base stats
                for s, v in base_stats.items():
                    stats_data[s]["base"] = v

                # Write back
                cur.execute(
                    """
                    UPDATE stats
                    SET stats_json=?, str_exp=?, end_exp=?, dex_exp=?, agi_exp=?, mag_exp=?, lck_exp=?
                    WHERE discord_id=?
                    """,
                    (
                        json.dumps(stats_data),
                        curr_exp["str_exp"],
                        curr_exp["end_exp"],
                        curr_exp["dex_exp"],
                        curr_exp["agi_exp"],
                        curr_exp["mag_exp"],
                        curr_exp["lck_exp"],
                        self.discord_id,
                    ),
                )

                if level_up_msgs:
                    logs.append("\n" + "\n".join(level_up_msgs))

        except Exception as e:
            logger.error(f"Stat EXP error: {e}")

    # ------------------------------------------------------------
    # SKILL EXP
    # ------------------------------------------------------------
    def _process_skill_exp(self, report_list, logs):
        """
        Awards EXP to skills based on usage.
        """
        usage_count = {}

        for entry in report_list:
            skill_key = entry.get("skill_key_used")
            if skill_key:
                usage_count[skill_key] = usage_count.get(skill_key, 0) + 1

        if not usage_count:
            return

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                messages = []

                for s_key, count in usage_count.items():
                    gain = count * SKILL_EXP_PER_USE

                    cur.execute(
                        """
                        SELECT skill_level, skill_exp, s.name
                        FROM player_skills ps
                        JOIN skills s ON ps.skill_key = s.key_id
                        WHERE ps.discord_id=? AND ps.skill_key=?
                        """,
                        (self.discord_id, s_key),
                    )

                    row = cur.fetchone()
                    if not row:
                        continue

                    lvl, exp, name = row["skill_level"], row["skill_exp"], row["name"]

                    exp += gain

                    while exp >= SKILL_EXP_THRESHOLD:
                        exp -= SKILL_EXP_THRESHOLD
                        lvl += 1
                        messages.append(f"{E.LEVEL_UP} Your **{name}** reached **Level {lvl}**!")

                    cur.execute(
                        """
                        UPDATE player_skills
                        SET skill_level=?, skill_exp=?
                        WHERE discord_id=? AND skill_key=?
                        """,
                        (lvl, exp, self.discord_id, s_key),
                    )

                if messages:
                    logs.append("\n" + "\n".join(messages))

        except Exception as e:
            logger.error(f"Skill EXP error: {e}")

    # ------------------------------------------------------------
    # GUILD KILL COUNTERS
    # ------------------------------------------------------------
    def _increment_kill_counter(self, tier):
        """
        Adds to guild kill statistics based on monster tier.
        """
        column = {
            "Normal": "normal_kills",
            "Elite": "elite_kills",
            "Boss": "boss_kills",
        }.get(tier)

        if not column:
            return

        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    f"UPDATE guild_members SET {column} = {column} + 1 WHERE discord_id=?",
                    (self.discord_id,),
                )
        except Exception:
            pass

    # ------------------------------------------------------------
    # SESSION LOOT UTILITY
    # ------------------------------------------------------------
    def _add_loot_to_session(self, session_loot, key, amt):
        session_loot[key] = session_loot.get(key, 0) + amt
