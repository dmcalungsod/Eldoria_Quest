"""
adventure_rewards.py

Handles post-combat rewards: Loot, XP, Stat growth, Skill growth.
Hardened to ensure atomic reward distribution.
"""

import json
import logging
import random
from collections import defaultdict

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.emojis import get_rarity_ansi
from game_systems.data.materials import MATERIALS
from game_systems.guild_system.rank_system import RankSystem
from game_systems.items.item_manager import item_manager
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.rewards")

# Configuration
HIGH_RARITY_TIERS = {"Epic", "Legendary", "Mythical"}
STAT_EXP_THRESHOLD = 100
SKILL_EXP_THRESHOLD = 100
SKILL_EXP_PER_USE = 2.5

STAT_UP_MESSAGES = {
    "STR": f"{E.STR} Your arms feel stronger. (**STR +1**)",
    "END": f"{E.CON} Your skin toughens. (**END +1**)",
    "DEX": f"{E.DEX} Your aim sharpens. (**DEX +1**)",
    "AGI": f"{E.AGI} You move with new grace. (**AGI +1**)",
    "MAG": f"{E.INT} Your mind expands. (**MAG +1**)",
    "LCK": f"{E.LCK} Fate smiles upon you. (**LCK +1**)",
}

STAT_EXP_GAINS = {
    "str_exp": lambda br: br.get("str_hits", 0) * 0.5,
    "dex_exp": lambda br: (br.get("dex_hits", 0) * 0.5) + (br.get("player_crit", 0) * 2.0),
    "agi_exp": lambda br: br.get("player_dodge", 0) * 1.5,
    "end_exp": lambda br: br.get("damage_taken", 0) * 0.2,
    "mag_exp": lambda br: br.get("mag_hits", 0) * 1.0,
    "lck_exp": lambda br: 0.5,
}


