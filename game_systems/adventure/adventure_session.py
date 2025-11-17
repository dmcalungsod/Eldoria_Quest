"""
adventure_session.py — Improved Hybrid Combat System
Option B: Improved Version
- Auto combat is safer, cleaner, and summarized
- Turn-based combat unchanged
- HP threshold works correctly
- Loot processed once
- No log spam
- Battle reports fixed
"""

import json
import random
import datetime
import logging
from typing import Optional, Dict, List, Tuple, Any

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager
from game_systems.items.item_manager import item_manager
from game_systems.data.emojis import get_rarity_ansi
import game_systems.data.emojis as E

from .adventure_events import AdventureEvents

logger = logging.getLogger("discord")

# ======================================================================
# CONSTANTS
# ======================================================================

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
    "dex_exp": lambda br: (br.get("dex_hits", 0) * 0.5)
                         + (br.get("player_crit", 0) * 2.0),
    "agi_exp": lambda br: br.get("player_dodge", 0) * 1.5,
    "end_exp": lambda br: br.get("damage_taken", 0) * 0.2,
    "mag_exp": lambda br: br.get("mag_hits", 0) * 1.0,
    "lck_exp": lambda br: 0.5,
}

# ======================================================================
# ADVENTURE SESSION
# ======================================================================

