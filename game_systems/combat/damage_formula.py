"""
damage_formula.py

Handles damage calculations for combat.
Exposes a static class 'DamageFormula' used by CombatEngine.
"""

import random
import math
from typing import Tuple  # <-- THIS IS THE FIX


class DamageFormula:
    @staticmethod
    def player_attack(player_stats, monster):
        """
        Calculates damage dealt by the player to a monster.
        Returns: (damage_dealt: int, is_critical: bool)
        """
        if hasattr(player_stats, "strength"):
            str_val = player_stats.strength
            dex_val = player_stats.dexterity
            luck_val = player_stats.luck
        else:
            str_val = player_stats.get("STR", 0)
            dex_val = player_stats.get("DEX", 0)
            luck_val = player_stats.get("LCK", 0)

        attack_power = (str_val * 2) + dex_val
        monster_def = monster.get("DEF", 0)

        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        crit_chance = 0.05 + (luck_val * 0.005)
        is_crit = random.random() < crit_chance

        if is_crit:
            damage = int(damage * 1.5)

        return max(1, damage), is_crit

    @staticmethod
    def player_skill(player_stats, monster, skill_data):
        """
        Calculates damage dealt by a player's skill.
        Now routes to different stats based on skill key.
        Returns: (damage_dealt: int, is_critical: bool)
        """
        skill_key = skill_data.get("key_id", "")

        # --- STAT-BASED DAMAGE ROUTING ---
        if skill_key in ["fireball", "explosion"]:
            # Magic-based
            base_stat = player_stats.magic
            stat_multiplier = 3.0
        elif skill_key == "power_strike":
            # Strength-based
            base_stat = player_stats.strength
            stat_multiplier = 2.5  # Slightly better than basic attack
        elif skill_key == "true_shot":
            # Dexterity-based
            base_stat = player_stats.dexterity
            stat_multiplier = 2.8  # Strong single shot
        else:
            # Default fallback
            base_stat = player_stats.magic
            stat_multiplier = 1.0

        luck_val = player_stats.luck

        attack_power = base_stat * stat_multiplier
        attack_power *= skill_data.get("power_multiplier", 1.0)

        monster_def = monster.get("DEF", 0)
        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        crit_chance = 0.05 + (luck_val * 0.005)
        is_crit = random.random() < crit_chance

        if is_crit:
            damage = int(damage * 1.5)

        return max(1, damage), is_crit

    # --- NEW METHOD ---
    @staticmethod
    def player_heal(player_stats, current_hp: int, skill_data: dict) -> Tuple[int, int]:
        """
        Calculates healing from a player's skill.
        Returns: (amount_healed: int, new_hp: int)
        """
        base_heal = skill_data.get("heal_power", 0)
        mag_val = player_stats.magic
        max_hp = player_stats.max_hp

        # Formula: Base Heal + (Magic * 2)
        total_heal = base_heal + (mag_val * 2)
        variance = random.uniform(0.9, 1.1)
        heal_amount = int(total_heal * variance)

        new_hp = min(current_hp + heal_amount, max_hp)
        actual_healed = new_hp - current_hp

        return actual_healed, new_hp

    @staticmethod
    def monster_attack(monster, player_stats):
        """
        Calculates damage dealt by a monster to the player.
        """
        attack_power = monster.get("ATK", 10)
        defense = player_stats.endurance * 1.5

        base_damage = max(1, attack_power - (defense / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        is_crit = random.random() < 0.05
        if is_crit:
            damage = int(damage * 1.5)

        return max(1, damage), is_crit

    @staticmethod
    def monster_skill(monster, player_stats, skill_data):
        """
        Calculates damage for a monster's special skill.
        """
        damage, is_crit = DamageFormula.monster_attack(monster, player_stats)
        multiplier = skill_data.get("power", 1.5)
        damage = int(damage * multiplier)

        return damage, is_crit
