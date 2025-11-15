"""
Combat Engine for Eldoria Quest

Orchestrates combat and returns a result dictionary.
(Refactored for material-based economy)
"""

from .damage_formula import DamageFormula
from ..rewards.exp_calculator import ExpCalculator

# GoldRewards import is REMOVED
from ..monsters.monster_actions import MonsterAI
from .combat_phrases import CombatPhrases


class CombatEngine:
    def __init__(self, player, monster):
        """
        player → LevelUpSystem wrapper (with stats + HP)
        monster → Dict containing monster stats
        """
        self.player = player
        self.monster = monster

        # Cache monster stats from template
        self.mon_hp = monster.get("HP", 1)
        self.mon_mp = monster.get("MP", 0)

        # Cache player's current HP from their stats object
        # We need a way to track HP during combat
        if not hasattr(self.player, "hp_current"):
            self.player.hp_current = self.player.stats.max_hp

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
            "drops": list,  <-- NEW
            "phrases": list
        }
        """
        log = []
        log.append(CombatPhrases.opening(self.monster))

        turn = 1
        while self.player.hp_current > 0 and self.mon_hp > 0:

            log.append(f"\n--- Turn {turn} ---")

            # ---------------------------
            # PLAYER ATTACK
            # ---------------------------
            dmg, crit = DamageFormula.player_attack(self.player.stats, self.monster)
            self.mon_hp -= dmg
            log.append(
                CombatPhrases.player_attack(self.player, self.monster, dmg, crit)
            )

            if self.mon_hp <= 0:
                return self._player_victory(log)

            # ---------------------------
            # MONSTER ATTACK
            # ---------------------------
            action = MonsterAI.choose_action(self.monster, self.mon_hp, self.mon_mp)

            if action["type"] == "attack":
                dmg, crit = DamageFormula.monster_attack(
                    self.monster, self.player.stats
                )
                self.player.hp_current -= dmg
                log.append(
                    CombatPhrases.monster_attack(self.monster, self.player, dmg, crit)
                )

            elif action["type"] == "skill":
                skill = action["skill"]
                # Check MP
                if self.mon_mp >= skill.get("mp_cost", 0):
                    self.mon_mp -= skill.get("mp_cost", 0)
                    dmg, crit = DamageFormula.monster_skill(
                        self.monster, self.player.stats, skill
                    )
                    self.player.hp_current -= dmg
                    log.append(
                        CombatPhrases.monster_skill(
                            self.monster, self.player, skill, dmg, crit
                        )
                    )
                else:
                    # Not enough MP, default to normal attack
                    dmg, crit = DamageFormula.monster_attack(
                        self.monster, self.player.stats
                    )
                    self.player.hp_current -= dmg
                    log.append(
                        CombatPhrases.monster_attack(
                            self.monster, self.player, dmg, crit
                        )
                    )

            elif action["type"] == "buff":
                buff = action["buff"]
                MonsterAI.apply_buff(self.monster, buff)
                log.append(CombatPhrases.monster_buff(self.monster, buff))

            # Check if player died
            if self.player.hp_current <= 0:
                return self._monster_victory(log)

            turn += 1

        # Fallback (should not happen)
        return {"winner": "unknown", "exp": 0, "drops": [], "phrases": log}

    # ------------------------------------------------------------
    # RESULT HANDLERS
    # ------------------------------------------------------------
    def _player_victory(self, log):
        """Handles rewarding EXP and passing up monster drops."""
        exp = ExpCalculator.calculate_exp(self.player.level, self.monster)

        # Gold is NO LONGER calculated here.
        # We just get the monster's drop list.
        drops = self.monster.get("drops", [])

        # Apply EXP to the player wrapper
        leveled_up = self.player.add_exp(exp)

        # We pass gold=0 because the phrase no longer uses it
        log.append(CombatPhrases.player_victory(self.monster, exp, 0, leveled_up))

        return {
            "winner": "player",
            "exp": exp,
            "drops": drops,  # Pass the raw drops list
            "phrases": log,
        }

    def _monster_victory(self, log):
        """Handles death phrase."""
        log.append(CombatPhrases.player_defeated(self.monster))

        return {
            "winner": "monster",
            "exp": 0,
            "drops": [],
            "phrases": log,
        }
