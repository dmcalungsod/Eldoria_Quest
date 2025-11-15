"""
Combat Engine for Eldoria Quest

Refactored to handle a single turn of auto-combat, including
player auto-skill usage.
"""

import random
from .damage_formula import DamageFormula
from ..rewards.exp_calculator import ExpCalculator
from ..monsters.monster_actions import MonsterAI
from .combat_phrases import CombatPhrases
import game_systems.data.emojis as E


class CombatEngine:

    # --- Player AI Settings ---
    PLAYER_SKILL_CHANCE = 40  # 40% chance to use a skill if possible

    def __init__(self, player, monster: dict, player_skills: list, player_mp: int):
        """
        player → LevelUpSystem wrapper (with stats + current HP)
        monster → DICT containing monster's CURRENT state (including current HP)
        player_skills → List of dicts of skills from DB
        player_mp → Player's current MP
        """
        self.player = player
        self.monster = monster
        self.player_skills = player_skills

        # Cache vitals
        self.player_hp = player.hp_current
        self.player_mp = player_mp
        self.monster_hp = monster.get("HP", 1)

    # ------------------------------------------------------------
    # MAIN COMBAT TURN
    # ------------------------------------------------------------
    def run_combat_turn(self):
        """
        Runs ONE turn of combat (Player -> Monster).
        Returns a full dictionary with the results.
        """
        log = []
        log.append(f"\n--- {E.COMBAT} Turn ---")

        # --- 1. PLAYER'S TURN ---

        # Decide action: Skill or Attack?
        use_skill = self._decide_player_skill()

        if use_skill:
            # --- Player uses a Skill ---
            skill = use_skill  # Get the skill data
            mp_cost = skill.get("mp_cost", 0)
            self.player_mp -= mp_cost

            if skill.get("heal_power", 0) > 0:
                # --- It's a HEAL skill ---
                heal, new_hp = DamageFormula.player_heal(
                    self.player.stats, self.player_hp, skill
                )
                self.player_hp = new_hp
                log.append(CombatPhrases.player_heal(self.player, skill, heal))
            else:
                # --- It's an ATTACK skill ---
                dmg, crit = DamageFormula.player_skill(
                    self.player.stats, self.monster, skill
                )
                self.monster_hp -= dmg
                log.append(
                    CombatPhrases.player_skill(
                        self.player, self.monster, skill, dmg, crit
                    )
                )

        else:
            # --- Player uses a Basic Attack ---
            dmg, crit = DamageFormula.player_attack(self.player.stats, self.monster)
            self.monster_hp -= dmg
            log.append(
                CombatPhrases.player_attack(self.player, self.monster, dmg, crit)
            )

        # --- Check for Player Victory ---
        if self.monster_hp <= 0:
            return self._player_victory(log)

        # --- 2. MONSTER'S TURN ---
        action = MonsterAI.choose_action(
            self.monster, self.monster_hp, self.monster.get("MP", 0)
        )

        if action["type"] == "attack":
            dmg, crit = DamageFormula.monster_attack(self.monster, self.player.stats)
            self.player_hp -= dmg
            log.append(
                CombatPhrases.monster_attack(self.monster, self.player, dmg, crit)
            )

        elif action["type"] == "skill":
            skill = action["skill"]
            # (Monster MP logic would go here if we tracked it)
            dmg, crit = DamageFormula.monster_skill(
                self.monster, self.player.stats, skill
            )
            self.player_hp -= dmg
            log.append(
                CombatPhrases.monster_skill(self.monster, self.player, skill, dmg, crit)
            )

        elif action["type"] == "buff":
            buff = action["buff"]
            MonsterAI.apply_buff(self.monster, buff)
            log.append(CombatPhrases.monster_buff(self.monster, buff))

        # --- Check for Monster Victory ---
        if self.player_hp <= 0:
            return self._monster_victory(log)

        # --- 3. Turn End: No winner yet ---
        return {
            "winner": None,
            "phrases": log,
            "hp_current": self.player_hp,
            "mp_current": self.player_mp,
            "monster_hp": self.monster_hp,
        }

    def _decide_player_skill(self) -> dict | None:
        """
        Player AI logic.
        Decides if the player should use a skill.
        Returns the skill dictionary if yes, None if no.
        """
        # 1. Check if we should even try
        if not self.player_skills or random.randint(1, 100) > self.PLAYER_SKILL_CHANCE:
            return None

        # 2. Find a skill we can afford
        usable_skills = [
            s for s in self.player_skills if s.get("mp_cost", 0) <= self.player_mp
        ]

        # --- Special Case: Cleric Heal Logic ---
        # If HP is low, prioritize healing
        if self.player_hp < (self.player.stats.max_hp * 0.5):
            heal_skill = next(
                (s for s in usable_skills if s.get("heal_power", 0) > 0), None
            )
            if heal_skill:
                return heal_skill  # Use heal!

        # 3. Use a random offensive skill
        offensive_skills = [s for s in usable_skills if s.get("heal_power", 0) == 0]
        if offensive_skills:
            return random.choice(offensive_skills)

        # 4. Can't afford any skills or have no offensive ones
        return None

    # ------------------------------------------------------------
    # RESULT HANDLERS
    # ------------------------------------------------------------
    def _player_victory(self, log):
        """Handles rewarding EXP and passing up monster drops."""
        exp = ExpCalculator.calculate_exp(self.player.level, self.monster)
        drops = self.monster.get("drops", [])
        leveled_up = self.player.add_exp(
            exp
        )  # This just updates the wrapper for the log

        log.append(CombatPhrases.player_victory(self.monster, exp, 0, leveled_up))

        return {
            "winner": "player",
            "phrases": log,
            "hp_current": self.player_hp,
            "mp_current": self.player_mp,
            "monster_hp": 0,
            "exp": exp,
            "drops": drops,
            "monster_data": self.monster,  # Pass back the original template
        }

    def _monster_victory(self, log):
        """Handles death phrase."""
        log.append(CombatPhrases.player_defeated(self.monster))

        return {
            "winner": "monster",
            "phrases": log,
            "hp_current": 0,
            "mp_current": self.player_mp,
            "monster_hp": self.monster_hp,
        }
