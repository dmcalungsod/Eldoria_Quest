"""
game_systems/adventure/adventure_session.py

Coordinates adventure flow for a single player.
Hardened: Crash recovery, atomic state saving, and robust JSON handling.
"""

import json
import logging
import random
from typing import Any

from database.database_manager import DatabaseManager
from game_systems.core.world_time import TimePhase, Weather, WorldTime
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.events.world_event_system import WorldEventSystem
from game_systems.player.player_stats import PlayerStats

# Subsystems
from .adventure_rewards import AdventureRewards
from .combat_handler import CombatHandler
from .event_handler import EventHandler

logger = logging.getLogger("eldoria.session")


class AdventureSession:
    """
    Represents an ongoing adventure run for one player.
    The DB holds: location_id, logs, loot, active state, active monster json
    """

    REGEN_CHANCE = 40  # % chance the step becomes a non-combat event

    def __init__(
        self,
        db: DatabaseManager,
        quest_system,
        inventory_manager,
        discord_id: int,
        row_data: dict | None = None,
    ):
        self.db = db
        self.discord_id = discord_id

        # Helpers
        self.rewards = AdventureRewards(db, discord_id)
        self.combat = CombatHandler(db, discord_id)
        self.events = EventHandler(db, quest_system, discord_id)

        self.quest_system = quest_system
        self.inventory_manager = inventory_manager

        # Safe State Restoration
        if row_data:
            self.location_id = row_data["location_id"]
            self.active = bool(row_data["active"])
            self.version = row_data.get("version", 1)
            self.steps_completed = row_data.get("steps_completed", 0)

            # Safe JSON Load
            try:
                self.logs = json.loads(row_data["logs"]) if row_data["logs"] else []
            except json.JSONDecodeError:
                self.logs = []

            try:
                self.loot = json.loads(row_data["loot_collected"]) if row_data["loot_collected"] else {}
            except json.JSONDecodeError:
                self.loot = {}

            try:
                self.active_monster = (
                    json.loads(row_data["active_monster_json"]) if row_data["active_monster_json"] else None
                )
            except json.JSONDecodeError:
                self.active_monster = None

            # Load Supplies
            self.supplies = row_data.get("supplies", {})
        else:
            self.active = False
            self.active_monster = None
            self.loot = {}
            self.logs = []
            self.location_id = None
            self.steps_completed = 0
            self.version = 1
            self.supplies = {}

    def _build_result(self, sequence: list, dead: bool, context: dict | None) -> dict[str, Any]:
        """Helper to build the standardized result dictionary."""
        return {
            "sequence": sequence,
            "dead": dead,
            "vitals": (context["vitals"] if context else {"current_hp": 0, "current_mp": 0}),
            "player_stats": context["player_stats"] if context else None,
            "active_monster": self.active_monster,
        }

    def _calculate_fatigue_multiplier(self) -> float:
        """
        Calculates monster damage multiplier based on session duration.
        Logic: > 4 hours (16 steps) -> +5% damage per hour (4 steps).
        """
        steps = getattr(self, "steps_completed", 0)
        if steps <= 16:
            return 1.0

        # Steps past threshold
        excess_steps = steps - 16

        # 5% per hour (4 steps) => 1.25% per step
        bonus = (excess_steps / 4.0) * 0.05

        # SUPPLY EFFECT: Hardtack reduces fatigue buildup by 20%
        if self.supplies.get("hardtack"):
            bonus *= 0.8

        return 1.0 + bonus

    # ======================================================================
    # MAIN STEP LOGIC
    # ======================================================================

    def _fetch_session_context(self, bundle: dict | None = None) -> dict[str, Any] | None:
        """
        Fetches all necessary data for the adventure step (combat or non-combat) in a single batch.
        Returns None if critical data (vitals) is missing.
        """
        try:
            # OPTIMIZED: Use single transaction to fetch all data
            if bundle is None:
                bundle = self.db.get_combat_context_bundle(self.discord_id)

            if not bundle:
                return None

            stats_data = bundle["stats"]
            player_stats = PlayerStats.from_dict(stats_data)

            # Apply Active Buffs (Crucial: Ensures buffs apply to both combat and gathering)
            active_buffs = bundle["buffs"]
            player_buffs = {}  # Store non-stat buffs here

            for buff in active_buffs:
                stat_key = buff["stat"]
                amount = buff["amount"]

                # Check if this is a core stat (STR, END, etc.)
                if stat_key.upper() in player_stats._stats:
                    player_stats.add_bonus_stat(stat_key, amount)
                else:
                    # Treat as a generic boost (e.g. gathering_boost)
                    # Accumulate additively
                    player_buffs[stat_key] = player_buffs.get(stat_key, 0.0) + amount

            # Extract vitals from player row
            player_row = bundle["player"]
            vitals = {
                "current_hp": player_row["current_hp"],
                "current_mp": player_row["current_mp"],
            }

            skills = bundle["skills"]

            # Global boosts are cached, so this is cheap
            active_boosts_list = self.db.get_active_boosts()
            boosts_dict = {b["boost_key"]: b["multiplier"] for b in active_boosts_list}

            # Merge Player Buffs (Additive to existing multipliers)
            for key, val in player_buffs.items():
                boosts_dict[key] = boosts_dict.get(key, 1.0) + val

            # --- WORLD EVENT BOOSTS ---
            event_system = WorldEventSystem(self.db)
            # OPTIMIZATION: Fetch event once to get both modifiers and type
            event = event_system.get_current_event()

            if event:
                boosts_dict.update(event.get("modifiers", {}))
                event_type = event["type"]
            else:
                event_type = None
            # --------------------------

            return {
                "player_stats": player_stats,
                "stats_dict": player_stats.get_total_stats_dict(),
                "vitals": vitals,
                "player_row": player_row,
                "skills": skills,
                "active_boosts": boosts_dict,
                "event_type": event_type,
            }
        except Exception as e:
            logger.error(f"Session context fetch failed: {e}")
            return None

    def _check_auto_condition(self, context: dict[str, Any]) -> bool:
        """
        Determines whether the player should use auto-combat using pre-fetched context.
        """
        if not self.active_monster:
            return False

        # Force manual for Bosses/Elites
        if self.active_monster.get("tier") in ("Boss", "Elite"):
            return False

        if not context or not context.get("vitals"):
            return False

        try:
            current_hp = context["vitals"]["current_hp"]
            # Ensure max_hp is at least 1
            if "stats_dict" in context:
                # Fallback to player_stats.max_hp if key missing
                max_hp = max(context["stats_dict"].get("HP", context["player_stats"].max_hp), 1)
            else:
                max_hp = max(context["player_stats"].max_hp, 1)
            return (current_hp / max_hp) >= 0.30
        except Exception:
            return False

    def simulate_step(
        self,
        context_bundle: dict | None = None,
        action: str = None,
        background: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """
        Executes one segment of an adventure.
        Returns: { "sequence": List[List[str]], "dead": bool, "vitals": dict, "player_stats": PlayerStats, "active_monster": dict }
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return self._build_result([["Error: Unknown location data."]], True, None)

        try:
            # --- 0. Pre-fetch Context (Optimized) ---
            # We fetch context ONCE at the start for both combat and non-combat.
            # This ensures Active Buffs are always available and reduces N+1 queries.
            context = self._fetch_session_context(context_bundle)
            if not context:
                return self._build_result([["Error: Failed to load player data."]], False, None)

            # EVENT HOOK: Check for Frostfall Threat Reduction
            threat_reduction = 1.0
            if self.location_id == "frostfall_expanse" and context.get("active_boosts"):
                threat_reduction = float(context["active_boosts"].get("frostfall_threat_reduction", 1.0))

            # --- Weather & Time System Check ---
            weather = WorldTime.get_current_weather(self.location_id)
            time_phase = WorldTime.get_current_phase()

            # --- 1. Continue Combat ---
            if self.active_monster:
                if action and action.startswith("set_stance:"):
                    stance = action.split(":", 1)[1]
                    self.active_monster["player_stance"] = stance
                    msg = f"You shift into an **{stance.capitalize()}** stance!"
                    self.logs.append(msg)
                    if persist:
                        self.save_state()
                    # Return immediate result to update UI without processing turn
                    # We wrap the msg in a list to match sequence format [[msg]]
                    return self._build_result([[msg]], False, context)

                if action == "flee":
                    return self._attempt_flee(context, persist=persist)

                if action == "defend":
                    return self._process_combat_turn(
                        context,
                        action="defend",
                        persist=persist,
                        weather=weather,
                        time_phase=time_phase,
                        threat_reduction=threat_reduction,
                    )

                if action == "special_ability":
                    return self._process_combat_turn(
                        context,
                        action="special_ability",
                        persist=persist,
                        weather=weather,
                        time_phase=time_phase,
                        threat_reduction=threat_reduction,
                    )

                should_auto = self._check_auto_condition(context)

                if background:
                    # Background: Flee if HP critical, else Auto-Combat
                    if context and context.get("vitals"):
                        current_hp = context["vitals"]["current_hp"]
                        # Ensure max_hp is at least 1
                        if "stats_dict" in context:
                            max_hp = max(context["stats_dict"].get("HP", context["player_stats"].max_hp), 1)
                        else:
                            max_hp = max(context["player_stats"].max_hp, 1)

                        if (current_hp / max_hp) < 0.30:
                            # Auto-Flee logic
                            return self._attempt_flee(context, persist=persist)

                    return self._resolve_auto_combat(
                        context,
                        background=True,
                        persist=persist,
                        weather=weather,
                        time_phase=time_phase,
                        threat_reduction=threat_reduction,
                    )

                # If explicit attack or implicit auto, and eligible -> Auto
                if (action == "attack" or not action) and should_auto:
                    return self._resolve_auto_combat(
                        context,
                        persist=persist,
                        weather=weather,
                        time_phase=time_phase,
                        threat_reduction=threat_reduction,
                    )

                # Otherwise manual single turn
                final_action = action if action else "attack"
                return self._process_combat_turn(
                    context,
                    action=final_action,
                    persist=persist,
                    weather=weather,
                    time_phase=time_phase,
                    threat_reduction=threat_reduction,
                )

            # Dynamic Combat Threshold based on Weather and Time
            # Base REGEN_CHANCE is 40 (meaning 60% combat).
            # We want Storms/Night to be more dangerous (Higher combat chance -> Lower Regen Chance).
            regen_threshold = self.REGEN_CHANCE

            # Weather Modifiers
            if weather == Weather.STORM:
                regen_threshold -= 10  # 30% Regen / 70% Combat
            elif weather == Weather.FOG:
                regen_threshold -= 5  # 35% Regen / 65% Combat
            elif weather == Weather.CLEAR:
                regen_threshold += 5  # 45% Regen / 55% Combat

            # Time Modifiers
            if time_phase == TimePhase.NIGHT:
                regen_threshold -= 10  # Night is dangerous (+10% Combat Chance)
            elif time_phase == TimePhase.DAY:
                regen_threshold += 5  # Day is safer (-5% Combat Chance)

            # --- 2. Trigger New Encounter ---
            if random.randint(1, 100) > regen_threshold:
                # OPTIMIZATION: Pass pre-fetched level to avoid DB lookup in initiate_combat
                player_level = context["player_row"].get("level", 1)
                monster, phrase = self.combat.initiate_combat(location, player_level=player_level)

                if monster:
                    # Prepend Weather Flavor to the encounter
                    weather_flavor = WorldTime.get_weather_flavor(weather)
                    phrase = f"{weather_flavor}\n{phrase}"

                    # --- NIGHT AMBUSH MECHANIC ---
                    # 20% Chance for monsters to strike first at night
                    ambush_chance = 0.20

                    # SUPPLY EFFECT: Pitch Torch reduces ambush chance by 50%
                    if self.supplies.get("pitch_torch"):
                        ambush_chance *= 0.5

                    if time_phase == TimePhase.NIGHT and random.random() < ambush_chance:
                        monster_atk = monster.get("ATK", 10)
                        damage = int(monster_atk * 0.8)  # 80% ATK damage
                        damage = max(1, damage)  # Minimum 1 damage

                        # Apply damage immediately
                        current_hp = context["vitals"]["current_hp"]
                        new_hp = max(0, current_hp - damage)
                        context["vitals"]["current_hp"] = new_hp

                        # Use Delta Update
                        max_hp = context["stats_dict"].get("HP", context["player_stats"].max_hp)
                        max_mp = context["stats_dict"].get("MP", context["player_stats"].max_mp)

                        if persist:
                            self.db.update_player_vitals_delta(self.discord_id, -damage, 0, max_hp, max_mp)

                        phrase += f"\n⚠️ **AMBUSH!** The {monster['name']} strikes from the shadows! You take **{damage}** damage!"

                    # Start new combat
                    self.active_monster = monster
                    self.logs.append(phrase)
                    if persist:
                        self.save_state()
                    return self._build_result([[phrase]], False, context)

                # Location has no monster this tick
                msg = phrase or "The path is clear for now."
                self.logs.append(msg)
                if persist:
                    self.save_state()
                return self._build_result([[msg]], False, context)

            # --- 3. Non-Combat Event ---
            location_name = location.get("name")
            # Pass the pre-fetched context to event handler
            result = self.events.resolve_non_combat(
                context=context,
                location_id=self.location_id,
                regen_chance=70,
                location_name=location_name,
                weather=weather,
                event_type=context.get("event_type"),
            )
            self.logs.extend(result["log"])

            # Process gathered loot
            if "loot" in result and result["loot"]:
                for item_key, amount in result["loot"].items():
                    self.loot[item_key] = self.loot.get(item_key, 0) + amount

            if persist:
                self.save_state()

            # Event handler might have updated vitals (e.g. regeneration)
            # Ensure context reflects this for return
            if "vitals" in result:
                context["vitals"] = result["vitals"]

            return self._build_result([result["log"]], False, context)

        except Exception as e:
            logger.error(f"Simulation error for {self.discord_id}: {e}", exc_info=True)
            return self._build_result(
                [["*An ominous force interrupts your journey (System Error).*"]],
                False,
                None,
            )

    def _attempt_flee(self, context: dict[str, Any], persist: bool = True) -> dict[str, Any]:
        """
        Calculates flee chance based on Agility vs Monster Level.
        """
        if not self.active_monster or not context:
            return self._build_result([["Error: Invalid flee state."]], False, context)

        player_stats = context["player_stats"]
        agi = player_stats.agility
        monster_level = self.active_monster.get("level", 1)

        # Formula: 50% base + 2% per Agility point diff from Monster Level
        # This rewards high agility builds.
        # Example: AGI 20 vs Lvl 10 = +20% -> 70% chance.
        bonus = (agi - monster_level) * 2
        chance = max(10, min(90, 50 + bonus))

        roll = random.randint(1, 100)

        if roll <= chance:
            # Success
            self.active_monster = None
            msg = [f"🏃 **You fled!** (Chance: {chance}%) - You escape into the shadows."]
            self.logs.extend(msg)
            if persist:
                self.save_state()
            return self._build_result([msg], False, context)
        else:
            # Fail - Trigger a "flee_failed" turn (Player misses turn, Monster attacks)
            fail_msg = f"🚫 **Escape Failed!** (Chance: {chance}%) - The enemy corners you!"
            return self._process_combat_turn(context, action="flee_failed", prepend_logs=[fail_msg], persist=persist)

    # ======================================================================
    # AUTO COMBAT SEQUENCE
    # ======================================================================

    def _resolve_auto_combat(
        self,
        context: dict[str, Any] | None = None,
        background: bool = False,
        persist: bool = True,
        weather=None,
        time_phase=None,
        threat_reduction: float = 1.0,
    ) -> dict[str, Any]:
        """
        Plays multiple combat turns automatically.
        """
        report = self.combat.create_empty_battle_report()
        turn_reports = []
        sequence: list[list[str]] = []
        is_dead = False
        player_won = False

        # Get accumulated XP to prevent duplicate level up messages
        current_session_exp = self.loot.get("exp", 0)

        if context is None:
            context = self._fetch_session_context()

        if not context:
            return self._build_result([["Error starting auto-combat."]], False, None)

        # Local pointers from context
        player_stats = context["player_stats"]
        stats_dict = context.get("stats_dict")
        # vitals are in context and updated in loop

        initial_hp = context["vitals"]["current_hp"]
        initial_mp = context["vitals"]["current_mp"]

        # Max 8 turns to avoid infinite loops
        stance = self.active_monster.get("player_stance", "balanced")
        fatigue_mult = self._calculate_fatigue_multiplier() * threat_reduction

        for _ in range(8):
            # FIX: Pass session XP
            result = self.combat.resolve_turn(
                self.active_monster,
                report,
                current_session_exp,
                context=context,
                persist_vitals=False,
                stance=stance,
                fatigue_multiplier=fatigue_mult,
                weather=weather,
                time_phase=time_phase,
            )
            turn_reports.append(result.get("turn_report", {}))

            # Update local vitals for next iteration
            context["vitals"]["current_hp"] = result["hp_current"]
            context["vitals"]["current_mp"] = result["mp_current"]

            # Add narration for this turn
            if result["phrases"]:
                sequence.append(result["phrases"])

            # Safety: Drop to manual if HP is too low
            max_hp = stats_dict.get("HP", player_stats.max_hp) if stats_dict else player_stats.max_hp
            if result["hp_current"] / max(max_hp, 1) < 0.30:
                if not background:
                    sequence.append(["\n⚠️ **Combat paused:** HP critical. Manual mode engaged."])
                # If background, we break silently. Next simulate_step will trigger _attempt_flee
                break

            if result.get("winner") == "monster":
                is_dead = True
                self.active_monster = None
                break

            if result.get("winner") == "player":
                player_won = True
                self.active_monster = None
                break

        # Save final vitals via Delta
        delta_hp = context["vitals"]["current_hp"] - initial_hp
        delta_mp = context["vitals"]["current_mp"] - initial_mp

        max_hp = stats_dict.get("HP", player_stats.max_hp) if stats_dict else player_stats.max_hp
        max_mp = stats_dict.get("MP", player_stats.max_mp) if stats_dict else player_stats.max_mp

        # Final Results Block
        final_block = []
        if player_won:
            final_block.append(
                f"\n⚔️ **Victory:** Defeated {result['monster_data']['name']} in {len(turn_reports)} rounds."
            )

            # Grant Rewards
            reward_texts = self.rewards.process_victory(
                battle_report=report,
                report_list=turn_reports,
                combat_result=result,
                quest_system=self.quest_system,
                inventory_manager=self.inventory_manager,
                session_loot=self.loot,
                location_id=self.location_id,
            )
            final_block.extend(reward_texts)

        elif is_dead:
            final_block.append("\n💀 **You have been defeated.**")

        if final_block:
            sequence.append(final_block)

        # Add to master log
        for frame in sequence:
            self.logs.extend(frame)

        if persist:
            self.save_state()

            # Update vitals only after successful save
            self.db.update_player_vitals_delta(self.discord_id, delta_hp, delta_mp, max_hp, max_mp)

        return self._build_result(sequence, is_dead, context)

    # ======================================================================
    # MANUAL COMBAT TURN
    # ======================================================================

    def _process_combat_turn(
        self,
        context: dict[str, Any] | None = None,
        action: str = "attack",
        prepend_logs: list = None,
        persist: bool = True,
        weather=None,
        time_phase=None,
        threat_reduction: float = 1.0,
    ) -> dict[str, Any]:
        """
        Executes a single combat turn for manual mode.
        """
        report = self.combat.create_empty_battle_report()

        # Extract Stance
        stance = self.active_monster.get("player_stance", "balanced")

        # FIX: Pass session XP
        current_session_exp = self.loot.get("exp", 0)

        # Capture initial HP/MP if context available
        initial_hp = context["vitals"]["current_hp"] if context else 0
        initial_mp = context["vitals"]["current_mp"] if context else 0

        fatigue_mult = self._calculate_fatigue_multiplier() * threat_reduction

        result = self.combat.resolve_turn(
            self.active_monster,
            report,
            current_session_exp,
            context=context,
            action=action,
            stance=stance,
            persist_vitals=False,  # FIX: Defer vital update
            fatigue_multiplier=fatigue_mult,
            weather=weather,
            time_phase=time_phase,
        )

        # Update context vitals from combat result
        if context:
            context["vitals"]["current_hp"] = result.get("hp_current", initial_hp)
            context["vitals"]["current_mp"] = result.get("mp_current", initial_mp)

        turn_logs = result["phrases"]
        if prepend_logs:
            turn_logs = prepend_logs + turn_logs

        is_dead = False

        # Determine outcome
        if result.get("winner") == "monster":
            is_dead = True
            self.active_monster = None
            turn_logs.append("\n💀 **You have been defeated.**")

        elif result.get("winner") == "player":
            self.active_monster = None
            turn_logs.append("\n⚔️ **Victory!**")

            reward_texts = self.rewards.process_victory(
                battle_report=report,
                report_list=[report],
                combat_result=result,
                quest_system=self.quest_system,
                inventory_manager=self.inventory_manager,
                session_loot=self.loot,
                location_id=self.location_id,
            )
            turn_logs.extend(reward_texts)

        self.logs.extend(turn_logs)

        if persist:
            self.save_state()

            # Update vitals only after successful save
            if context:
                final_hp = context["vitals"]["current_hp"]
                final_mp = context["vitals"]["current_mp"]
                delta_hp = final_hp - initial_hp
                delta_mp = final_mp - initial_mp

                # Get max stats safely
                player_stats = context["player_stats"]
                stats_dict = context.get("stats_dict")
                max_hp = stats_dict.get("HP", player_stats.max_hp) if stats_dict else player_stats.max_hp
                max_mp = stats_dict.get("MP", player_stats.max_mp) if stats_dict else player_stats.max_mp

                if delta_hp != 0 or delta_mp != 0:
                    self.db.update_player_vitals_delta(self.discord_id, delta_hp, delta_mp, max_hp, max_mp)

        return self._build_result([turn_logs], is_dead, context)

    # ======================================================================
    # PERSISTENCE
    # ======================================================================

    def save_state(self):
        """
        Writes the current adventure state to the database.
        """
        m_json = json.dumps(self.active_monster) if self.active_monster else None

        # Limit logs to prevent DB bloat
        trimmed_logs = self.logs[-30:]

        try:
            success = self.db.update_adventure_session(
                self.discord_id,
                logs=json.dumps(trimmed_logs),
                loot_collected=json.dumps(self.loot),
                active=1 if self.active else 0,
                active_monster_json=m_json,
                previous_version=self.version,
                steps_completed=getattr(self, "steps_completed", 0),
            )
            if not success:
                raise RuntimeError("Adventure session state conflict (optimistic lock failed).")
            self.version += 1

        except Exception as e:
            logger.error(f"[AdventureSession] Failed to save state for {self.discord_id}: {e}")
            raise e  # Re-raise so simulate_step handles it as a System Error
