"""
combat_handler.py

Manages combat initialization and turn resolution.
Hardened: Syncs session XP to prevent duplicate level-up messages.
"""

import logging
import random
import uuid
from typing import Any

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.events.world_event_system import WorldEventSystem
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats
from game_systems.world_time import WorldTime

logger = logging.getLogger("eldoria.combat")


class CombatHandler:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id

    def initiate_combat(
        self, location: dict[str, Any], player_level: int | None = None
    ) -> tuple[dict[str, Any] | None, str]:
        """
        Selects a monster and prepares the combat session.
        """
        try:
            # 1. Day/Night Cycle Check
            is_night = WorldTime.is_night()

            # Select Pool
            if is_night and "night_monsters" in location:
                monster_pool = list(location["night_monsters"])
            else:
                monster_pool = list(location.get("monsters", []))

            # 2. Conditional Spawns (Level Check)
            conditionals = location.get("conditional_monsters", [])
            if conditionals:
                # OPTIMIZATION: Use passed level if available, otherwise fetch from DB
                if player_level is None:
                    player_level = self.db.get_player_field(self.discord_id, "level") or 1

                for cond in conditionals:
                    if player_level >= cond.get("min_level", 1):
                        monster_pool.append((cond["monster_key"], cond["weight"]))

            if not monster_pool:
                return None, "The area is silent. No threats detected."

            # 3. Select Monster
            choices, weights = zip(*monster_pool)
            monster_key = random.choices(choices, weights=weights, k=1)[0]

            template = MONSTERS.get(monster_key)
            if not template:
                logger.error(f"Monster key {monster_key} not found in database.")
                return None, "You sense a presence, but it fades."

            # 4. Instantiate Monster
            active_monster = {
                "name": template["name"],
                "level": template["level"],
                "tier": template["tier"],
                "HP": template["hp"],
                "max_hp": template["hp"],
                "MP": 10 + (template["level"] * 3),
                "ATK": template["atk"],
                "DEF": template["def"],
                "xp": template["xp"],
                "drops": list(template.get("drops", [])),
                "skills": list(template.get("skills", [])),
            }

            # --- WORLD EVENT HOOK ---
            try:
                event_system = WorldEventSystem(self.db)
                event = event_system.get_current_event()

                if event:
                    modifiers = event.get("modifiers", {})

                    # 1. Apply Stat Buffs
                    buff_mult = modifiers.get("monster_buff", 1.0)
                    if buff_mult > 1.0:
                        active_monster["HP"] = int(active_monster["HP"] * buff_mult)
                        active_monster["max_hp"] = int(active_monster["max_hp"] * buff_mult)
                        active_monster["ATK"] = int(active_monster["ATK"] * buff_mult)

                    # 2. Event Specific Flavor
                    if event["type"] == WorldEventSystem.BLOOD_MOON:
                        # 30% chance for Blood-Crazed prefix
                        if random.random() < 0.30:
                            active_monster["name"] = f"Blood-Crazed {active_monster['name']}"
                            active_monster["xp"] = int(active_monster["xp"] * 1.5)
                            # Add Blood Shard drop (30% chance)
                            # drops is a list of tuples (key, chance)
                            # We create a new list to avoid modifying the template's list in memory cache if it was shared
                            # (Though strictly speaking, template["drops"] is usually a tuple or list, and we copied it above?)
                            # Wait, above: "drops": template.get("drops", [])
                            # If template["drops"] is a list, it might be a reference.
                            # But looking at monste data, it's usually defined as a tuple of tuples or list of tuples.
                            # Safe copy:
                            active_monster["drops"] = list(active_monster["drops"])
                            active_monster["drops"].append(("blood_shard", 30))
                            active_monster["is_blood_crazed"] = True

            except Exception as e:
                logger.error(f"World event check failed: {e}")
            # ------------------------

            # --- EVENT: SPECTRAL TIDE ---
            try:
                active_tourney = self.db.get_active_tournament()
                if active_tourney and active_tourney["type"] == "spectral_tide":
                    # 20% Chance for Spectral variant
                    if random.random() < 0.20:
                        active_monster["name"] = f"Spectral {active_monster['name']}"
                        active_monster["HP"] = int(active_monster["HP"] * 1.2)
                        active_monster["max_hp"] = int(active_monster["max_hp"] * 1.2)
                        active_monster["ATK"] = int(active_monster["ATK"] * 1.2)
                        # Guaranteed Ectoplasm drop
                        active_monster["drops"].append(("ectoplasm", 100))
                        active_monster["is_spectral"] = True
            except Exception as e:
                logger.error(f"Event check failed: {e}")
            # ----------------------------

            phrase = CombatPhrases.opening(active_monster)

            # Prepend Spectral Flavor
            if active_monster.get("is_spectral"):
                phrase = f"👻 **The air turns grave-cold!** A spectral entity manifests!\n{phrase}"

            # Prepend Time Phase Flavor
            time_flavor = WorldTime.get_phase_flavor()
            phrase = f"{time_flavor}\n{phrase}"

            return active_monster, phrase

        except Exception as e:
            logger.error(f"Combat init failed for {self.discord_id}: {e}", exc_info=True)
            return None, "An error occurred while tracking the enemy."

    def resolve_turn(
        self,
        active_monster: dict[str, Any],
        battle_report: dict[str, Any],
        accumulated_exp: int = 0,
        context: dict[str, Any] | None = None,
        persist_vitals: bool = True,
        action: str = "auto",
        stance: str = "balanced",
    ) -> dict[str, Any]:
        """
        Executes a full combat round (Player vs Monster).
        Args:
            accumulated_exp: XP earned in this session but not yet saved to DB.
            context: Optional pre-fetched data to avoid DB calls.
            persist_vitals: Whether to write HP/MP to DB immediately.
            stance: Player's current combat stance (aggressive, balanced, defensive).
        """
        vitals = None
        try:
            # 1. Load Data
            if context:
                player_stats = context["player_stats"]
                stats_dict = context.get("stats_dict")
                vitals = context["vitals"]
                p_row = context["player_row"]
                skills = context["skills"]
                boosts = context.get("active_boosts", {})
                player_debuffs = context.get("player_debuffs", [])
            else:
                stats_json = self.db.get_player_stats_json(self.discord_id)
                player_stats = PlayerStats.from_dict(stats_json)

                # Apply Active Buffs (Manual Mode)
                self.db.clear_expired_buffs(self.discord_id)
                active_buffs = self.db.get_active_buffs(self.discord_id)
                player_debuffs = []

                for buff in active_buffs:
                    if buff["stat"] in ["poison", "bleed"]:
                        # Manual parsing
                        # We don't have easy access to WorldTime here without import loop?
                        # WorldTime is imported.
                        # active_buffs has end_time string.
                        try:
                            end_time = WorldTime.parse(buff["end_time"])
                            duration_mins = int((end_time - WorldTime.now()).total_seconds() / 60)
                            if duration_mins > 0:
                                player_debuffs.append({
                                    "type": buff["stat"],
                                    "damage": buff["amount"],
                                    "duration": duration_mins,
                                    "name": buff["name"]
                                })
                        except Exception:
                            pass
                    else:
                        player_stats.add_bonus_stat(buff["stat"], buff["amount"])

                # Generate cached stats dict
                stats_dict = player_stats.get_total_stats_dict()

                vitals = self.db.get_player_vitals(self.discord_id)

                if not vitals:
                    raise ValueError("Player vitals not found.")

                p_row = self.db.get_player(self.discord_id)
                skills = self.db.get_combat_skills(self.discord_id)

                active_boosts_list = self.db.get_active_boosts()
                boosts = {b["boost_key"]: b["multiplier"] for b in active_boosts_list}

            # 3. Setup Wrappers & Fast-Forward State
            player_wrapper = LevelUpSystem(player_stats, p_row["level"], p_row["experience"], p_row["exp_to_next"])

            # Apply session XP so leveling logic is up to date
            if accumulated_exp > 0:
                player_wrapper.add_exp(accumulated_exp)

            player_wrapper.hp_current = vitals["current_hp"]

            # 4. Run Engine
            engine = CombatEngine(
                player=player_wrapper,
                monster=active_monster,
                player_skills=skills,
                player_mp=vitals["current_mp"],
                player_class_id=p_row["class_id"],
                active_boosts=boosts,
                stats_dict=stats_dict,
                action=action,
                player_stance=stance,
                player_debuffs=player_debuffs,
            )

            result = engine.run_combat_turn()

            # 5. Persist State (Vitals & Monster HP)
            # We update vitals immediately so if bot crashes, HP loss is saved
            if persist_vitals:
                # Use Atomic Delta Update to prevent overwriting concurrent heals
                delta_hp = result["hp_current"] - vitals["current_hp"]
                delta_mp = result["mp_current"] - vitals["current_mp"]

                self.db.update_player_vitals_delta(
                    self.discord_id,
                    delta_hp,
                    delta_mp,
                    player_stats.max_hp,
                    player_stats.max_mp,
                )
            active_monster["HP"] = result["monster_hp"]

            # 6. Update Report
            self._aggregate_battle_report(battle_report, result.get("turn_report", {}))

            # 7. Persist New Buffs
            new_buffs = result.get("new_buffs", [])
            for buff in new_buffs:
                # Convert turn duration to seconds (1 turn = 60s)
                duration_s = buff.get("duration", 3) * 60
                buff_id = uuid.uuid4().hex
                self.db.add_active_buff(
                    discord_id=self.discord_id,
                    buff_id=buff_id,
                    name=buff.get("name"),
                    stat=buff.get("stat"),
                    amount=buff.get("amount"),
                    duration_s=duration_s,
                )

            # 8. Persist Player Debuffs (Full Sync)
            # Only if debuffs changed (check if list is different?)
            # For safety, we clear existing poison/bleed and re-add active ones.
            # This handles expiration and duration updates.
            final_debuffs = result.get("player_debuffs", [])

            # Prune existing debuffs first
            # We can't easily select "poison OR bleed" in one delete call without regex or $in
            # Using loop for clarity
            for debuff_type in ["poison", "bleed"]:
                self.db.db["active_buffs"].delete_many({
                    "discord_id": self.discord_id,
                    "stat": debuff_type
                })

            for debuff in final_debuffs:
                duration_s = debuff.get("duration", 3) * 60
                if duration_s > 0:
                    buff_id = uuid.uuid4().hex
                    self.db.add_active_buff(
                        discord_id=self.discord_id,
                        buff_id=buff_id,
                        name=debuff.get("name", "Debuff"),
                        stat=debuff.get("type", "poison"),
                        amount=debuff.get("damage", 0),
                        duration_s=duration_s,
                    )

            return result

        except Exception as e:
            logger.error(f"Combat turn error for {self.discord_id}: {e}", exc_info=True)
            # Return a safe "neutral" result to prevent crash loops
            return {
                "winner": None,
                "phrases": ["*Something disrupts the flow of battle...*"],
                "hp_current": vitals["current_hp"] if vitals else 1,
                "mp_current": vitals["current_mp"] if vitals else 1,
                "monster_hp": active_monster.get("HP", 0),
                "turn_report": {},
                "active_boosts": {},
            }

    @staticmethod
    def create_empty_battle_report():
        return {
            "str_hits": 0,
            "dex_hits": 0,
            "mag_hits": 0,
            "player_crit": 0,
            "player_dodge": 0,
            "damage_taken": 0,
            "skills_used": 0,
            "skill_key_used": None,
        }

    @staticmethod
    def _aggregate_battle_report(base, turn):
        for k in base:
            if k != "skill_key_used" and k in turn:
                base[k] += turn[k]
        base["skill_key_used"] = turn.get("skill_key_used")
