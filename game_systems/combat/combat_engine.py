"""
Combat Engine for Eldoria Quest

This module orchestrates combat between a Player and a Monster.

Relies on:
- damage_formula.py        → Handles physical/magical damage, crits, defense, reductions
- exp_calculator.py        → Calculates EXP rewards
- gold_rewards.py          → Determines gold drops
- monster_actions.py       → AI: monster attack patterns & behaviors
- combat_phrases.py        → Beautiful, book-like combat narration

The engine governs:
- Turn order
- Executing attacks
- Applying damage
- Checking victory/defeat
- Returning combat results
"""

from .damage_formula import DamageFormula
from ..rewards.exp_calculator import ExpCalculator
from ..rewards.gold_rewards import GoldRewards
from ..monsters.monster_actions import MonsterAI
from .combat_phrases import CombatPhrases


class CombatEngine:
    def __init__(self, player, monster):
        """
        player → LevelUpSystem or similar wrapper (with stats + HP/MP)
        monster → Dict containing monster stats
        """
        self.player = player
        self.monster = monster

        # Cache monster stats
        self.mon_hp = monster["HP"]
        self.mon_mp = monster["MP"]

    # ------------------------------------------------------------
    # MAIN COMBAT LOOP
    # ------------------------------------------------------------
    def begin_combat(self):
        """
        Runs combat automatically until someone dies.
        Returns a dictionary with:
        {
            "winner": "player" or "monster",
            "exp": int,
            "gold": int,
            "phrases": list of battle narration
        }
        """
        log = []
        log.append(CombatPhrases.opening(self.monster))

        turn = 1
        while self.player.stats.hp_current > 0 and self.mon_hp > 0:

            log.append(f"\n--- Turn {turn} ---")

            # ---------------------------
            # PLAYER ATTACK
            # ---------------------------
            dmg, crit = DamageFormula.player_attack(self.player.stats, self.monster)
            self.mon_hp -= dmg

            log.append(CombatPhrases.player_attack(self.player, self.monster, dmg, crit))

            if self.mon_hp <= 0:
                return self._player_victory(log)

            # ---------------------------
            # MONSTER ATTACK
            # ---------------------------
            action = MonsterAI.choose_action(self.monster, self.mon_hp, self.mon_mp)

            if action["type"] == "attack":
                dmg, crit = DamageFormula.monster_attack(self.monster, self.player.stats)
                self.player.stats.hp_current -= dmg

                log.append(CombatPhrases.monster_attack(self.monster, self.player, dmg, crit))

            elif action["type"] == "skill":
                skill = action["skill"]
                dmg, crit = DamageFormula.monster_skill(self.monster, self.player.stats, skill)
                self.player.stats.hp_current -= dmg
                self.mon_mp -= skill["mp_cost"]

                log.append(CombatPhrases.monster_skill(self.monster, self.player, skill, dmg, crit))

            elif action["type"] == "buff":
                buff = action["buff"]
                MonsterAI.apply_buff(self.monster, buff)

                log.append(CombatPhrases.monster_buff(self.monster, buff))

            # Check if player died
            if self.player.stats.hp_current <= 0:
                return self._monster_victory(log)

            turn += 1

        # Fallback (should not happen)
        return {"winner": "unknown", "exp": 0, "gold": 0, "phrases": log}

    # ------------------------------------------------------------
    # RESULT HANDLERS
    # ------------------------------------------------------------
    def _player_victory(self, log):
        """Handles rewarding EXP and gold."""
        exp = ExpCalculator.calculate_exp(self.player.level, self.monster)
        gold = GoldRewards.generate(self.monster)

        # Apply EXP
        leveled_up = self.player.add_exp(exp)

        log.append(CombatPhrases.player_victory(self.monster, exp, gold, leveled_up))

        return {
            "winner": "player",
            "exp": exp,
            "gold": gold,
            "phrases": log,
        }

    def _monster_victory(self, log):
        """Handles death phrase."""
        log.append(CombatPhrases.player_defeated(self.monster))

        return {
            "winner": "monster",
            "exp": 0,
            "gold": 0,
            "phrases": log,
        }
