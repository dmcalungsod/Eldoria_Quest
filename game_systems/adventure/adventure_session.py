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
from game_systems.data.consumables import CONSUMABLES
from game_systems.data.skills_data import SKILLS
from game_systems.events.world_event_system import WorldEventSystem
from game_systems.player.player_stats import PlayerStats, calculate_tiered_bonus

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
                self.loot = (
                    json.loads(row_data["loot_collected"])
                    if row_data["loot_collected"]
                    else {}
                )
            except json.JSONDecodeError:
                self.loot = {}

            try:
                self.active_monster = (
                    json.loads(row_data["active_monster_json"])
                    if row_data["active_monster_json"]
                    else None
                )
            except json.JSONDecodeError:
                self.active_monster = None

            # Load Supplies
            self.supplies = row_data.get("supplies", {})
            self.start_time = row_data.get("start_time", 0)
        else:
            self.active = False
            self.active_monster = None
            self.loot = {}
            self.logs = []
            self.location_id = None
            self.steps_completed = 0
            self.version = 1
            self.supplies = {}
            self.start_time = 0

    def _build_result(
        self, sequence: list, dead: bool, context: dict | None
    ) -> dict[str, Any]:
        """Helper to build the standardized result dictionary."""
        return {
            "sequence": sequence,
            "dead": dead,
            "vitals": (
                context["vitals"] if context else {"current_hp": 0, "current_mp": 0}
            ),
            "player_stats": context["player_stats"] if context else None,
            "active_monster": self.active_monster,
        }

    def _calculate_fatigue_multiplier(self) -> float:
        """
        Calculates monster damage multiplier based on session duration.
        Logic: > 4 hours (240 steps) -> +5% damage per hour (60 steps).
        For silent_city_ouros: sensory deprivation doubles the fatigue buildup (+10% per hour).
        """
        steps = getattr(self, "steps_completed", 0)
        if steps <= 240:
            return 1.0

        # Steps past threshold
        excess_steps = steps - 240

        # 5% per hour (60 steps) => ~0.083% per step. Double for silent_city_ouros, ironhaven (thin air), and the_undergrove (toxins).
        location_id = getattr(self, "location_id", None)
        base_rate = (
            0.10
            if location_id in ("silent_city_ouros", "ironhaven", "the_undergrove")
            else 0.05
        )
        bonus = (excess_steps / 60.0) * base_rate

        # SUPPLY EFFECT: Hardtack reduces fatigue buildup by 20%
        if self.supplies.get("hardtack", 0) > 0:
            bonus *= 0.8

        return 1.0 + bonus

    def _get_max_vitals(self, context: dict) -> tuple[int, int]:
        """Returns (max_hp, max_mp) from context, using stats_dict when available."""
        stats_dict = context.get("stats_dict", {})
        player_stats = context["player_stats"]
        max_hp = max(stats_dict.get("HP", player_stats.max_hp), 1)
        max_mp = max(stats_dict.get("MP", player_stats.max_mp), 1)
        return max_hp, max_mp

    def _apply_ambush_damage(self, context: dict, monster: dict, persist: bool) -> int:
        """
        Applies night-ambush pre-combat damage to the player.
        Returns the amount of damage dealt.
        """
        monster_atk = monster.get("ATK", 10)
        stats = context.get("stats_dict", {})
        end_val = stats.get("END", 10)
        def_val = stats.get("DEF", 0)

        defense_power = calculate_tiered_bonus(end_val, 1.5) + def_val
        mitigation = defense_power * (0.3 + (0.2 * min(1, defense_power / 100)))
        mitigation *= 0.5  # Ambush penalty: defence 50% less effective

        damage = max(1, int((monster_atk * 0.8) - mitigation))

        # Apply damage to context vitals
        current_hp = context["vitals"]["current_hp"]
        context["vitals"]["current_hp"] = max(0, current_hp - damage)

        if persist:
            max_hp, max_mp = self._get_max_vitals(context)
            self.db.update_player_vitals_delta(
                self.discord_id, -damage, 0, max_hp, max_mp
            )

        return damage

    # ======================================================================
    # MAIN STEP LOGIC
    # ======================================================================

    def _fetch_session_context(
        self, bundle: dict | None = None
    ) -> dict[str, Any] | None:
        """
        Fetches all necessary data for the adventure step (combat or non-combat).
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
                max_hp = max(
                    context["stats_dict"].get("HP", context["player_stats"].max_hp), 1
                )
            else:
                max_hp = max(context["player_stats"].max_hp, 1)
            return (current_hp / max_hp) >= 0.15
        except Exception:
            return False

    def _calculate_weather_damage(
        self, max_hp: int, weather: Weather
    ) -> tuple[int, str | None]:
        """Calculates damage and returns (damage, message) based on weather."""
        damage = 0
        message = None

        weather_effects = {
            Weather.BLIZZARD: {
                "chance": 0.30,
                "dmg_pct": 0.04,
                "msg": "❄️ **Freezing Winds:** The blizzard bites deep, dealing **{damage}** cold damage!",
            },
            Weather.SANDSTORM: {
                "chance": 0.30,
                "dmg_pct": 0.04,
                "msg": "🌪️ **Scouring Sand:** The storm flays your skin, dealing **{damage}** damage!",
            },
            Weather.ASH: {
                "chance": 0.30,
                "dmg_pct": 0.03,
                "msg": "🌋 **Choking Ash:** You cough violently, taking **{damage}** damage!",
            },
            Weather.MIASMA: {
                "chance": 0.40,
                "dmg_pct": 0.03,
                "msg": "☠️ **Toxic Fumes:** The air burns your lungs! You take **{damage}** poison damage.",
            },
            Weather.GALE: {
                "chance": 0.20,
                "dmg_pct": 0.02,
                "msg": "💨 **Gale Force:** The wind knocks you down! You take **{damage}** damage!",
            },
        }

        effect = weather_effects.get(weather)
        if effect and random.random() < effect["chance"]:  # nosec B311
            damage = max(1, int(max_hp * effect["dmg_pct"]))
            message = effect["msg"].format(damage=damage)

        return damage, message

    def _apply_sanity_drain(self, context: dict, persist: bool):
        """Applies MP drain if in the Wailing Chasm or Silent City of Ouros."""
        location_id = getattr(self, "location_id", None)
        if (
            location_id in ("the_wailing_chasm", "silent_city_ouros")
            and random.random() < 0.30
        ):  # nosec B311
            max_hp = context["stats_dict"].get("HP", context["player_stats"].max_hp)
            max_mp = context["stats_dict"].get("MP", context["player_stats"].max_mp)
            mp_drain = max(1, int(max_mp * 0.02))
            current_mp = context["vitals"]["current_mp"]
            if current_mp > 0:
                new_mp = max(0, current_mp - mp_drain)
                context["vitals"]["current_mp"] = new_mp

                if location_id == "the_wailing_chasm":
                    msg = f"🧠 **Sanity Drain:** The maddening echoes of the chasm sap **{current_mp - new_mp}** MP."
                else:
                    msg = f"🧠 **Sensory Deprivation:** The absolute silence of the city saps your mind, draining **{current_mp - new_mp}** MP."

                self.logs.append(msg)
                if persist:
                    self.db.update_player_vitals_delta(
                        self.discord_id, 0, -(current_mp - new_mp), max_hp, max_mp
                    )

    def _apply_ironhaven_penalties(self, context: dict, persist: bool):
        """Applies Cold damage if in Ironhaven without thermal protection."""
        location_id = getattr(self, "location_id", None)
        if location_id == "ironhaven" and random.random() < 0.40:  # nosec B311
            # Check for thermal protection
            has_thermal = (
                context.get("active_boosts", {}).get("thermal_insulation", 0) > 0
            )
            if has_thermal:
                return

            has_torch = self.supplies.get("pitch_torch", 0) > 0

            max_hp = context.get("stats_dict", {}).get(
                "HP", context["player_stats"].max_hp
            )
            cold_dmg = max(1, int(max_hp * 0.03))

            if has_torch:
                cold_dmg = max(1, int(cold_dmg * 0.5))
                msg = f"🏔️ **Biting Cold:** The freezing winds bite, but your torch provides some warmth. You take **{cold_dmg}** HP damage."
            else:
                msg = f"🏔️ **Biting Cold:** Without thermal gear, the freezing winds of Ironhaven sap your life! You take **{cold_dmg}** HP damage."

            current_hp = context["vitals"]["current_hp"]
            if current_hp > 0:
                new_hp = max(0, current_hp - cold_dmg)
                context["vitals"]["current_hp"] = new_hp
                self.logs.append(msg)

                if persist:
                    max_mp = context.get("stats_dict", {}).get(
                        "MP", context["player_stats"].max_mp
                    )
                    self.db.update_player_vitals_delta(
                        self.discord_id, -cold_dmg, 0, max_hp, max_mp
                    )

    def _apply_undergrove_penalties(self, context: dict, persist: bool):
        """Applies Toxin Accumulation if exploring The Undergrove."""
        location_id = getattr(self, "location_id", None)
        if location_id == "the_undergrove":
            # Players continuously build up a 'Toxin' meter while exploring.
            # Using session tracking or just a periodic chance to simulate accumulation
            if not hasattr(self, "_toxin_level"):
                self._toxin_level = 0

            # Increase toxin level each step
            self._toxin_level += 1

            # Toxin applies damage or penalties periodically
            if self._toxin_level >= 5 and random.random() < 0.50:  # nosec B311
                # Check for protection (to mitigate/reset)
                has_respirator = (
                    context.get("active_boosts", {}).get("toxin_filtration", 0) > 0
                )
                if has_respirator:
                    self._toxin_level = 0  # Respirator clears it constantly
                    return

                # Check for purifying brews (consumable mitigation)
                # Purifying brews will be used automatically to clear toxin if present
                if self.supplies.get("purifying_brew", 0) > 0:
                    self.supplies["purifying_brew"] -= 1
                    self.logs.append(
                        "🧪 **Toxin Purged:** You drink a Purifying Brew, clearing the dangerous spores from your system."
                    )
                    self._toxin_level = 0
                    return

                max_hp = context.get("stats_dict", {}).get(
                    "HP", context["player_stats"].max_hp
                )

                # Toxin accumulation scales with how long you've been poisoned
                toxin_dmg = max(1, int(max_hp * (0.02 * (self._toxin_level - 4))))

                msg = f"☠️ **Toxin Accumulation:** The glowing spores choke your lungs! You suffer **{toxin_dmg}** poison damage."
                current_hp = context["vitals"]["current_hp"]
                if current_hp > 0:
                    new_hp = max(0, current_hp - toxin_dmg)
                    context["vitals"]["current_hp"] = new_hp
                    self.logs.append(msg)

                    if persist:
                        max_mp = context.get("stats_dict", {}).get(
                            "MP", context["player_stats"].max_mp
                        )
                        self.db.update_player_vitals_delta(
                            self.discord_id, -toxin_dmg, 0, max_hp, max_mp
                        )

    def _apply_environmental_effects(
        self, context: dict, weather: Weather, persist: bool = True
    ):
        """
        Applies non-combat environmental hazards based on weather.
        Modifies context["vitals"] directly.
        """
        if not context or not context.get("vitals"):
            return

        max_hp = context["stats_dict"].get("HP", context["player_stats"].max_hp)
        damage, message = self._calculate_weather_damage(max_hp, weather)

        # Apply Effects
        if damage > 0:
            current_hp = context["vitals"]["current_hp"]
            new_hp = max(0, current_hp - damage)
            context["vitals"]["current_hp"] = new_hp

            if message:
                self.logs.append(message)

            if persist:
                # Delta update
                max_mp = context["stats_dict"].get("MP", context["player_stats"].max_mp)
                self.db.update_player_vitals_delta(
                    self.discord_id, -damage, 0, max_hp, max_mp
                )

        # Wailing Chasm / Ouros - Sanity Drain (MP Drain)
        self._apply_sanity_drain(context, persist)

        # Ironhaven - Cold Survival Penalty
        self._apply_ironhaven_penalties(context, persist)

        # The Undergrove - Toxin Accumulation Penalty
        self._apply_undergrove_penalties(context, persist)

    def _handle_active_combat(
        self,
        context: dict[str, Any],
        action: str | None,
        background: bool,
        persist: bool,
        weather: Weather,
        time_phase: TimePhase,
        threat_reduction: float,
    ) -> dict[str, Any]:
        """Handles the turn if a monster is already present."""
        if action and action.startswith("set_stance:"):
            stance = action.split(":", 1)[1]
            self.active_monster["player_stance"] = stance
            msg = f"You shift into an **{stance.capitalize()}** stance!"
            self.logs.append(msg)
            if persist:
                self.save_state()
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
                max_hp, _ = self._get_max_vitals(context)

                if (current_hp / max_hp) < 0.15:
                    flee_result = self._attempt_flee(context, persist=persist)
                    flee_result["auto_retreat"] = True
                    return flee_result

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

        # Check if player is stunned (skip turn logic handled in process_combat_turn via combat_engine)
        # However, we need to ensure the action reflects this if necessary, or rely on engine.
        # Engine handles stun check internally.

        return self._process_combat_turn(
            context,
            action=final_action,
            persist=persist,
            weather=weather,
            time_phase=time_phase,
            threat_reduction=threat_reduction,
        )

    def _handle_new_encounter(
        self,
        context: dict[str, Any],
        location: dict,
        regen_threshold: int,
        persist: bool,
        weather: Weather,
        time_phase: TimePhase,
    ) -> dict[str, Any] | None:
        """
        Attempts to trigger a new combat encounter.
        Returns result dict if encounter starts (or fails to start but logs something).
        Returns None if no encounter check passed (random roll failed), allowing fall-through.
        """
        if random.randint(1, 100) <= regen_threshold:  # nosec B311
            return None

        # OPTIMIZATION: Pass pre-fetched level to avoid DB lookup in initiate_combat
        player_level = context["player_row"].get("level", 1)
        monster, phrase = self.combat.initiate_combat(
            location, player_level=player_level
        )

        if monster:
            # Prepend Weather Flavor to the encounter
            weather_flavor = WorldTime.get_weather_flavor(weather)
            phrase = f"{weather_flavor}\n{phrase}"

            # --- NIGHT AMBUSH MECHANIC ---
            ambush_chance = 0.20
            # Event Modifier
            ambush_chance += context.get("active_boosts", {}).get(
                "spectral_ambush_chance", 0.0
            )

            is_dark = (
                time_phase == TimePhase.NIGHT or self.location_id == "the_wailing_chasm"
            )
            has_torch = self.supplies.get("pitch_torch", 0) > 0

            # SUPPLY EFFECT: Pitch Torch reduces ambush chance by 50%
            if has_torch:
                ambush_chance *= 0.5

            # Wailing Chasm specific: No torch means severe ambush risk
            if self.location_id == "the_wailing_chasm" and not has_torch:
                ambush_chance += 0.40

            if is_dark and random.random() < ambush_chance:  # nosec B311
                damage = self._apply_ambush_damage(context, monster, persist)
                phrase += f"\n⚠️ **AMBUSH!** The {monster['name']} strikes from the shadows! You take **{damage}** damage!"

                if context.get("event_type") == "spectral_tide":
                    phrase += (
                        "\n👻 **Spectral Chill:** The spirits guide the enemy's strike!"
                    )

            # Start new combat
            self.active_monster = monster
            self.logs.append(phrase)
            if persist:
                self.save_state()
            return self._build_result([[phrase]], False, context)

        # Location has no monster this tick (rare but possible depending on combat handler)
        msg = phrase or "The path is clear for now."
        self.logs.append(msg)
        if persist:
            self.save_state()
        return self._build_result([[msg]], False, context)

    def _handle_exploration_event(
        self,
        context: dict[str, Any],
        location: dict,
        weather: Weather,
        persist: bool,
        time_phase: TimePhase = None,
    ) -> dict[str, Any]:
        """Resolves a non-combat exploration event."""
        location_name = location.get("name")
        # Pass the pre-fetched context to event handler
        result = self.events.resolve_non_combat(
            context=context,
            location_id=self.location_id,
            regen_chance=70,
            location_name=location_name,
            weather=weather,
            event_type=context.get("event_type"),
            supplies=self.supplies,
            time_phase=time_phase,
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

    def _prepare_simulation_context(
        self, context_bundle: dict | None
    ) -> dict[str, Any] | None:
        if (
            context_bundle
            and "player_stats" in context_bundle
            and isinstance(context_bundle["player_stats"], PlayerStats)
        ):
            return context_bundle
        return self._fetch_session_context(context_bundle)

    def _calculate_threat_reduction(self, context: dict) -> float:
        """Calculates the threat reduction multiplier based on location and active boosts."""
        threat_reduction = 1.0
        if not context.get("active_boosts"):
            return threat_reduction

        if self.location_id == "frostfall_expanse":
            threat_reduction = float(
                context["active_boosts"].get("frostfall_threat_reduction", 1.0)
            )
        elif self.location_id == "the_wailing_chasm":
            threat_reduction = float(
                context["active_boosts"].get("wailing_chasm_threat_reduction", 1.0)
            )
        elif self.location_id == "silent_city_ouros":
            threat_reduction = float(
                context["active_boosts"].get("ouros_threat_reduction", 1.0)
            )
        elif self.location_id == "the_undergrove":
            threat_reduction = float(
                context["active_boosts"].get("undergrove_threat_reduction", 1.0)
            )
        return threat_reduction

    def _consume_supplies(self):
        """Consumes supplies based on steps completed and location."""
        current_step = getattr(self, "steps_completed", 0)

        # Torch Consumption
        torch_rate = 30 if self.location_id == "the_wailing_chasm" else 60
        if current_step > 0 and current_step % torch_rate == 0:
            if self.supplies.get("pitch_torch", 0) > 0:
                self.supplies["pitch_torch"] -= 1
                if self.supplies["pitch_torch"] <= 0:
                    del self.supplies["pitch_torch"]
                    self.logs.append(
                        "🔥 **Your last torch has burned out. The darkness closes in.**"
                    )

        # Ration Consumption
        if current_step > 0 and current_step % 60 == 0:
            if self.supplies.get("hardtack", 0) > 0:
                self.supplies["hardtack"] -= 1
                if self.supplies["hardtack"] <= 0:
                    del self.supplies["hardtack"]
                    self.logs.append(
                        "🍞 **You have run out of rations. Fatigue will build faster.**"
                    )

    def _calculate_regen_threshold(
        self, context: dict, weather: Weather, time_phase: TimePhase
    ) -> int:
        """Calculates the dynamic combat threshold based on weather and time."""
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
            night_mod = context.get("active_boosts", {}).get("night_danger_mod", 0.0)
            regen_threshold -= 10 + int(night_mod * 100)  # Night is dangerous
        elif time_phase == TimePhase.DAY:
            regen_threshold += 5  # Day is safer

        return regen_threshold

    def simulate_step(
        self,
        context_bundle: dict | None = None,
        action: str = None,
        background: bool = False,
        persist: bool = True,
        weather: Weather | None = None,
        time_phase: TimePhase | None = None,
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
            context = self._prepare_simulation_context(context_bundle)

            if not context:
                return self._build_result(
                    [["Error: Failed to load player data."]], False, None
                )

            threat_reduction = self._calculate_threat_reduction(context)

            # --- Weather & Time System Check ---
            if weather is None:
                weather = WorldTime.get_current_weather(self.location_id)
            if time_phase is None:
                time_phase = WorldTime.get_current_phase()

            # --- 0.25. Supply Consumption ---
            self._consume_supplies()

            # --- 0.5. Environmental Hazards ---
            # Only apply if not already in combat
            if not self.active_monster:
                self._apply_environmental_effects(context, weather, persist)

            # --- 1. Continue Combat ---
            if self.active_monster:
                return self._handle_active_combat(
                    context,
                    action,
                    background,
                    persist,
                    weather,
                    time_phase,
                    threat_reduction,
                )

            # Dynamic Combat Threshold based on Weather and Time
            regen_threshold = self._calculate_regen_threshold(
                context, weather, time_phase
            )

            # --- 2. Trigger New Encounter ---
            combat_result = self._handle_new_encounter(
                context, location, regen_threshold, persist, weather, time_phase
            )
            if combat_result:
                return combat_result

            # --- 3. Non-Combat Event ---
            return self._handle_exploration_event(context, location, weather, persist, time_phase=time_phase)

        except Exception as e:
            logger.error(f"Simulation error for {self.discord_id}: {e}", exc_info=True)
            return self._build_result(
                [["*An ominous force interrupts your journey (System Error).*"]],
                False,
                None,
            )

    def _attempt_flee(
        self, context: dict[str, Any], persist: bool = True
    ) -> dict[str, Any]:
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

        roll = random.randint(1, 100)  # nosec B311  # nosec B311

        if roll <= chance:
            # Success
            self.active_monster = None
            msg = [
                f"🏃 **You fled!** (Chance: {chance}%) - You escape into the shadows."
            ]
            self.logs.extend(msg)
            if persist:
                self.save_state()
            return self._build_result([msg], False, context)
        else:
            # Fail - Trigger a "flee_failed" turn (Player misses turn, Monster attacks)
            fail_msg = (
                f"🚫 **Escape Failed!** (Chance: {chance}%) - The enemy corners you!"
            )
            return self._process_combat_turn(
                context, action="flee_failed", prepend_logs=[fail_msg], persist=persist
            )

    # ======================================================================
    # AUTO COMBAT SEQUENCE
    # ======================================================================

    # ======================================================================
    # AUTO COMBAT SEQUENCE
    # ======================================================================

    def _check_auto_potion_during_combat(
        self, context: dict, result: dict, max_hp: int, background: bool, sequence: list
    ) -> bool:
        """Checks and uses auto-potion if HP is critical, returns True if combat should abort."""
        if result["hp_current"] / max_hp < 0.15:
            potion_used = self._try_auto_potion(context, max_hp)
            if potion_used:
                sequence.append([potion_used])
                result["hp_current"] = context["vitals"]["current_hp"]
                return False
            else:
                if not background:
                    sequence.append(
                        ["\n⚠️ **Combat paused:** HP critical. Manual mode engaged."]
                    )
                else:
                    sequence.append(
                        ["\n⚠️ **HP Critical! Auto-Retreating to save your life!**"]
                    )
                return True
        return False

    def _process_auto_combat_victory(
        self,
        result: dict,
        turn_reports: list,
        report: dict,
        sequence: list,
        context: dict | None = None,
    ):
        """Processes victory rewards for auto combat."""
        final_block = [
            f"\n⚔️ **Victory:** Defeated {result['monster_data']['name']} in {len(turn_reports)} rounds."
        ]

        if context and "active_boosts" in context:
            result["active_boosts"] = context["active_boosts"]

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
        sequence.append(final_block)

    def _setup_auto_combat(
        self, context: dict | None, threat_reduction: float
    ) -> tuple[dict | None, int, int, int, float, str]:
        """Sets up variables for auto combat resolution."""
        if context is None:
            context = self._fetch_session_context()

        if not context:
            return None, 0, 0, 0, 1.0, "balanced"

        initial_hp = context["vitals"]["current_hp"]
        initial_mp = context["vitals"]["current_mp"]
        current_session_exp = self.loot.get("exp", 0)

        stance = self.active_monster.get("player_stance", "balanced")
        fatigue_mult = self._calculate_fatigue_multiplier() * threat_reduction

        return (
            context,
            initial_hp,
            initial_mp,
            current_session_exp,
            fatigue_mult,
            stance,
        )

    def _apply_turn_results(self, result: dict, context: dict, sequence: list):
        """Updates context vitals and sequence based on the turn result."""
        # Update local vitals for next iteration
        context["vitals"]["current_hp"] = result.get(
            "hp_current", context["vitals"]["current_hp"]
        )
        context["vitals"]["current_mp"] = result.get(
            "mp_current", context["vitals"]["current_mp"]
        )

        # Add narration for this turn
        if result.get("phrases"):
            sequence.append(result["phrases"])

    def _check_combat_winner(self, result: dict) -> tuple[bool, bool, bool]:
        """Checks for combat winner and returns (should_break, is_dead, player_won)."""
        if result.get("winner") == "monster":
            self.active_monster = None
            return True, True, False

        if result.get("winner") == "player":
            self.active_monster = None
            return True, False, True

        return False, False, False

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

        context, initial_hp, initial_mp, current_session_exp, fatigue_mult, stance = (
            self._setup_auto_combat(context, threat_reduction)
        )

        if not context:
            return self._build_result([["Error starting auto-combat."]], False, None)

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

            self._apply_turn_results(result, context, sequence)

            # Safety: Drop to manual if HP is too low
            max_hp, max_mp = self._get_max_vitals(context)
            if self._check_auto_potion_during_combat(
                context, result, max_hp, background, sequence
            ):
                break

            should_break, is_dead, player_won = self._check_combat_winner(result)
            if should_break:
                break

        # Save final vitals via Delta
        delta_hp = context["vitals"]["current_hp"] - initial_hp
        delta_mp = context["vitals"]["current_mp"] - initial_mp

        max_hp, max_mp = self._get_max_vitals(context)

        # Auto-Retreat checks
        if (
            background
            and not player_won
            and not is_dead
            and result["hp_current"] / max_hp < 0.15
        ):
            # We broke early due to HP and couldn't potion
            # So next step will be a flee, but we can also just mark it now
            pass

        # Final Results Block
        if player_won:
            self._process_auto_combat_victory(
                result, turn_reports, report, sequence, context
            )
        elif is_dead:
            sequence.append(["\n💀 **You have been defeated.**"])

        # Add to master log
        for frame in sequence:
            self.logs.extend(frame)

        if persist:
            self.save_state()

            # Update vitals only after successful save
            self.db.update_player_vitals_delta(
                self.discord_id, delta_hp, delta_mp, max_hp, max_mp
            )

        return self._build_result(sequence, is_dead, context)

    # ======================================================================
    # MANUAL COMBAT TURN
    # ======================================================================

    def _handle_combat_turn_outcome(
        self, result: dict, report: dict, turn_logs: list, context: dict | None = None
    ) -> tuple[bool, list]:
        """Processes the outcome of a single manual combat turn."""
        is_dead = False
        if result.get("winner") == "monster":
            is_dead = True
            self.active_monster = None
            turn_logs.append("\n💀 **You have been defeated.**")
        elif result.get("winner") == "player":
            self.active_monster = None
            turn_logs.append("\n⚔️ **Victory!**")
            if context and "active_boosts" in context:
                result["active_boosts"] = context["active_boosts"]
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
        return is_dead, turn_logs

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

        # Extract Stun State (Persistence)
        # We inject the stunned state into the monster dict (temporary storage) or pass it directly.
        # CombatEngine initializes `player_stunned` from `player.is_stunned`.
        # `context['player']` is a dict (row data), not object. `context['player_stats']` is object.
        # We need to set `is_stunned` on `context['player_stats']` or similar wrapper used by Engine.
        # `CombatEngine` expects `player` arg to be "LevelUpSystem wrapper (with stats + current HP)".
        # In `combat_handler.py`, it passes `player` object.
        # In `adventure_session.py`, `combat.resolve_turn` is called.

        # Check `active_monster` for persisted stun state
        is_stunned = self.active_monster.get("player_stunned", False)

        # We need to pass this to `resolve_turn`.
        # `resolve_turn` instantiates `CombatEngine`.
        # We need to ensure `CombatEngine` gets this state.
        # `CombatHandler.resolve_turn` uses `context['player_stats']` as player object (usually).
        # Let's attach the attribute to the player object in context.
        if context and "player_stats" in context:
            context["player_stats"].is_stunned = is_stunned
            context["player_stats"].is_silenced = self.active_monster.get(
                "player_silenced", False
            )

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

        # Update Persistence for Stun State
        if "player_stunned" in result:
            self.active_monster["player_stunned"] = result["player_stunned"]

        if "player_silenced" in result:
            self.active_monster["player_silenced"] = result["player_silenced"]

        turn_logs = result["phrases"]
        if prepend_logs:
            turn_logs = prepend_logs + turn_logs

        is_dead, turn_logs = self._handle_combat_turn_outcome(
            result, report, turn_logs, context
        )

        self.logs.extend(turn_logs)

        if persist:
            self.save_state()

        return self._build_result([turn_logs], is_dead, context)

    def _get_best_healing_potion(self) -> str | None:
        """Finds the best healing potion in supplies."""
        for item_key, count in self.supplies.items():
            if count <= 0:
                continue
            c_data = CONSUMABLES.get(item_key)
            if c_data and c_data["type"] == "hp":
                return item_key
        return None

    def _get_healing_multiplier(self, context: dict) -> float:
        """Calculates healing multiplier from skills and active boosts."""
        healing_multiplier = 1.0
        try:
            skills = context.get("skills", [])
            for s in skills:
                if s.get("key_id") == "triage":
                    full_skill = SKILLS.get(s.get("key_id"))
                    if full_skill and "passive_bonus" in full_skill:
                        base_potency = full_skill["passive_bonus"].get(
                            "healing_item_potency", 0
                        )
                        s_level = s.get("skill_level", 1)
                        if base_potency > 0:
                            scaling_potency = base_potency + (0.02 * (s_level - 1))
                            healing_multiplier += scaling_potency
        except Exception as e:
            logger.error(f"Error checking passive skills for auto-potion: {e}")

        # Add event/global boost
        healing_multiplier += context.get("active_boosts", {}).get(
            "healing_item_potency", 0.0
        )
        return healing_multiplier

    def _try_auto_potion(self, context: dict, max_hp: int) -> str | None:
        """
        Attempts to use a healing potion from supplies.
        Returns log string if used, None otherwise.
        """
        target_potion = self._get_best_healing_potion()
        if not target_potion:
            return None

        # Use Potion
        c_data = CONSUMABLES[target_potion]
        base_heal = c_data["effect"].get("heal", 0)

        healing_multiplier = self._get_healing_multiplier(context)

        heal_amount = int(base_heal * healing_multiplier)

        # Apply Heal
        current_hp = context["vitals"]["current_hp"]
        new_hp = min(max_hp, current_hp + heal_amount)
        actual_heal = new_hp - current_hp

        context["vitals"]["current_hp"] = new_hp

        # Decrement Supply
        self.supplies[target_potion] -= 1
        if self.supplies[target_potion] <= 0:
            del self.supplies[target_potion]

        msg = f"💊 **Auto-Potion:** Used {c_data['name']} to recover {actual_heal} HP."
        if healing_multiplier > 1.0:
            msg += f" (Boosted x{healing_multiplier:.1f})"
        return msg

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
                raise RuntimeError(
                    "Adventure session state conflict (optimistic lock failed)."
                )
            self.version += 1

        except Exception as e:
            logger.error(
                f"[AdventureSession] Failed to save state for {self.discord_id}: {e}"
            )
            raise e  # Re-raise so simulate_step handles it as a System Error
