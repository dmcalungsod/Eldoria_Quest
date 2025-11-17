"""
adventure_rewards.py

Handles the complex logic of granting rewards after a victory:
- XP Calculation & Level Up
- Stat Experience (Practice Mode)
- Skill Experience
- Loot Generation & Quest Updates
- Guild Kill Counters
"""

import random
import logging
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.data.materials import MATERIALS
from game_systems.items.item_manager import item_manager
from game_systems.data.emojis import get_rarity_ansi
import game_systems.data.emojis as E

logger = logging.getLogger("discord")

HIGH_RARITY_TIERS = {"Epic", "Legendary", "Mythical"}
STAT_EXP_THRESHOLD = 100
SKILL_EXP_THRESHOLD = 100
SKILL_EXP_PER_USE = 2.5

STAT_UP_MESSAGES = {
    "STR": f"{E.STR} Your arm feels stronger after the struggle. (STR +1)",
    "END": f"{E.CON} You feel more resilient, having weathered the blows. (END +1)",
    "DEX": f"{E.DEX} Your focus sharpens, finding new openings. (DEX +1)",
    "AGI": f"{E.AGI} Your body feels lighter. (AGI +1)",
    "MAG": f"{E.INT} Your understanding of the arcane deepens. (MAG +1)",
    "LCK": f"{E.LCK} The world seems to bend slightly to your will. (LCK +1)",
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

    def process_victory(self, battle_report: dict, report_list: list, combat_result: dict, quest_system, inventory_manager, session_loot):
        """
        Main entry point to process all rewards.
        Returns a list of log strings to append to the session log.
        """
        logs = []

        # 1. Process Loot & Quests
        self._process_loot_and_quests(combat_result, quest_system, inventory_manager, session_loot, logs)

        # 2. Process Stat EXP (STR/DEX/etc)
        self._process_stat_exp(battle_report, logs)

        # 3. Process Skill EXP
        self._process_skill_exp(report_list, logs)

        # 4. Guild Kill Counters
        self._increment_kill_counter(combat_result["monster_data"]["tier"])
        
        return logs

    def _process_loot_and_quests(self, combat_result, quest_system, inventory_manager, session_loot, logs):
        loot_lines = []

        # EXP
        exp_gain = combat_result["exp"]
        self._add_loot_to_session(session_loot, "exp", exp_gain)
        loot_lines.append(get_rarity_ansi("Common", f"• {exp_gain} EXP"))

        # Calculate Luck
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        luck_bonus = (stats.luck / 999) * 50.0
        loot_boost = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # Material Drops
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

        # Equipment Drops
        eq_list = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in eq_list:
            try:
                inventory_manager.add_item(
                    discord_id=self.discord_id,
                    item_key=str(item["id"]),
                    item_name=item["name"],
                    item_type="equipment",
                    rarity=item["rarity"],
                    amount=1,
                    slot=item["slot"],
                    item_source_table=item["source"],
                )
                loot_lines.append(get_rarity_ansi(item["rarity"], f"• {item['name']}"))
            except Exception as e:
                logger.error(f"Equipment add error: {e}")

        # Add Loot Box to Log
        if loot_lines:
            block = "\n".join(loot_lines)
            # Using append directly to the logs list passed by reference
            logs.append(f"\n{E.ITEM_BOX} **Loot**\n```ansi\n{block}\n```")

        # Update Quests
        self._update_quests(quest_system, combat_result["monster_data"]["name"], combat_result["drops"], logs)

    def _update_quests(self, quest_system, monster_name, drops, logs):
        updated = []
        quests = quest_system.get_player_quests(self.discord_id)

        for q in quests:
            objs = q.get("objectives", {})
            hit = False

            if "defeat" in objs and monster_name in objs["defeat"]:
                quest_system.update_progress(self.discord_id, q["id"], "defeat", monster_name)
                hit = True

            if "collect" in objs:
                for dk, _ in drops:
                    if dk in objs["collect"]:
                        quest_system.update_progress(self.discord_id, q["id"], "collect", dk)
                        hit = True

            if hit and q["title"] not in updated:
                updated.append(q["title"])
        
        if updated:
            logs.append(f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(updated)}*")

    def _process_stat_exp(self, br, logs):
        gains = {k: fn(br) for k, fn in STAT_EXP_GAINS.items()}

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp "
                    "FROM stats WHERE discord_id=?", (self.discord_id,)
                )
                row = cur.fetchone()
                if not row: return

                stats_data = json.loads(row["stats_json"])
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}
                
                curr_exp = {
                    "str_exp": row["str_exp"], "end_exp": row["end_exp"], 
                    "dex_exp": row["dex_exp"], "agi_exp": row["agi_exp"], 
                    "mag_exp": row["mag_exp"], "lck_exp": row["lck_exp"]
                }
                up_messages = []

                for exp_key, gain in gains.items():
                    if gain <= 0: continue
                    stat = exp_key.split("_")[0].upper()
                    curr_exp[exp_key] += gain

                    while curr_exp[exp_key] >= STAT_EXP_THRESHOLD:
                        curr_exp[exp_key] -= STAT_EXP_THRESHOLD
                        base_stats[stat] += 1
                        if stat in STAT_UP_MESSAGES:
                            up_messages.append(STAT_UP_MESSAGES[stat])

                for s, v in base_stats.items():
                    stats_data[s]["base"] = v

                cur.execute(
                    "UPDATE stats SET stats_json=?, str_exp=?, end_exp=?, dex_exp=?, "
                    "agi_exp=?, mag_exp=?, lck_exp=? WHERE discord_id=?",
                    (json.dumps(stats_data),
                     curr_exp["str_exp"], curr_exp["end_exp"], curr_exp["dex_exp"],
                     curr_exp["agi_exp"], curr_exp["mag_exp"], curr_exp["lck_exp"],
                     self.discord_id)
                )
                if up_messages: logs.append("\n" + "\n".join(up_messages))

        except Exception as e:
            logger.error(f"Stat EXP error: {e}")

    def _process_skill_exp(self, report_list, logs):
        uses = {}
        for rep in report_list:
            sk = rep.get("skill_key_used")
            if sk: uses[sk] = uses.get(sk, 0) + 1
        
        if not uses: return

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                up_msgs = []
                for s_key, count in uses.items():
                    gain = count * SKILL_EXP_PER_USE
                    cur.execute(
                        "SELECT skill_level, skill_exp, s.name FROM player_skills ps "
                        "JOIN skills s ON ps.skill_key=s.key_id "
                        "WHERE ps.discord_id=? AND ps.skill_key=?", (self.discord_id, s_key)
                    )
                    row = cur.fetchone()
                    if not row: continue

                    lvl, exp, name = row["skill_level"], row["skill_exp"], row["name"]
                    exp += gain
                    while exp >= SKILL_EXP_THRESHOLD:
                        exp -= SKILL_EXP_THRESHOLD
                        lvl += 1
                        up_msgs.append(f"{E.LEVEL_UP} Your **{name}** reached **Level {lvl}**!")
                    
                    cur.execute(
                        "UPDATE player_skills SET skill_level=?, skill_exp=? "
                        "WHERE discord_id=? AND skill_key=?", (lvl, exp, self.discord_id, s_key)
                    )
                if up_msgs: logs.append("\n" + "\n".join(up_msgs))
        except Exception as e:
            logger.error(f"Skill EXP error: {e}")

    def _increment_kill_counter(self, tier):
        col = {"Normal": "normal_kills", "Elite": "elite_kills", "Boss": "boss_kills"}.get(tier)
        if not col: return
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(f"UPDATE guild_members SET {col}={col}+1 WHERE discord_id=?", (self.discord_id,))
        except: pass

    def _add_loot_to_session(self, session_loot, key, amt):
        session_loot[key] = session_loot.get(key, 0) + amt