class AdventureRewards:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id
        self.rank_system = RankSystem(db)

    def process_victory(self, battle_report, report_list, combat_result, quest_system, inventory_manager, session_loot):
        """
        Master reward processor.
        Coordinates all sub-systems safely.
        """
        logs = []

        try:
            # 1. Promotion Trial
            monster_data = combat_result.get("monster_data", {})
            promo_rank = monster_data.get("promotion_target")

            if promo_rank:
                success, msg = self.rank_system.finalize_promotion(self.discord_id, promo_rank)
                if success:
                    logs.append(f"\n{E.MEDAL} **PROMOTION SUCCESSFUL!**\nYou are now **Rank {promo_rank}**.")

            # 2. Loot & Quests
            self._process_loot_and_quests(combat_result, quest_system, inventory_manager, session_loot, logs)

            # 3. Stat Growth
            self._process_stat_exp(battle_report, logs)

            # 4. Skill Growth
            self._process_skill_exp(report_list, logs)

            # 5. Kill Counters
            self._increment_kill_counter(monster_data.get("tier"))

        except Exception as e:
            logger.error(f"Reward processing failed for {self.discord_id}: {e}", exc_info=True)
            logs.append(f"\n{E.ERROR} *An error occurred processing some rewards.*")

        return logs

    def _process_loot_and_quests(self, combat_result, quest_system, inventory_manager, session_loot, logs):
        """Calculates drops and updates quest progress."""
        loot_bundle = defaultdict(int)
        exp_gain = combat_result["exp"]

        # Add XP to session loot immediately
        self._add_loot_to_session(session_loot, "exp", exp_gain)

        # Determine drops
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        luck_bonus = (stats.luck / 999) * 50.0
        loot_boost = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # Material Drops
        for drop_key, base_chance in combat_result.get("drops", []):
            mat = MATERIALS.get(drop_key, {})
            rarity = mat.get("rarity", "Common")
            final_chance = base_chance * loot_boost
            if rarity in HIGH_RARITY_TIERS:
                final_chance += luck_bonus

            if random.randint(1, 100) <= final_chance:
                self._add_loot_to_session(session_loot, drop_key, 1)
                loot_bundle[(mat.get("name", drop_key), rarity)] += 1

        # Equipment Drops
        eq_list = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in eq_list:
            # Add item to DB immediately to prevent loss
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
            loot_bundle[(item["name"], item["rarity"])] += 1

        # Format Logs
        loot_lines = [get_rarity_ansi("Common", f"• {exp_gain} EXP")]

        # Sort by Rarity
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythical": 5}
        sorted_loot = sorted(loot_bundle.items(), key=lambda x: (rarity_order.get(x[0][1], 0), x[0][1]))

        for (name, rarity), count in sorted_loot:
            qty = f" (x{count})" if count > 1 else ""
            loot_lines.append(get_rarity_ansi(rarity, f"• {name}{qty}"))

        if loot_lines:
            block = "\n".join(loot_lines)
            logs.append(f"{E.ITEM_BOX} **Loot Acquired**\n```ansi\n{block}```")

        # Quest Updates
        self._update_quests(quest_system, combat_result["monster_data"]["name"], combat_result.get("drops", []), logs)

    def _update_quests(self, quest_system, monster_name, drops, logs):
        updated = []
        quests = quest_system.get_player_quests(self.discord_id)

        for q in quests:
            progress_made = False
            objs = q.get("objectives", {})

            # Defeat check
            if "defeat" in objs and monster_name in objs["defeat"]:
                quest_system.update_progress(self.discord_id, q["id"], "defeat", monster_name)
                progress_made = True

            # Collect check
            if "collect" in objs:
                for dk, _ in drops:
                    if dk in objs["collect"]:
                        quest_system.update_progress(self.discord_id, q["id"], "collect", dk)
                        progress_made = True

            if progress_made:
                updated.append(q["title"])

        if updated:
            logs.append(f"\n{E.QUEST_SCROLL} *Quest Updated: {', '.join(updated)}*")

    def _process_stat_exp(self, br, logs):
        """
        Updates practice-based stat experience.
        """
        gains = {k: fn(br) for k, fn in STAT_EXP_GAINS.items()}

        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp FROM stats WHERE discord_id=?",
                    (self.discord_id,),
                ).fetchone()

                if not row:
                    return

                stats_data = json.loads(row["stats_json"])
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}

                # Mutable exp dict
                curr_exp = {k: row[k] for k in STAT_EXP_GAINS.keys()}
                level_up_msgs = []

                for exp_key, gain in gains.items():
                    if gain <= 0:
                        continue

                    stat_key = exp_key.split("_")[0].upper()
                    curr_exp[exp_key] += gain

                    # Check Threshold
                    while curr_exp[exp_key] >= STAT_EXP_THRESHOLD:
                        curr_exp[exp_key] -= STAT_EXP_THRESHOLD
                        base_stats[stat_key] += 1
                        if stat_key in STAT_UP_MESSAGES:
                            level_up_msgs.append(STAT_UP_MESSAGES[stat_key])

                # Save updates
                for s, v in base_stats.items():
                    stats_data[s]["base"] = v

                conn.execute(
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
            logger.error(f"Stat XP error: {e}")

    def _process_skill_exp(self, report_list, logs):
        """Updates skill levels."""
        usage = defaultdict(int)
        for entry in report_list:
            if entry.get("skill_key_used"):
                usage[entry["skill_key_used"]] += 1

        if not usage:
            return

        try:
            with self.db.get_connection() as conn:
                msgs = []
                for s_key, count in usage.items():
                    row = conn.execute(
                        """
                        SELECT skill_level, skill_exp, s.name
                        FROM player_skills ps JOIN skills s ON ps.skill_key = s.key_id
                        WHERE ps.discord_id=? AND ps.skill_key=?
                        """,
                        (self.discord_id, s_key),
                    ).fetchone()

                    if not row:
                        continue

                    lvl, exp, name = row["skill_level"], row["skill_exp"], row["name"]
                    gain = count * SKILL_EXP_PER_USE
                    exp += gain

                    while exp >= SKILL_EXP_THRESHOLD:
                        exp -= SKILL_EXP_THRESHOLD
                        lvl += 1
                        msgs.append(f"{E.LEVEL_UP} **{name}** reached **Level {lvl}**!")

                    conn.execute(
                        "UPDATE player_skills SET skill_level=?, skill_exp=? WHERE discord_id=? AND skill_key=?",
                        (lvl, exp, self.discord_id, s_key),
                    )

                if msgs:
                    logs.append("\n" + "\n".join(msgs))
        except Exception as e:
            logger.error(f"Skill XP error: {e}")

    def _increment_kill_counter(self, tier):
        col = {"Normal": "normal_kills", "Elite": "elite_kills", "Boss": "boss_kills"}.get(tier)
        if col:
            with self.db.get_connection() as conn:
                conn.execute(f"UPDATE guild_members SET {col} = {col} + 1 WHERE discord_id=?", (self.discord_id,))

    def _add_loot_to_session(self, session_loot, key, amt):
        session_loot[key] = session_loot.get(key, 0) + amt
