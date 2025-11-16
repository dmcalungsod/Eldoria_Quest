"""
Combat Engine for Eldoria Quest

Refactored to handle a single turn of auto-combat, including
player auto-skill usage.
"""

import random
import logging
from .damage_formula import DamageFormula
from ..rewards.exp_calculator import ExpCalculator
from ..monsters.monster_actions import MonsterAI
from .combat_phrases import CombatPhrases
import game_systems.data.emojis as E

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
    ):
        """
        player → LevelUpSystem wrapper (with stats + current HP)
        monster → DICT containing monster's CURRENT state (including current HP)
        player_skills → List of dicts of skills from DB (INCLUDES skill_level)
        player_mp → Player's current MP
        player_class_id -> The player's class ID (1=War, 2=Mage, etc.)
        """
        self.player = player
        self.monster = monster
        self.player_skills = player_skills
        self.player_class_id = player_class_id

        self.player_hp = player.hp_current
        self.player_mp = player_mp
        self.monster_hp = monster.get("HP", 1)

    def run_combat_turn(self):
        """
        Runs ONE turn of combat (Player -> Monster).
        Returns a full dictionary with the results.
        """
        log = []
        log.append(f"\n--- {E.COMBAT} Turn ---")
        
        # --- THIS IS THE FIX: More specific counters ---
        turn_report = {
            "str_hits": 0,         # For STR exp
            "dex_hits": 0,         # For DEX exp
            "mag_hits": 0,         # For MAG exp
            "player_crit": 0,      # For DEX exp (bonus)
            "player_dodge": 0,     # For AGI exp
            "damage_taken": 0,     # For END exp
            "skills_used": 0,      # (Retained for LCK or other logic)
        }
        # --- END OF FIX ---

        logger.info(
            f"Combat Turn Start: Player Vitals: {self.player_hp} HP, {self.player_mp} MP"
        )
        logger.info(f"Combat Turn Start: Monster HP: {self.monster_hp}")

        # --- 1. PLAYER'S TURN ---
        skill_decision = self._decide_player_skill()
        use_skill = skill_decision["skill"]
        logger.info(f"Combat Player AI: {skill_decision['reason']}")

        if use_skill:
            skill = use_skill
            mp_cost = skill.get("mp_cost", 0)
            skill_level = skill.get("skill_level", 1)
            self.player_mp -= mp_cost
            turn_report["skills_used"] = 1
            
            if skill.get("heal_power", 0) > 0:
                # --- Healing Skill ---
                heal, new_hp, event_type = DamageFormula.player_heal(
                    self.player.stats, self.player_hp, skill, skill_level
                )
                logger.info(
                    f"Combat Player Heal: {skill['name']} | Base: {skill.get('heal_power', 0)} | Total: {heal}"
                )
                self.player_hp = new_hp
                log.append(CombatPhrases.player_heal(self.player, skill, heal))
                
            elif skill.get("buff_data"):
                # --- Buff/Utility Skill ---
                log.append(CombatPhrases.player_buff(self.player, skill))
                logger.info(f"Combat Player Buff: {skill['name']} applied buff/utility.")
                
            else:
                # --- Offensive Skill ---
                dmg, crit, event_type = DamageFormula.player_skill(
                    self.player.stats, self.monster, skill, skill_level
                )
                
                # --- THIS IS THE FIX (per user suggestion) ---
                skill_key = skill.get("key_id", "")
                
                # Crits are counted as a bonus
                if event_type == "crit":
                    turn_report["player_crit"] = 1
                
                # Grant base stat EXP regardless of crit
                if skill_key in ["fireball", "explosion", "ice_lance", "smite"]:
                    turn_report["mag_hits"] = 1
                elif skill_key in ["true_shot", "multi_shot", "double_strike", "toxic_blade"]:
                    turn_report["dex_hits"] = 1
                elif skill_key in ["power_strike", "cleave"]:
                    turn_report["str_hits"] = 1
                # --- END OF FIX ---
                
                logger.info(
                    f"Combat Player Skill: {skill['name']} | Dmg: {dmg} | Crit: {crit}"
                )
                self.monster_hp -= dmg
                log.append(
                    CombatPhrases.player_skill(
                        self.player, self.monster, skill, dmg, crit
                    )
                )
        else:
            # --- Basic Attack ---
            dmg, crit, event_type = DamageFormula.player_attack(self.player.stats, self.monster)
            
            # --- THIS IS THE FIX (per user suggestion) ---
            # Grant crit as a bonus, not a replacement
            if event_type == "crit":
                turn_report["player_crit"] = 1
            
            # Grant class-appropriate base stat EXP regardless of crit
            if self.player_class_id in [1, 4]: # Warrior, Cleric
                turn_report["str_hits"] = 1
            elif self.player_class_id in [3, 5]: # Rogue, Ranger
                turn_report["dex_hits"] = 1
            elif self.player_class_id == 2: # Mage
                turn_report["mag_hits"] = 1
            else: # Fallback
                turn_report["str_hits"] = 1
            # --- END OF FIX ---
            
            logger.info(f"Combat Player Atk: Basic | Dmg: {dmg} | Crit: {crit}")
            self.monster_hp -= dmg

            log.append(
                CombatPhrases.player_attack(
                    self.player, self.monster, dmg, crit, self.player_class_id
                )
            )

        if self.monster_hp <= 0:
            logger.info(f"Combat End: Monster HP {self.monster_hp} <= 0. Player wins.")
            return self._player_victory(log, turn_report)

        # --- 2. MONSTER'S TURN ---
        action = MonsterAI.choose_action(
            self.monster, self.monster_hp, self.monster.get("MP", 0)
        )
        logger.info(f"Combat Monster AI: Selected {action['type']}")

        if action["type"] == "attack":
            dmg, crit, event_type = DamageFormula.monster_attack(self.monster, self.player.stats)
            
            if event_type == "dodge":
                turn_report["player_dodge"] = 1
            else:
                turn_report["damage_taken"] = dmg

            logger.info(f"Combat Monster Atk: Basic | Dmg: {dmg} | Crit: {crit}")
            self.player_hp -= dmg
            log.append(
                CombatPhrases.monster_attack(self.monster, self.player, dmg, crit)
            )
        elif action["type"] == "skill":
            skill = action["skill"]
            dmg, crit, event_type = DamageFormula.monster_skill(
                self.monster, self.player.stats, skill
            )

            if event_type == "dodge":
                turn_report["player_dodge"] = 1
            else:
                turn_report["damage_taken"] = dmg
            
            logger.info(
                f"Combat Monster Skill: {skill['name']} | Dmg: {dmg} | Crit: {crit}"
            )
            self.player_hp -= dmg
            log.append(
                CombatPhrases.monster_skill(self.monster, self.player, skill, dmg, crit)
            )
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

        usable_skills = [
            s for s in self.player_skills if s.get("mp_cost", 0) <= self.player_mp
        ]

        if not usable_skills:
            return {"skill": None, "reason": "Not enough MP for any skill."}

        # Priority 1: Healing (if below 50% HP)
        hp_threshold = self.player.stats.max_hp * 0.5
        if self.player_hp < hp_threshold:
            heal_skill = next(
                (s for s in usable_skills if s.get("heal_power", 0) > 0), None
            )
            if heal_skill:
                return {
                    "skill": heal_skill,
                    "reason": f"HP < {hp_threshold}, using Heal.",
                }
        
        # Priority 2: Buffs (simple check: if Mana Shield or Endure is available)
        utility_skills = [s for s in usable_skills if s.get("buff_data")]
        if utility_skills and random.randint(1, 100) > 50: # 50% chance to use buff if one is available
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
        exp = ExpCalculator.calculate_exp(self.player.level, self.monster)
        drops = self.monster.get("drops", [])
        leveled_up = self.player.add_exp(exp)

        logger.info(f"Combat Player Victory. EXP: {exp} | Leveled Up: {leveled_up}")
        
        # --- THIS IS THE FIX ---
        # We now pass the new level to the phrasing function
        log.append(CombatPhrases.player_victory(self.monster, exp, 0, leveled_up, self.player.level))
        # --- END OF FIX ---

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
        }