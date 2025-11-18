"""
Combat Engine for Eldoria Quest

Refactored to handle a single turn of auto-combat, including
player auto-skill usage.
"""

import logging
import random

import game_systems.data.emojis as E

from ..monsters.monster_actions import MonsterAI
from ..rewards.exp_calculator import ExpCalculator
from .combat_phrases import CombatPhrases
from .damage_formula import DamageFormula

logger = logging.getLogger("discord")


class CombatEngine:
    PLAYER_SKILL_CHANCE = 40  # 40% chance to use a skill if possible

    def __init__(
        self,
        player,
        monster: dict,
        player_skills: list,
        player_mp: int,
        player_class_id: int,
        active_boosts: dict = None,  # <-- Receives a DICT now
    ):
        """
        player → LevelUpSystem wrapper (with stats + current HP)
        monster → DICT containing monster's CURRENT state (including current HP)
        player_skills → List of dicts of skills from DB (INCLUDES skill_level)
        player_mp → Player's current MP
        player_class_id -> The player's class ID (1=War, 2=Mage, etc.)
        active_boosts → Dict of active global boosts, e.g., {"exp_boost": 2.0}
        """
        self.player = player
        self.monster = monster
        self.player_skills = player_skills
        self.player_class_id = player_class_id

        self.player_hp = player.hp_current
        self.player_mp = player_mp
        self.monster_hp = monster.get("HP", 1)

        # --- THIS IS THE FIX ---
        # Store the raw dict
        self.active_boosts_dict = active_boosts or {}

        # Process the dict into simple multipliers
        self.exp_boost = self.active_boosts_dict.get("exp_boost", 1.0)
        self.loot_boost = self.active_boosts_dict.get("loot_boost", 1.0)
        # --- END OF FIX ---

    def run_combat_turn(self):
        """
        Runs ONE turn of combat (Player -> Monster).
        Returns a full dictionary with the results.
        """
        log = []
        log.append(f"\n--- {E.COMBAT} Turn ---")

        turn_report = {
            "str_hits": 0,
            "dex_hits": 0,
            "mag_hits": 0,
            "player_crit": 0,
            "player_dodge": 0,
            "damage_taken": 0,
            "skills_used": 0,
            "skill_key_used": None,
        }

        logger.info(f"Combat Turn Start: Player Vitals: {self.player_hp} HP, {self.player_mp} MP")
        logger.info(f"Combat Turn Start: Monster HP: {self.monster_hp}")

        # --- 1. PLAYER'S TURN ---
        skill_decision = self._decide_player_skill()
        use_skill = skill_decision["skill"]
        logger.info(f"Combat Player AI: {skill_decision['reason']}")

        if use_skill:
            skill = use_skill
            mp_cost = skill.get("mp_cost", 0)
            skill_level = skill.get("skill_level", 1)
            skill_key = skill.get("key_id", "")

            self.player_mp -= mp_cost
            turn_report["skills_used"] = 1
            turn_report["skill_key_used"] = skill_key

            if skill.get("heal_power", 0) > 0:
                # --- Healing Skill ---
                heal, new_hp, event_type = DamageFormula.player_heal(
                    self.player.stats, self.player_hp, skill, skill_level
                )
                self.player_hp = new_hp
                log.append(CombatPhrases.player_heal(self.player, skill, heal))

            elif skill.get("buff_data"):
                # --- Buff/Utility Skill ---
                log.append(CombatPhrases.player_buff(self.player, skill))

            else:
                # --- Offensive Skill ---
                dmg, crit, event_type = DamageFormula.player_skill(self.player.stats, self.monster, skill, skill_level)

                if event_type == "crit":
                    turn_report["player_crit"] = 1

                if skill_key in ["fireball", "explosion", "ice_lance", "smite"]:
                    turn_report["mag_hits"] = 1
                elif skill_key in ["true_shot", "multi_shot", "double_strike", "toxic_blade"]:
                    turn_report["dex_hits"] = 1
                elif skill_key in ["power_strike", "cleave"]:
                    turn_report["str_hits"] = 1

                self.monster_hp -= dmg
                log.append(CombatPhrases.player_skill(self.player, self.monster, skill, dmg, crit))
        else:
            # --- Basic Attack ---
            dmg, crit, event_type = DamageFormula.player_attack(self.player.stats, self.monster)

            if event_type == "crit":
                turn_report["player_crit"] = 1

            if self.player_class_id in [1, 4]:
                turn_report["str_hits"] = 1
            elif self.player_class_id in [3, 5]:
                turn_report["dex_hits"] = 1
            elif self.player_class_id == 2:
                turn_report["mag_hits"] = 1
            else:
                turn_report["str_hits"] = 1

            self.monster_hp -= dmg
            log.append(CombatPhrases.player_attack(self.player, self.monster, dmg, crit, self.player_class_id))

        if self.monster_hp <= 0:
            logger.info(f"Combat End: Monster HP {self.monster_hp} <= 0. Player wins.")
            return self._player_victory(log, turn_report)

        # --- 2. MONSTER'S TURN ---
        action = MonsterAI.choose_action(self.monster, self.monster_hp, self.monster.get("MP", 0))
        logger.info(f"Combat Monster AI: Selected {action['type']}")

        if action["type"] == "attack":
            dmg, crit, event_type = DamageFormula.monster_attack(self.monster, self.player.stats)

            if event_type == "dodge":
                turn_report["player_dodge"] = 1
            else:
                turn_report["damage_taken"] = dmg

            self.player_hp -= dmg
            log.append(CombatPhrases.monster_attack(self.monster, self.player, dmg, crit))
        elif action["type"] == "skill":
            skill = action["skill"]
            dmg, crit, event_type = DamageFormula.monster_skill(self.monster, self.player.stats, skill)

            if event_type == "dodge":
                turn_report["player_dodge"] = 1
            else:
                turn_report["damage_taken"] = dmg

            self.player_hp -= dmg
            log.append(CombatPhrases.monster_skill(self.monster, self.player, skill, dmg, crit))
        elif action["type"] == "buff":
            buff = action["buff"]
            MonsterAI.apply_buff(self.monster, buff)
            log.append(CombatPhrases.monster_buff(self.monster, buff))

        if self.player_hp <= 0:
            logger.info(f"Combat End: Player HP {self.player_hp} <= 0. Monster wins.")
            return self._monster_victory(log, turn_report)

        logger.info("Combat Turn End: No winner.")
        return {
            "winner": None,
            "phrases": log,
            "hp_current": self.player_hp,
            "mp_current": self.player_mp,
            "monster_hp": self.monster_hp,
            "turn_report": turn_report,
            "active_boosts": self.active_boosts_dict,  # <-- Pass the dict back
        }

    def _decide_player_skill(self) -> dict:
        """
        Player AI logic.
        Returns a dict: {"skill": (skill_dict or None), "reason": str}
        """
        if not self.player_skills:
            return {"skill": None, "reason": "No skills available."}

        roll = random.randint(1, 100)
        if roll > self.PLAYER_SKILL_CHANCE:
            return {
                "skill": None,
                "reason": f"Roll {roll} > {self.PLAYER_SKILL_CHANCE}.",
            }

        usable_skills = [s for s in self.player_skills if s.get("mp_cost", 0) <= self.player_mp]

        if not usable_skills:
            return {"skill": None, "reason": "Not enough MP for any skill."}

        # Priority 1: Healing (if below 50% HP)
        hp_threshold = self.player.stats.max_hp * 0.5
        if self.player_hp < hp_threshold:
            heal_skill = next((s for s in usable_skills if s.get("heal_power", 0) > 0), None)
            if heal_skill:
                return {
                    "skill": heal_skill,
                    "reason": f"HP < {hp_threshold}, using Heal.",
                }

        # Priority 2: Buffs (simple check: if Mana Shield or Endure is available)
        utility_skills = [s for s in usable_skills if s.get("buff_data")]
        if utility_skills and random.randint(1, 100) > 50:  # 50% chance to use buff if one is available
            chosen_skill = random.choice(utility_skills)
            return {
                "skill": chosen_skill,
                "reason": f"Rolled {roll}, prioritizing utility skill `{chosen_skill['name']}`.",
            }

        # Priority 3: Offensive Skills
        offensive_skills = [s for s in usable_skills if s.get("heal_power", 0) == 0 and not s.get("buff_data")]
        if offensive_skills:
            chosen_skill = random.choice(offensive_skills)
            return {
                "skill": chosen_skill,
                "reason": f"Rolled {roll}, chose offensive skill `{chosen_skill['name']}`.",
            }

        return {"skill": None, "reason": "No offensive skills usable or affordable."}

    def _player_victory(self, log, turn_report):
        """Handles rewarding EXP and passing up monster drops."""

        exp = ExpCalculator.calculate_exp(self.player.level, self.monster, self.exp_boost)
        drops = self.monster.get("drops", [])
        leveled_up = self.player.add_exp(exp)

        logger.info(f"Combat Player Victory. EXP: {exp} | Leveled Up: {leveled_up}")

        log.append(CombatPhrases.player_victory(self.monster, exp, 0, leveled_up, self.player.level))

        return {
            "winner": "player",
            "phrases": log,
            "hp_current": self.player_hp,
            "mp_current": self.player_mp,
            "monster_hp": 0,
            "exp": exp,
            "drops": drops,
            "monster_data": self.monster,
            "turn_report": turn_report,
            "active_boosts": self.active_boosts_dict,  # <-- Pass the dict back
        }

    def _monster_victory(self, log, turn_report):
        """Handles death phrase."""
        logger.info("Combat Monster Victory.")
        log.append(CombatPhrases.player_defeated(self.monster))

        return {
            "winner": "monster",
            "phrases": log,
            "hp_current": 0,
            "mp_current": self.player_mp,
            "monster_hp": self.monster_hp,
            "turn_report": turn_report,
            "active_boosts": self.active_boosts_dict,  # <-- Pass the dict back
        }
