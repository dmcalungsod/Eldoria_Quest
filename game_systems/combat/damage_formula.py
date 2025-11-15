"""
damage_formula.py

Handles damage calculations for combat.
Exposes a static class 'DamageFormula' used by CombatEngine.
"""

import random
import math


class DamageFormula:
    @staticmethod
    def player_attack(player_stats, monster):
        """
        Calculates damage dealt by the player to a monster.
        Returns: (damage_dealt: int, is_critical: bool)
        """
        # 1. Calculate Player Attack Power
        # Formula: (STR * 2) + DEX
        # Check if stats is a PlayerStats object or a dictionary
        if hasattr(player_stats, "strength"):
            str_val = player_stats.strength
            dex_val = player_stats.dexterity
            luck_val = player_stats.luck
        else:
            # Fallback for dictionary access
            str_val = player_stats.get("STR", 0)
            dex_val = player_stats.get("DEX", 0)
            luck_val = player_stats.get("LCK", 0)

        attack_power = (str_val * 2) + dex_val

        # 2. Calculate Monster Defense
        monster_def = monster.get("DEF", 0)

        # 3. Damage Calculation
        # Damage = (Atk - Def/2) * Random Variance
        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # 4. Critical Hit Check (Base 5% + Luck mod)
        crit_chance = 0.05 + (luck_val * 0.005)
        is_crit = random.random() < crit_chance

        if is_crit:
            damage = int(damage * 1.5)

        return max(1, damage), is_crit

    @staticmethod
    def monster_attack(monster, player_stats):
        """
        Calculates damage dealt by a monster to the player.
        Returns: (damage_dealt: int, is_critical: bool)
        """
        # 1. Monster Attack
        attack_power = monster.get("ATK", 10)

        # 2. Player Defense
        # Formula: (END * 1.5)
        if hasattr(player_stats, "endurance"):
            end_val = player_stats.endurance
        else:
            end_val = player_stats.get("END", 0)

        defense = end_val * 1.5

        # 3. Damage Calculation
        base_damage = max(1, attack_power - (defense / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # 4. Crit (Monsters have fixed 5% chance usually)
        is_crit = random.random() < 0.05
        if is_crit:
            damage = int(damage * 1.5)

        return max(1, damage), is_crit

    @staticmethod
    def monster_skill(monster, player_stats, skill_data):
        """
        Calculates damage for a monster's special skill.
        """
        # Calculate normal attack first
        damage, is_crit = DamageFormula.monster_attack(monster, player_stats)

        # Apply skill multiplier
        multiplier = skill_data.get("power", 1.5)
        damage = int(damage * multiplier)

        return damage, is_crit