class AdventureSession:

    REGEN_CHANCE = 40  # % Chance to regen instead of new encounter

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_system: QuestSystem,
        inventory_manager: InventoryManager,
        discord_id: int,
        row_data: Optional[Dict[str, Any]] = None,
    ):
        self.db = db_manager
        self.quest_system = quest_system
        self.inventory_manager = inventory_manager
        self.discord_id = discord_id

        if row_data:
            self.location_id = row_data["location_id"]
            self.end_time = datetime.datetime.fromisoformat(row_data["end_time"])
            self.logs = json.loads(row_data["logs"])
            self.loot = json.loads(row_data["loot_collected"])
            self.active = bool(row_data["active"])
            self.active_monster = (
                json.loads(row_data["active_monster_json"])
                if row_data["active_monster_json"]
                else None
            )
        else:
            self.active = False
            self.active_monster = None

    # ==================================================================
    # DECISION LOGIC
    # ==================================================================

    def _should_auto(self) -> bool:
        """Centralized logic for determining if auto-combat should be used."""
        if not self.active_monster:
            return False

        tier = self.active_monster.get("tier", "Normal")
        if tier in ["Boss", "Elite"]:
            return False

        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        hp_percent = vitals["current_hp"] / max(stats.max_hp, 1)

        return hp_percent >= 0.30

    # ==================================================================
    # MAIN SIMULATION LOOP
    # ==================================================================

    def simulate_step(self) -> Dict[str, Any]:
        """Simulates a single adventure step."""
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location not found."], "dead": True}

        # ------------------------
        # CONTINUE COMBAT
        # ------------------------
        if self.active_monster:

            if self._should_auto():
                return self._resolve_auto_combat()
            else:
                return self._process_combat_turn()

        # ------------------------
        # NEW COMBAT?
        # ------------------------
        if random.randint(1, 100) > self.REGEN_CHANCE:
            logs = self._initiate_combat(location)
            return {"log": logs, "dead": False}

        # ------------------------
        # NON-COMBAT EVENT
        # ------------------------
        return self._resolve_non_combat_step()

    # ==================================================================
    # AUTO-COMBAT (IMPROVED + SUMMARIZED)
    # ==================================================================

    def _resolve_auto_combat(self) -> Dict[str, Any]:
        """Improved auto-combat: summarized, safe, clean."""
        logger.info("Auto-combat engaged.")

        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        max_hp = stats.max_hp

        battle_report = self._create_empty_battle_report()
        reports = []
        is_dead = False
        player_won = False

        turn_limit = 8  # Shorter for Discord clarity

        for _ in range(turn_limit):

            result = self._resolve_combat_turn(battle_report)
            turn_rep = result["turn_report"]
            reports.append(turn_rep.copy())

            # HP safety
            if result["hp_current"] / max_hp < 0.30:
                break

            if result.get("winner") == "monster":
                is_dead = True
                self.active = False
                self.active_monster = None
                break

            if result.get("winner") == "player":
                player_won = True
                self.active_monster = None
                break

        # -------------------------
        # POST-FIGHT PROCESSING
        # -------------------------
        logs = []

        if player_won:
            self._process_victory_rewards(
                battle_report, reports, result, logs
            )

            # SUMMARIZED AUTO RESULT
            logs.append(
                f"{E.SWORDS} You swiftly defeat the **{result['monster_data']['name']}** "
                f"in `{len(reports)}` rounds."
            )

        elif is_dead:
            logs.append(f"{E.SKULL} You were slain in auto-combat...")

        else:
            logs.append(
                f"{E.WARNING} Combat became dangerous! HP dropped below 30%. "
                f"Auto-combat paused."
            )

        self.logs.extend(logs)
        self.save_state()

        return {"log": logs, "dead": is_dead}

    # ==================================================================
    # TURN-BASED COMBAT (1 ROUND)
    # ==================================================================

    def _process_combat_turn(self) -> Dict[str, Any]:
        """Executes one turn for manual mode."""
        logger.info("Turn-based combat turn.")

        battle_report = self._create_empty_battle_report()
        result = self._resolve_combat_turn(battle_report)

        logs = result["phrases"]
        is_dead = False

        if result.get("winner") == "monster":
            is_dead = True
            self.active_monster = None
            self.active = False

        elif result.get("winner") == "player":
            self._process_victory_rewards(
                battle_report,
                [battle_report.copy()],
                result,
                logs
            )
            self.active_monster = None

        self.logs.extend(logs)
        self.save_state()

        return {"log": logs, "dead": is_dead}

    # ==================================================================
    # NON-COMBAT STEPS
    # ==================================================================

    def _resolve_non_combat_step(self) -> Dict[str, Any]:
        if random.randint(1, 100) <= 70:
            result = self._perform_regeneration()
        else:
            result = self._perform_quest_event()

        self.logs.extend(result["log"])
        self.save_state()
        return result

    # ==================================================================
    # COMBAT HELPER LOGIC
    # ==================================================================

    def _initiate_combat(self, location: Dict[str, Any]) -> List[str]:
        try:
            monster_pool = location["monsters"]
            choices, weights = zip(*monster_pool)
            monster_key = random.choices(choices, weights=weights, k=1)[0]

            template = MONSTERS.get(monster_key)
            if not template:
                return ["Error: Monster data missing."]

            self.active_monster = {
                "name": template["name"],
                "level": template["level"],
                "tier": template["tier"],
                "HP": template["hp"],
                "max_hp": template["hp"],
                "MP": 10,
                "ATK": template["atk"],
                "DEF": template["def"],
                "xp": template["xp"],
                "drops": template.get("drops", []),
            }

            phrase = CombatPhrases.opening(self.active_monster)
            self.logs.append(phrase)
            self.save_state()
            return [phrase]

        except Exception as e:
            logger.error(f"Error spawning monster: {e}")
            return ["Error: Could not start combat."]

    # ==================================================================

    def _resolve_combat_turn(self, battle_report: Dict[str, Any]) -> Dict[str, Any]:
        """Runs one turn via CombatEngine."""
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = self.db.get_player_vitals(self.discord_id)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id=?",
                (self.discord_id,)
            )
            p_row = cur.fetchone()

            cur.execute(
                """SELECT s.key_id, s.name, s.type, ps.skill_level,
                          s.mp_cost, s.power_multiplier, s.heal_power,
                          s.buff_data
                   FROM player_skills ps
                   JOIN skills s ON ps.skill_key=s.key_id
                   WHERE ps.discord_id=? AND s.type='Active'""",
                (self.discord_id,)
            )
            skills_raw = cur.fetchall()

        skills = []
        for row in skills_raw:
            s = dict(row)
            if s.get("buff_data"):
                try: s["buff_data"] = json.loads(s["buff_data"])
                except: s["buff_data"] = {}
            skills.append(s)

        player_wrapper = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )
        player_wrapper.hp_current = vitals["current_hp"]

        boosts = self._fetch_active_boosts()

        engine = CombatEngine(
            player=player_wrapper,
            monster=self.active_monster,
            player_skills=skills,
            player_mp=vitals["current_mp"],
            player_class_id=p_row["class_id"],
            active_boosts=boosts,
        )

        result = engine.run_combat_turn()

        # Update DB vitals
        self.db.set_player_vitals(
            self.discord_id,
            result["hp_current"],
            result["mp_current"]
        )

        # Update monster HP
        self.active_monster["HP"] = result["monster_hp"]

        # Merge reports
        self._aggregate_battle_report(
            battle_report, result.get("turn_report", {})
        )

        return result

    # ==================================================================
    # REWARD PROCESSING
    # ==================================================================

    def _process_victory_rewards(
        self,
        aggregated_report,
        report_list,
        combat_result,
        log_entries
    ):
        """Handles EXP, stats, skills, kills, and loot (clean)."""

        # LOOT + QUESTS
        self._process_loot_and_quests(combat_result)

        # STATS
        self._process_stat_exp(aggregated_report, log_entries)

        # SKILLS
        self._process_skill_exp(report_list, log_entries)

        # KILL COUNTER
        self._increment_kill_counter(combat_result["monster_data"]["tier"])

    # ==================================================================
    # LOOT PROCESSING (NO DUPLICATION)
    # ==================================================================

    def _process_loot_and_quests(self, combat_result):
        """Single unified loot handler (fixed)."""
        loot_lines = []

        # EXP
        exp_gain = combat_result["exp"]
        self.add_loot("exp", exp_gain)
        loot_lines.append(get_rarity_ansi("Common", f"• {exp_gain} EXP"))

        # Player stats (for luck)
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        luck_bonus = (stats.luck / 999) * 50.0
        loot_boost = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # Material drops
        for drop_key, base_chance in combat_result["drops"]:
            mat = MATERIALS.get(drop_key, {})
            rarity = mat.get("rarity", "Common")
            name = mat.get("name", drop_key)

            final_chance = base_chance * loot_boost
            if rarity in HIGH_RARITY_TIERS:
                final_chance += luck_bonus

            if random.randint(1, 100) <= final_chance:
                self.add_loot(drop_key, 1)
                loot_lines.append(get_rarity_ansi(rarity, f"• {name}"))

        # Equipment drops
        eq_list = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in eq_list:
            try:
                self.inventory_manager.add_item(
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

        # Log loot block
        if loot_lines:
            block = "\n".join(loot_lines)
            combat_result["phrases"].append(
                f"\n{E.ITEM_BOX} **Loot**\n```ansi\n{block}\n```"
            )

        # Quest updates
        q_update = self._update_quests(
            combat_result["monster_data"]["name"],
            combat_result["drops"]
        )
        if q_update:
            combat_result["phrases"].append(
                f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(q_update)}*"
            )

    # ==================================================================
    # STAT & SKILL PROCESSING
    # ==================================================================

    def _process_stat_exp(self, br, logs):
        gains = {k: fn(br) for k, fn in STAT_EXP_GAINS.items()}

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp "
                    "FROM stats WHERE discord_id=?",
                    (self.discord_id,)
                )
                row = cur.fetchone()
                if not row:
                    return

                stats_data = json.loads(row["stats_json"])
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}

                curr_exp = {
                    "str_exp": row["str_exp"],
                    "end_exp": row["end_exp"],
                    "dex_exp": row["dex_exp"],
                    "agi_exp": row["agi_exp"],
                    "mag_exp": row["mag_exp"],
                    "lck_exp": row["lck_exp"]
                }

                up_messages = []

                for exp_key, gain in gains.items():
                    if gain <= 0:
                        continue
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

                if up_messages:
                    logs.append("\n" + "\n".join(up_messages))

        except Exception as e:
            logger.error(f"Stat EXP error: {e}")

    def _process_skill_exp(self, report_list, logs):
        uses = {}

        for rep in report_list:
            sk = rep.get("skill_key_used")
            if sk:
                uses[sk] = uses.get(sk, 0) + 1

        if not uses:
            return

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                up_msgs = []

                for s_key, count in uses.items():
                    gain = count * SKILL_EXP_PER_USE

                    cur.execute(
                        "SELECT skill_level, skill_exp, s.name "
                        "FROM player_skills ps "
                        "JOIN skills s ON ps.skill_key=s.key_id "
                        "WHERE ps.discord_id=? AND ps.skill_key=?",
                        (self.discord_id, s_key)
                    )
                    row = cur.fetchone()
                    if not row:
                        continue

                    lvl, exp, name = row["skill_level"], row["skill_exp"], row["name"]
                    exp += gain

                    while exp >= SKILL_EXP_THRESHOLD:
                        exp -= SKILL_EXP_THRESHOLD
                        lvl += 1
                        up_msgs.append(
                            f"{E.LEVEL_UP} Your **{name}** reached **Level {lvl}**!"
                        )

                    cur.execute(
                        "UPDATE player_skills SET skill_level=?, skill_exp=? "
                        "WHERE discord_id=? AND skill_key=?",
                        (lvl, exp, self.discord_id, s_key)
                    )

                if up_msgs:
                    logs.append("\n" + "\n".join(up_msgs))

        except Exception as e:
            logger.error(f"Skill EXP error: {e}")

    # ==================================================================
    # NON-COMBAT EVENTS
    # ==================================================================

    def _perform_regeneration(self):
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)

        cur_hp, cur_mp = vitals["current_hp"], vitals["current_mp"]
        max_hp, max_mp = stats.max_hp, stats.max_mp

        if cur_hp >= max_hp and cur_mp >= max_mp:
            return {"log": [AdventureEvents.no_event_found()], "dead": False}

        regen_hp = max(1, int(stats.endurance * 0.5) + 1)
        regen_mp = max(1, int(stats.magic * 0.5) + 1)

        new_hp = min(cur_hp + regen_hp, max_hp)
        new_mp = min(cur_mp + regen_mp, max_mp)

        self.db.set_player_vitals(self.discord_id, new_hp, new_mp)

        logs = AdventureEvents.regeneration()
        if new_hp > cur_hp:
            logs.append(f"You regenerated `{new_hp - cur_hp}` HP.")
        if new_mp > cur_mp:
            logs.append(f"You regenerated `{new_mp - cur_mp}` MP.")

        return {"log": logs, "dead": False}

    def _perform_quest_event(self):
        quests = self.quest_system.get_player_quests(self.discord_id)
        event_types = ["gather", "locate", "examine", "survey", "escort", "retrieve", "deliver"]

        for q in quests:
            objectives = q.get("objectives", {})
            progress = q.get("progress", {})

            for obj in event_types:
                if obj in objectives:
                    tasks = objectives[obj]
                    if not isinstance(tasks, dict):
                        tasks = {tasks: 1}

                    for tk, req in tasks.items():
                        curr = (progress.get(obj) or {}).get(tk, 0)
                        if curr < req:
                            self.quest_system.update_progress(
                                self.discord_id, q["id"], obj, tk, 1
                            )
                            return {
                                "log": [
                                    AdventureEvents.quest_event(obj, tk),
                                    f"{E.QUEST_SCROLL} *Quest Updated: {q['title']}*"
                                ],
                                "dead": False
                            }

        return {"log": [AdventureEvents.no_event_found()], "dead": False}

    # ==================================================================
    # UTILITY
    # ==================================================================

    def _fetch_active_boosts(self):
        try:
            return {b["boost_key"]: b["multiplier"] for b in self.db.get_active_boosts()}
        except:
            return {}

    @staticmethod
    def _create_empty_battle_report():
        return {
            "str_hits": 0,
            "dex_hits": 0,
            "mag_hits": 0,
            "player_crit": 0,
            "player_dodge": 0,
            "damage_taken": 0,
            "skills_used": 0,
            "skill_key_used": None
        }

    @staticmethod
    def _aggregate_battle_report(base, turn):
        for key in base:
            if key != "skill_key_used":
                base[key] += turn.get(key, 0)
        if turn.get("skill_key_used"):
            base["skill_key_used"] = turn["skill_key_used"]

    def _increment_kill_counter(self, tier):
        col = {
            "Normal": "normal_kills",
            "Elite": "elite_kills",
            "Boss": "boss_kills"
        }.get(tier)
        if not col:
            return

        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    f"UPDATE guild_members SET {col}={col}+1 WHERE discord_id=?",
                    (self.discord_id,)
                )
        except:
            pass

    def _update_quests(self, monster_name, drops):
        updated = []
        quests = self.quest_system.get_player_quests(self.discord_id)

        for q in quests:
            objs = q.get("objectives", {})
            hit = False

            # defeat
            if "defeat" in objs and monster_name in objs["defeat"]:
                self.quest_system.update_progress(
                    self.discord_id, q["id"], "defeat", monster_name
                )
                hit = True

            # collect
            if "collect" in objs:
                for dk, _ in drops:
                    if dk in objs["collect"]:
                        self.quest_system.update_progress(
                            self.discord_id, q["id"], "collect", dk
                        )
                        hit = True

            if hit and q["title"] not in updated:
                updated.append(q["title"])

        return updated

    # Utility method for loot storage
    def add_loot(self, key, amt):
        self.loot[key] = self.loot.get(key, 0) + amt

    def save_state(self):
        monster_json = json.dumps(self.active_monster) if self.active_monster else None

        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    """UPDATE adventure_sessions
                       SET logs=?, loot_collected=?, active=?, active_monster_json=?
                       WHERE discord_id=? AND active=1""",
                    (
                        json.dumps(self.logs),
                        json.dumps(self.loot),
                        1 if self.active else 0,
                        monster_json,
                        self.discord_id
                    )
                )
        except Exception as e:
            logger.error(f"Save error: {e}")
