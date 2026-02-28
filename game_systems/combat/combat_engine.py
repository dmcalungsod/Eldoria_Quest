"""
Combat Engine for Eldoria Quest

Handles a single turn of combat logic (Player -> Monster -> Player).
Hardened against data inconsistencies and missing keys.
Logging added for combat flow analysis.
"""

import logging
import random

import game_systems.data.emojis as E
from game_systems.core.world_time import TimePhase, Weather

from ..monsters.monster_actions import MonsterAI
from ..player.player_stats import calculate_tiered_bonus
from ..rewards.aurum_calculator import AurumCalculator
from ..rewards.exp_calculator import ExpCalculator
from . import combat_weather
from .combat_phrases import CombatPhrases
from .damage_formula import DamageFormula

logger = logging.getLogger("eldoria.combat_engine")


class CombatEngine:
    PLAYER_SKILL_CHANCE = 40  # 40% chance to use a skill if possible

    _STAT_HIT_MAP = {
        "STR": "str_hits",
        "DEX": "dex_hits",
        "AGI": "dex_hits",
        "MAG": "mag_hits",
        "INT": "mag_hits",
        "END": "str_hits",
        "LCK": "mag_hits",
    }

    _CLASS_SPECIALS = {
        1: {
            "name": "Cleave",
            "damage_mult": 1.5,
            "emoji": "🪓",
            "type": "str",
            "log": "You swing your weapon in a massive arc!",
        },
        2: {
            "name": "Fireball",
            "damage_mult": 2.0,
            "emoji": "🔥",
            "type": "mag",
            "log": "You unleash a torrent of arcane fire!",
        },
        3: {
            "name": "Backstab",
            "damage_mult": 1.4,
            "emoji": "🗡️",
            "type": "dex",
            "log": "You strike from the shadows with lethal precision!",
        },
        4: {
            "name": "Smite",
            "damage_mult": 0.8,
            "emoji": "✨",
            "type": "mag",
            "heal": 20,
            "log": "Holy light descends to judge your foe and mend your wounds!",
        },
        5: {
            "name": "Aimed Shot",
            "damage_mult": 1.5,
            "emoji": "🏹",
            "type": "dex",
            "crit_bonus": 50,
            "log": "You take a breath and loose a perfect shot!",
        },
    }

    def __init__(
        self,
        player,
        monster: dict,
        player_skills: list,
        player_mp: int,
        player_class_id: int,
        active_boosts: dict = None,
        active_buffs: list = None,
        stats_dict: dict = None,
        base_stats_dict: dict = None,
        action: str = "auto",
        player_stance: str = "balanced",
        monster_dmg_mult: float = 1.0,
        weather: Weather = Weather.CLEAR,
        time_phase: TimePhase = TimePhase.DAY,
    ):
        """
        player → LevelUpSystem wrapper (with stats + current HP)
        monster → DICT containing monster's CURRENT state (including current HP)
        player_skills → List of dicts of skills from DB (INCLUDES skill_level)
        player_mp → Player's current MP
        player_class_id -> The player's class ID (1=War, 2=Mage, etc.)
        active_boosts → Dict of active global boosts
        active_buffs -> List of active buffs on the player
        stats_dict → Cached dictionary of player stats to avoid property overhead
        base_stats_dict → Cached dictionary of BASE stats (for buff calculation)
        action -> Combat action ("attack", "defend", "flee_failed", "special_ability", "auto")
        player_stance -> "aggressive", "balanced", or "defensive"
        weather -> The current weather condition (modifies damage/mechanics)
        time_phase -> The current time of day
        """
        self.player = player
        self.monster = monster
        self.player_skills = player_skills
        self.player_class_id = player_class_id

        # Use cached stats if provided, otherwise generate them
        if stats_dict:
            self.stats_dict = stats_dict
        else:
            # Fallback to generating it (e.g. if caller didn't provide it)
            self.stats_dict = self.player.stats.get_total_stats_dict()

        # Handle base stats for buff calculations (Equilibrium Fix)
        if base_stats_dict:
            self.base_stats_dict = base_stats_dict
        else:
            # Fallback to total stats if base not provided
            self.base_stats_dict = self.stats_dict

        # Safe property access
        self.player_hp = getattr(player, "hp_current", 1)
        self.player_mp = player_mp
        self.monster_hp = monster.get("HP", 1)

        # Process boosts safely
        self.active_boosts_dict = active_boosts or {}
        self.active_buffs = active_buffs or []
        self.exp_boost = float(self.active_boosts_dict.get("exp_boost", 1.0))
        self.loot_boost = float(self.active_boosts_dict.get("loot_boost", 1.0))
        self.action = action

        # Fatigue / Monster Buff Logic
        self.monster_dmg_mult = monster_dmg_mult

        # Weather & Time Logic
        self.weather = weather
        self.time_phase = time_phase

        # Stance Logic
        self.player_stance = player_stance
        self.dmg_dealt_mult = 1.0
        self.dmg_taken_mult = 1.0
        self.new_buffs = []
        self.new_titles = []
        self.consumed_buff_ids = []

        # Player Status State (Initialized from player object or default False)
        # Note: Ideally this should persist in DB, but for now it's per-session or per-turn in this engine instance.
        # If CombatEngine is re-instantiated every turn, we need to pass this state in.
        # Current architecture suggests CombatEngine is transient.
        # We will check if player object has a 'stunned' attribute or similar.
        self.player_stunned = getattr(player, "is_stunned", False)

        if self.player_stance == "aggressive":
            self.dmg_dealt_mult = 1.2
            self.dmg_taken_mult = 1.2
        elif self.player_stance == "defensive":
            self.dmg_dealt_mult = 0.8
            self.dmg_taken_mult = 0.8

    def _get_effective_monster_stats(self):
        """
        Calculates monster stats with active debuffs applied.
        Returns a copy of the monster dict with modified stats.
        """
        eff_monster = self.monster.copy()

        if "debuffs" in self.monster:
            for debuff in self.monster["debuffs"]:
                if debuff.get("type") == "stat_mod":
                    # Apply percentage modifiers
                    for stat in ["ATK", "DEF", "AGI", "DEX"]:
                        key = f"{stat}_percent"
                        if key in debuff:
                            mod = float(debuff[key])
                            base_val = eff_monster.get(stat, 0)
                            # Apply modifier (additive compounding? No, simple multiplicative for now)
                            # If multiple debuffs affect same stat, order matters if we chain.
                            # Better: Sum modifiers then apply?
                            # Current logic: Iterative multiplication.
                            # e.g. -20% -> * 0.8. Two -20% -> 0.8 * 0.8 = 0.64 (-36%)
                            # This is acceptable for RPG mechanics.
                            new_val = max(0, int(base_val * (1.0 + mod)))
                            eff_monster[stat] = new_val

                    # Special Rogue Debuff: Accuracy
                    if "accuracy_percent" in debuff:
                        acc_mod = float(debuff["accuracy_percent"])
                        # Additive to base accuracy (0.0 means 100% base)
                        eff_monster["accuracy_percent"] = eff_monster.get("accuracy_percent", 0.0) + acc_mod

        return eff_monster

    def _check_and_consume_crit_buff(self) -> bool:
        """
        Checks if 'next_hit_crit' buff is active.
        If so, consumes it (marks for deletion) and returns True.
        """
        found_buff = None
        for buff in self.active_buffs:
            if buff.get("stat") == "next_hit_crit":
                found_buff = buff
                break

        if found_buff:
            self.consumed_buff_ids.append(found_buff.get("buff_id"))
            # We don't remove from self.active_buffs immediately to avoid mutation during iteration in other places,
            # but for logic consistency, we should treat it as gone for this turn if checked again.
            # However, logic usually checks once per attack.
            return True
        return False

    def run_combat_turn(self):
        """
        Runs ONE turn of combat.
        Returns a full dictionary with the results.
        """
        log = []
        log.append(f"\n--- {E.COMBAT} Turn ---")

        self._handle_start_of_turn(log)

        turn_report = {
            "str_hits": 0,
            "dex_hits": 0,
            "mag_hits": 0,
            "player_crit": 0,
            "player_dodge": 0,
            "damage_taken": 0,
            "skills_used": 0,
            "skill_key_used": None,
            "hits_taken": 0,
        }

        logger.debug(f"Combat Turn Start: Player {self.player_hp} HP, Monster {self.monster_hp} HP")

        try:
            player_defending = False
            monster_stunned = False
            bonus_crit = False

            # --- 0. CHECK FOR COUNTERS ---
            monster_stunned, bonus_crit, player_defending = self._check_interrupt_mechanic(log)

            # --- 1. PLAYER'S TURN ---
            if self.player_stunned:
                log.append("💫 **Stunned!** You cannot move!")
                monster_defeated = False
                # Reset stun for next turn (or decrement if we had duration)
                self.player_stunned = False
                # We need to signal this back to caller if state persists,
                # but currently engine returns result dict.
                # We'll add 'player_stunned' to result dict.
            else:
                monster_defeated, player_defending = self._process_player_turn(
                    log, turn_report, bonus_crit, player_defending
                )

            # Check if player skill stunned the monster
            if self.monster.pop("is_stunned", False):
                monster_stunned = True

            if monster_defeated:
                logger.info("Combat End: Monster defeated.")
                return self._player_victory(log, turn_report)

            # --- 2. MONSTER'S TURN ---
            player_defeated = self._process_monster_turn(log, turn_report, player_defending, monster_stunned)

            if player_defeated:
                logger.info("Combat End: Player defeated.")
                return self._monster_victory(log, turn_report)

            return {
                "winner": None,
                "phrases": log,
                "hp_current": self.player_hp,
                "mp_current": self.player_mp,
                "monster_hp": self.monster_hp,
                "turn_report": turn_report,
                "active_boosts": self.active_boosts_dict,
                "new_buffs": self.new_buffs,
                "new_titles": self.new_titles,
                "player_stunned": self.player_stunned,
                "consumed_buff_ids": self.consumed_buff_ids,
            }

        except Exception as e:
            logger.error(f"Combat Engine Error: {e}", exc_info=True)
            # Fail gracefully to avoid stuck combat state
            return {
                "winner": None,
                "phrases": ["*The combat is interrupted by a strange force.*"],
                "hp_current": self.player_hp,
                "mp_current": self.player_mp,
                "monster_hp": self.monster_hp,
                "turn_report": turn_report,
                "active_boosts": self.active_boosts_dict,
                "new_buffs": self.new_buffs,
                "new_titles": self.new_titles,
            }

    def _handle_start_of_turn(self, log: list):
        """Processes start-of-turn effects (buffs, debuffs, weather)."""
        # Weather Events
        player_max_hp = self.stats_dict.get("HP", 100)
        monster_max_hp = self.monster.get("max_hp", 100)
        monster_name = self.monster.get("name", "Enemy")
        self.player_hp, self.monster_hp = combat_weather.handle_weather_events(
            self.weather,
            self.player_hp,
            self.monster_hp,
            player_max_hp,
            monster_max_hp,
            monster_name,
            log,
        )

        # Process Buffs
        buff_msgs = MonsterAI.handle_buffs(self.monster)
        if buff_msgs:
            log.extend(buff_msgs)

        # Process Debuffs
        debuff_msgs = self._process_monster_debuffs()
        if debuff_msgs:
            log.extend(debuff_msgs)

    # ------------------------------------------------------------------
    # Backward-compatible shims (tests call these as instance methods)
    # ------------------------------------------------------------------

    def _handle_weather_events(self, log: list):
        """Shim: delegates to the combat_weather module."""
        player_max_hp = self.stats_dict.get("HP", 100)
        monster_max_hp = self.monster.get("max_hp", 100)
        monster_name = self.monster.get("name", "Enemy")
        self.player_hp, self.monster_hp = combat_weather.handle_weather_events(
            self.weather,
            self.player_hp,
            self.monster_hp,
            player_max_hp,
            monster_max_hp,
            monster_name,
            log,
        )

    def _detect_element(self, skill: dict) -> str:
        """Shim: delegates to combat_weather.detect_element."""
        return combat_weather.detect_element(skill)

    def _apply_weather_modifiers(self, dmg: int, element: str) -> int:
        """Shim: delegates to combat_weather.apply_weather_modifiers."""
        return combat_weather.apply_weather_modifiers(dmg, element, self.weather)

    def _process_player_turn(self, log, turn_report, bonus_crit, player_defending) -> tuple[bool, bool]:
        """
        Executes player action logic.
        Returns (monster_defeated, updated_player_defending).
        """
        if self.action == "defend":
            player_defending = True
            # Regenerate 5% MP
            max_mp = self.stats_dict.get("MP", 100)
            regen = int(max_mp * 0.05)
            self.player_mp = min(max_mp, self.player_mp + regen)
            log.append(f"🛡️ **Defensive Stance:** You brace yourself, recovering {regen} MP!")

        elif self.action == "flee_failed":
            log.append("You stumble, leaving yourself open to attack!")

        elif self.action == "special_ability":
            self._resolve_special_ability(log, turn_report, force_crit=bonus_crit)

        elif self.action.startswith("skill:"):
            skill_key = self.action.split(":", 1)[1]
            use_skill = next(
                (s for s in self.player_skills if s.get("key_id") == skill_key),
                None,
            )

            if not use_skill:
                log.append(f"⚠️ **Skill Failed:** You try to use a skill you don't know ({skill_key}).")
                self._perform_basic_attack(log, turn_report, force_crit=bonus_crit)
            else:
                mp_cost = use_skill.get("mp_cost", 0)
                if self.player_mp < mp_cost:
                    log.append(
                        f"⚠️ **Not enough MP:** You need {mp_cost} MP to use {use_skill.get('name', 'this skill')}."
                    )
                    self._perform_basic_attack(log, turn_report, force_crit=bonus_crit)
                else:
                    self._execute_player_skill(use_skill, log, turn_report, force_crit=bonus_crit)

        else:
            # Normal Attack / Auto Logic
            use_skill = self._decide_player_skill()["skill"]
            if use_skill:
                self._execute_player_skill(use_skill, log, turn_report, force_crit=bonus_crit)
            else:
                self._perform_basic_attack(log, turn_report, force_crit=bonus_crit)

        return (self.monster_hp <= 0), player_defending

    def _process_monster_turn(self, log, turn_report, player_defending, monster_stunned) -> bool:
        """
        Executes monster AI and action.
        Returns True if player is defeated.
        """
        if monster_stunned:
            log.append(f"💫 The {self.monster.get('name', 'enemy')} is reeling and misses its turn!")
            return False

        effective_monster = self._get_effective_monster_stats()
        action = MonsterAI.choose_action(effective_monster, self.monster_hp, self.monster.get("MP", 0))

        if action["type"] == "attack":
            dmg, crit, event_type = DamageFormula.monster_attack(effective_monster, self.stats_dict)
            dmg = self._apply_incoming_damage(dmg, "physical", player_defending, turn_report, log)
            if event_type != "dodge" and not player_defending:
                log.append(CombatPhrases.monster_attack(self.monster, self.player, dmg, crit))

        elif action["type"] == "skill":
            skill = action["skill"]
            mp_cost = skill.get("mp_cost", 0)
            self.monster["MP"] = max(0, self.monster.get("MP", 0) - mp_cost)

            if skill.get("heal_power", 0) > 0:
                heal, new_hp, _event = DamageFormula.monster_heal(
                    self.monster.get("max_hp", self.monster_hp),
                    self.monster_hp,
                    skill,
                )
                self.monster_hp = new_hp
                log.append(CombatPhrases.monster_heal(self.monster, skill, heal))
            else:
                dmg, crit, event_type = DamageFormula.monster_skill(effective_monster, self.stats_dict, skill)
                element = combat_weather.detect_element(skill)
                dmg = self._apply_incoming_damage(dmg, element, player_defending, turn_report, log)

                if event_type != "dodge" and not player_defending:
                    log.append(CombatPhrases.monster_skill(self.monster, self.player, skill, dmg, crit))

                # Status effects (applied if damage > 0)
                status_effect = skill.get("status_effect")
                if status_effect:
                    stun_chance = status_effect.get("stun_chance", 0)
                    if stun_chance > 0 and random.random() < stun_chance:  # nosec B311
                        if self._is_player_immune("stun"):
                            log.append("🛡️ **Immune!** You shrug off the stun effect!")
                        else:
                            log.append("💫 **Stunned!** You are reeling from the blow!")
                            self.player_stunned = True

        elif action["type"] == "buff":
            buff = action["buff"]
            self.monster["MP"] = max(0, self.monster.get("MP", 0) - buff.get("mp_cost", 0))
            MonsterAI.apply_buff(self.monster, buff)
            log.append(CombatPhrases.monster_buff(self.monster, buff))

        elif action["type"] == "telegraph":
            skill = action["skill"]
            self.monster["charged_skill"] = skill
            log.append(CombatPhrases.telegraph_warning(self.monster, skill))

        elif action["type"] == "execute_charge":
            skill = action["skill"]
            self.monster.pop("charged_skill", None)
            self.monster["MP"] = max(0, self.monster.get("MP", 0) - skill.get("mp_cost", 0))

            dmg, crit, event_type = DamageFormula.monster_skill(effective_monster, self.stats_dict, skill)
            element = combat_weather.detect_element(skill)
            dmg = self._apply_incoming_damage(dmg, element, player_defending, turn_report, log)

            if event_type != "dodge":
                emoji = skill.get("emoji", "🔥")
                attack_msg = f"{emoji} **{self.monster.get('name', 'Enemy')}** unleashes **{skill.get('name')}**!"
                if player_defending:
                    log.append(f"{attack_msg} You brace against it! (`{dmg}` dmg)")
                else:
                    log.append(f"{attack_msg} (`{dmg}` dmg)")

        return self.player_hp <= 0

    def _apply_incoming_damage(
        self,
        dmg: int,
        element: str,
        player_defending: bool,
        turn_report: dict,
        log: list,
    ) -> int:
        """
        Applies monster-damage multipliers (fatigue, weather, stance, defending)
        and records dodge/hit in turn_report. Returns the final damage dealt.
        """
        if self.monster_dmg_mult != 1.0:
            dmg = int(dmg * self.monster_dmg_mult)

        dmg = combat_weather.apply_weather_modifiers(dmg, element, self.weather)

        if self.dmg_taken_mult != 1.0:
            dmg = int(dmg * self.dmg_taken_mult)

        # event_type is already encoded in dmg == 0; re-derive from context:
        # If dmg is 0 at this point it was either a miss or dodge (handled by DamageFormula)
        # We rely on the caller passing dmg=0 for those cases.
        if dmg == 0:
            turn_report["player_dodge"] = 1
            return 0

        turn_report["hits_taken"] = 1
        if player_defending:
            dmg = int(dmg * 0.5)  # 50% damage reduction
            log.append(f"🛡️ Your defense absorbs the impact! ({dmg} dmg)")

        turn_report["damage_taken"] = dmg
        self.player_hp -= dmg
        return dmg

    def _check_interrupt_mechanic(self, log: list) -> tuple[bool, bool, bool]:
        """
        Checks for Counter/Parry opportunities.
        Returns (monster_stunned, bonus_crit, player_defending).
        """
        charged_skill = self.monster.get("charged_skill")
        monster_stunned = False
        bonus_crit = False
        player_defending = False

        if charged_skill:
            skill_type = charged_skill.get("type", "physical")

            # INTERRUPT LOGIC: Magic Charge + Offensive Action
            is_magic = skill_type in [
                "magical",
                "fire",
                "ice",
                "poison",
                "water",
                "wind",
                "earth",
                "dark",
                "holy",
            ]
            is_offensive = (
                self.action in ["attack", "special_ability"]
                or self.action.startswith("skill:")
                or (self.action == "auto")  # Allow auto to trigger randomly? No, safer to assume auto handles attack
            )

            # Refine offensive check: Auto often means attack, but we want to reward choice.
            # If action is 'auto', we'll rely on the random skill decision later, so we check specific actions here.
            if self.action == "auto":
                # In auto mode, we give a small chance to "accidentally" counter
                if is_magic and random.randint(1, 100) <= 20:  # nosec B311
                    is_offensive = True
                else:
                    is_offensive = False  # Assume auto doesn't strategically counter

            if is_magic and is_offensive:
                monster_stunned = True
                bonus_crit = True
                self.monster.pop("charged_skill", None)
                log.append(CombatPhrases.counter_success(self.monster, charged_skill, "interrupt"))
                # Ensure bonus_crit is propagated to result later if immediate action requires it,
                # BUT this method returns bonus_crit to caller.

            # PARRY LOGIC: Physical Charge + Defend Action
            is_physical = not is_magic
            if is_physical and self.action == "defend":
                monster_stunned = True
                player_defending = True  # Still defending
                self.monster.pop("charged_skill", None)

                # Reflect Damage
                reflect_dmg = max(1, int(self.monster.get("ATK", 10) * 1.0))
                self.monster_hp -= reflect_dmg
                log.append(CombatPhrases.counter_success(self.monster, charged_skill, "parry"))
                log.append(f"⚔️ **Reflected!** You deal `{reflect_dmg}` damage back!")

        return monster_stunned, bonus_crit, player_defending

    def _resolve_special_ability(self, log, turn_report, force_crit=False):
        spec = self._CLASS_SPECIALS.get(self.player_class_id)
        cost = 20

        if not spec or self.player_mp < cost:
            log.append("⚠️ **Focus Broken:** Not enough MP for special ability! You perform a hasty attack instead.")
            self._perform_basic_attack(log, turn_report, force_crit=force_crit)
            return

        if self._check_and_consume_crit_buff():
            force_crit = True

        self.player_mp -= cost
        log.append(f"{spec['emoji']} **{spec['name']}**: {spec['log']}")

        effective_monster = self._get_effective_monster_stats()
        base_dmg, crit, event_type = DamageFormula.player_attack(self.stats_dict, effective_monster)

        if force_crit:
            crit = True
            event_type = "crit"

        dmg = int(base_dmg * spec["damage_mult"])
        element = combat_weather.detect_element(spec)
        dmg = combat_weather.apply_weather_modifiers(dmg, element, self.weather)

        if self.dmg_dealt_mult != 1.0:
            dmg = int(dmg * self.dmg_dealt_mult)

        # Apply crit multiplier if lucky roll OR forced crit (apply once)
        # Note: base_dmg formula may have already produced a natural crit; track that separately.
        is_lucky_crit = bool(spec.get("crit_bonus")) and random.randint(1, 100) <= spec["crit_bonus"]  # nosec B311
        if is_lucky_crit or force_crit:
            dmg = int(dmg * 1.5)
            crit = True
            event_type = "crit"

        if spec.get("heal"):
            heal_amount = spec["heal"] + int(self.player.level * 2)
            max_hp = self.stats_dict.get("HP", self.player.stats.max_hp)
            self.player_hp = min(max_hp, self.player_hp + heal_amount)
            log.append(f"✨ You recover {heal_amount} HP!")

        if event_type == "crit":
            turn_report["player_crit"] = 1

        if spec["type"] == "str":
            turn_report["str_hits"] = 1
        elif spec["type"] == "dex":
            turn_report["dex_hits"] = 1
        elif spec["type"] == "mag":
            turn_report["mag_hits"] = 1

        self.monster_hp -= dmg
        log.append(CombatPhrases.player_attack(self.player, self.monster, dmg, crit, self.player_class_id))

    def _execute_player_skill(self, skill, log, turn_report, force_crit=False):
        mp_cost = skill.get("mp_cost", 0)
        skill_level = skill.get("skill_level", 1)
        skill_key = skill.get("key_id", "")

        self.player_mp = max(0, self.player_mp - mp_cost)
        turn_report["skills_used"] = 1
        turn_report["skill_key_used"] = skill_key

        if skill.get("key_id") == "unstoppable_force":
            self.new_titles.append("Unstoppable")

        damage_dealt = 0
        skill_processed = False

        if skill.get("heal_power", 0) > 0:
            heal, new_hp, _event = DamageFormula.player_heal(self.stats_dict, self.player_hp, skill, skill_level)
            self.player_hp = new_hp
            log.append(CombatPhrases.player_heal(self.player, skill, heal))
            skill_processed = True

        elif skill.get("buff_data"):
            self._apply_skill_buffs(skill)
            log.append(CombatPhrases.player_buff(self.player, skill))
            skill_processed = True

        if not skill_processed:
            effective_monster = self._get_effective_monster_stats()

            if self._check_and_consume_crit_buff():
                force_crit = True

            dmg, crit, event_type = DamageFormula.player_skill(self.stats_dict, effective_monster, skill, skill_level)

            # Conditional multiplier (e.g. Rogue Venomous Strike)
            cond_mult_data = skill.get("conditional_multiplier")
            if cond_mult_data and cond_mult_data.get("condition") == "target_poisoned":
                has_poison = any(d.get("type") == "poison" for d in self.monster.get("debuffs", []))
                if has_poison:
                    dmg = int(dmg * float(cond_mult_data.get("multiplier", 1.0)))
                    log.append("☠️ **Critical Poison Strike!**")

            if force_crit and event_type != "crit":
                crit = True
                event_type = "crit"
                dmg = int(dmg * 1.5)
            elif force_crit:
                crit = True

            element = combat_weather.detect_element(skill)
            dmg = combat_weather.apply_weather_modifiers(dmg, element, self.weather)

            if self.dmg_dealt_mult != 1.0:
                dmg = int(dmg * self.dmg_dealt_mult)

            damage_dealt = dmg

            if event_type == "crit":
                turn_report["player_crit"] = 1

            self._tag_damage_type(skill, turn_report)
            self.monster_hp -= dmg
            log.append(CombatPhrases.player_skill(self.player, self.monster, skill, dmg, crit))

        # Shared mechanics: debuffs, recoil, status effects
        if skill.get("debuff"):
            debuff_msg = self._apply_monster_debuff(skill)
            if debuff_msg:
                log.append(debuff_msg)

        recoil_pct = skill.get("self_damage_percent")
        if recoil_pct:
            if damage_dealt > 0:
                recoil_dmg = max(1, int(damage_dealt * recoil_pct))
            else:
                recoil_dmg = max(1, int(self.stats_dict.get("HP", 100) * recoil_pct))
            self.player_hp = max(0, self.player_hp - recoil_dmg)
            log.append(f"💔 **Recoil!** You take {recoil_dmg} damage from the exertion!")

        status_effect = skill.get("status_effect")
        if status_effect:
            stun_chance = status_effect.get("stun_chance", 0)
            if stun_chance > 0 and random.random() < stun_chance:  # nosec B311
                self.monster["is_stunned"] = True
                log.append(f"💫 **Stunned!** The {self.monster.get('name', 'Enemy')} is reeling!")

    def _is_player_immune(self, status_type: str) -> bool:
        """Checks if the player has immunity to a specific status."""
        for buff in self.active_buffs:
            if buff.get("stat") == f"immunity_{status_type}":
                return True
        # Check new buffs applied this turn
        for buff in self.new_buffs:
            if buff.get("stat") == f"immunity_{status_type}":
                return True
        return False

    def _process_monster_debuffs(self):
        """
        Handles damage over time from debuffs on the monster.
        """
        if "debuffs" not in self.monster or not self.monster["debuffs"]:
            return []

        msgs = []
        active_debuffs = []

        for debuff in self.monster["debuffs"]:
            debuff_type = debuff.get("type")

            # Legacy Support: If type is missing but damage exists, treat as poison
            if not debuff_type and "damage" in debuff:
                debuff_type = "poison"

            name = debuff.get("name", "Debuff")

            if debuff_type == "poison":
                dmg = debuff.get("damage", 0)
                # Apply Damage
                self.monster_hp -= dmg
                msgs.append(f"☠️ **{self.monster.get('name', 'Enemy')}** takes {dmg} {name.lower()} damage!")

            # Decrement Duration
            debuff["duration"] -= 1
            if debuff["duration"] > 0:
                active_debuffs.append(debuff)
            else:
                msgs.append(f"✅ {name} on **{self.monster.get('name', 'Enemy')}** has worn off.")

        self.monster["debuffs"] = active_debuffs
        return msgs

    def _apply_monster_debuff(self, skill):
        """
        Applies a debuff to the monster (e.g., Poison, Stat Down).
        Scales damage based on player stats.
        """
        debuff_data = skill.get("debuff", {})
        if not debuff_data:
            return None

        # Initialize debuffs list if missing
        if "debuffs" not in self.monster:
            self.monster["debuffs"] = []

        # Check for Poison
        if "poison" in debuff_data:
            base_dmg = float(debuff_data["poison"])
            duration = int(debuff_data.get("duration", 3))

            # Scaling: Base + Tiered Bonus (Factor 0.3)
            # Default scaling stat for Rogue is DEX
            scaling_stat = skill.get("scaling_stat", "DEX").upper()
            stat_val = self.stats_dict.get(scaling_stat, 10)

            # Equilibrium Fix: Use Tiered Scaling (0.3) to match direct damage progression.
            # Prevents DoTs from becoming obsolete at high levels due to super-linear stat growth.
            stat_bonus = calculate_tiered_bonus(stat_val, 0.3)
            scaled_dmg = int(base_dmg + stat_bonus)

            # Avoid duplicate stacking (refresh duration instead)
            existing = next((d for d in self.monster["debuffs"] if d["type"] == "poison"), None)
            if existing:
                existing["duration"] = duration
                existing["damage"] = max(existing["damage"], scaled_dmg)  # Keep higher damage
                return f"☠️ **{self.monster.get('name', 'Enemy')}**'s poison is refreshed!"
            else:
                self.monster["debuffs"].append(
                    {
                        "type": "poison",
                        "damage": scaled_dmg,
                        "duration": duration,
                        "name": "Poison",
                    }
                )
                return f"☠️ **{self.monster.get('name', 'Enemy')}** is poisoned for {scaled_dmg} dmg/turn!"

        # Check for Stat Modifiers (ATK_percent, DEF_percent, etc.)
        stat_mods = {}
        for key in ["ATK_percent", "DEF_percent", "AGI_percent", "DEX_percent"]:
            if key in debuff_data:
                stat_mods[key] = debuff_data[key]

        if stat_mods:
            duration = int(debuff_data.get("duration", 3))
            name = skill.get("name", "Debuff")

            # Avoid duplicate stacking of the SAME skill (refresh duration)
            existing = next(
                (d for d in self.monster["debuffs"] if d.get("name") == name and d.get("type") == "stat_mod"), None
            )

            if existing:
                existing["duration"] = duration
                # Update magnitude if new one is stronger? For now, we assume same skill = same magnitude.
                return f"💢 **{self.monster.get('name', 'Enemy')}**'s {name} is refreshed!"
            else:
                new_debuff = {
                    "type": "stat_mod",
                    "duration": duration,
                    "name": name,
                }
                new_debuff.update(stat_mods)
                self.monster["debuffs"].append(new_debuff)
                return f"💢 **{self.monster.get('name', 'Enemy')}** is weakened by {name}!"

        return None

    def _perform_basic_attack(self, log, turn_report, force_crit=False):
        effective_monster = self._get_effective_monster_stats()

        if self._check_and_consume_crit_buff():
            force_crit = True

        dmg, crit, event_type = DamageFormula.player_attack(self.stats_dict, effective_monster)

        if force_crit and event_type != "crit":
            crit = True
            event_type = "crit"
            dmg = int(dmg * 1.5)
        elif force_crit:
            crit = True

        dmg = combat_weather.apply_weather_modifiers(dmg, "physical", self.weather)

        if self.dmg_dealt_mult != 1.0:
            dmg = int(dmg * self.dmg_dealt_mult)

        if event_type == "crit":
            turn_report["player_crit"] = 1

        # Tag damage type based on class
        if self.player_class_id in [1, 4]:  # Warrior, Cleric -> Str
            turn_report["str_hits"] = 1
        elif self.player_class_id in [3, 5]:  # Rogue, Ranger -> Dex
            turn_report["dex_hits"] = 1
        elif self.player_class_id == 2:  # Mage -> Mag
            turn_report["mag_hits"] = 1
        else:
            turn_report["str_hits"] = 1

        self.monster_hp -= dmg
        log.append(CombatPhrases.player_attack(self.player, self.monster, dmg, crit, self.player_class_id))

    def _apply_skill_buffs(self, skill):
        """
        Calculates and records buffs from a skill.
        Converts % bonuses to flat values based on current stats.
        """
        buff_data = skill.get("buff_data", {})
        if not buff_data:
            return

        duration = int(buff_data.get("duration", 3))

        def add_buff(stat, amount):
            self.new_buffs.append(
                {
                    "name": skill.get("name", "Unknown Buff"),
                    "stat": stat,
                    "amount": int(amount),
                    "duration": duration,
                }
            )

        for key, val in buff_data.items():
            if key == "duration":
                continue

            if key == "all_stats_percent":
                # Apply to all primary stats
                for stat_code in ["STR", "END", "DEX", "AGI", "MAG", "LCK"]:
                    # Equilibrium Fix: Use base stats for % calculation to prevent compounding
                    current_val = self.base_stats_dict.get(stat_code, 10)
                    bonus = current_val * float(val)
                    if bonus > 0:
                        add_buff(stat_code, bonus)

            elif key.endswith("_percent"):
                # e.g., "END_percent": 0.25 -> +25% END
                stat_code = key.replace("_percent", "").upper()
                # Equilibrium Fix: Use base stats for % calculation to prevent compounding
                current_val = self.base_stats_dict.get(stat_code, 10)
                bonus = current_val * float(val)
                if bonus > 0:
                    add_buff(stat_code, bonus)

            elif key == "status_immunity":
                # Handle Status Immunity List (e.g. ["stun", "slow"])
                # Creates individual buffs like immunity_stun, immunity_slow
                for status in val:
                    add_buff(f"immunity_{status}", 1)

    def _tag_damage_type(self, skill, report):
        """Helper to categorize skill damage for stat growth."""
        stat = skill.get("scaling_stat", "STR").upper()
        hit_key = self._STAT_HIT_MAP.get(stat, "str_hits")
        report[hit_key] = 1

    def _decide_player_skill(self) -> dict:
        """
        Player AI logic.
        Returns a dict: {"skill": (skill_dict or None), "reason": str}
        """
        if not self.player_skills:
            return {"skill": None, "reason": "No skills available."}

        roll = random.randint(1, 100)  # nosec B311  # nosec B311
        if roll > self.PLAYER_SKILL_CHANCE:
            return {"skill": None, "reason": "RNG check failed."}

        usable_skills = [s for s in self.player_skills if s.get("mp_cost", 0) <= self.player_mp]

        if not usable_skills:
            return {"skill": None, "reason": "Not enough MP."}

        # Priority 1: Healing (if below 50% HP)
        hp_threshold = self.stats_dict.get("HP", self.player.stats.max_hp) * 0.5
        if self.player_hp < hp_threshold:
            heal_skill = next((s for s in usable_skills if s.get("heal_power", 0) > 0), None)
            if heal_skill:
                return {"skill": heal_skill, "reason": "HP Critical."}

        # Priority 2: Buffs (50% chance if available)
        utility_skills = [s for s in usable_skills if s.get("buff_data")]
        if utility_skills and random.randint(1, 100) > 50:  # nosec B311
            chosen_skill = random.choice(utility_skills)  # nosec B311
            return {"skill": chosen_skill, "reason": "Buff chosen."}

        # Priority 3: Offensive Skills
        offensive_skills = [s for s in usable_skills if s.get("heal_power", 0) == 0 and not s.get("buff_data")]
        if offensive_skills:
            chosen_skill = random.choice(offensive_skills)  # nosec B311  # nosec B311
            return {"skill": chosen_skill, "reason": "Offense chosen."}

        return {"skill": None, "reason": "No offensive skills usable."}

    def _player_victory(self, log, turn_report):
        """Handles rewarding EXP and passing up monster drops."""
        exp = ExpCalculator.calculate_exp(self.player.level, self.monster, self.exp_boost)

        # Calculate Aurum
        monster_lvl = self.monster.get("level", 1)
        monster_tier = self.monster.get("tier", "Normal")
        luck = self.stats_dict.get("LCK", 0)
        aurum = AurumCalculator.calculate_drop(monster_lvl, monster_tier, luck)

        drops = self.monster.get("drops", [])
        leveled_up = self.player.add_exp(exp)

        # Passive Mechanics: Kill Heal (Bloodlust)
        for skill in self.player_skills:
            if skill.get("type") == "Passive" and "passive_bonus" in skill:
                bonuses = skill["passive_bonus"]
                if "kill_heal_percent" in bonuses:
                    heal_pct = bonuses["kill_heal_percent"]
                    max_hp = self.stats_dict.get("HP", self.player.stats.max_hp)
                    heal_amt = int(max_hp * heal_pct)
                    self.player_hp = min(max_hp, self.player_hp + heal_amt)
                    log.append(f"🩸 **Bloodlust:** You recover {heal_amt} HP from the kill!")

        log.append(CombatPhrases.player_victory(self.monster, exp, aurum, leveled_up, self.player.level))

        return {
            "winner": "player",
            "phrases": log,
            "hp_current": self.player_hp,
            "mp_current": self.player_mp,
            "monster_hp": 0,
            "exp": exp,
            "aurum": aurum,
            "drops": drops,
            "monster_data": self.monster,
            "turn_report": turn_report,
            "active_boosts": self.active_boosts_dict,
            "new_buffs": self.new_buffs,
            "new_titles": self.new_titles,
        }

    def _monster_victory(self, log, turn_report):
        """Handles death phrase."""
        log.append(CombatPhrases.player_defeated(self.monster))

        return {
            "winner": "monster",
            "phrases": log,
            "hp_current": 0,
            "mp_current": self.player_mp,
            "monster_hp": self.monster_hp,
            "turn_report": turn_report,
            "active_boosts": self.active_boosts_dict,
        }
