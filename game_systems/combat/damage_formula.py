"""
damage_formula.py

Handles damage calculations for combat.
Exposes a static class 'DamageFormula' used by CombatEngine.
"""

import random
import math
from typing import Tuple

# --- IMPORT THE NEW HELPER ---
from game_systems.player.player_stats import calculate_tiered_bonus


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

        # --- MODIFIED ATTACK POWER CALCULATION ---
        # Old Formula: attack_power = (str_val * 2) + dex_val
        str_bonus = calculate_tiered_bonus(str_val, 2)  # 2 Attack per STR
        dex_bonus = calculate_tiered_bonus(dex_val, 1)  # 1 Attack per DEX
        attack_power = str_bonus + dex_bonus
        # --- END OF MODIFICATION ---

        monster_def = monster.get("DEF", 0)

        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # Crit formula is unchanged as per your request
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

        # --- MODIFIED STAT-BASED DAMAGE ROUTING ---
        if skill_key in ["fireball", "explosion"]:
            # Magic-based
            base_stat_value = player_stats.magic
            base_effect_per_point = 3.0
        elif skill_key == "power_strike":
            # Strength-based
            base_stat_value = player_stats.strength
            base_effect_per_point = 2.5
        elif skill_key == "true_shot":
            # Dexterity-based
            base_stat_value = player_stats.dexterity
            base_effect_per_point = 2.8
        else:
            # Default fallback
            base_stat_value = player_stats.magic
            base_effect_per_point = 1.0

        # Old Formula: attack_power = base_stat * stat_multiplier
        attack_power = calculate_tiered_bonus(base_stat_value, base_effect_per_point)
        # --- END OF MODIFICATION ---

        luck_val = player_stats.luck
        attack_power *= skill_data.get("power_multiplier", 1.0)

        monster_def = monster.get("DEF", 0)
        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # Crit formula is unchanged
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

        # --- MODIFIED HEAL CALCULATION ---
        # Old Formula: total_heal = base_heal + (mag_val * 2)
        magic_bonus = calculate_tiered_bonus(mag_val, 2)  # 2 Heal per MAG
        total_heal = base_heal + magic_bonus
        # --- END OF MODIFICATION ---

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

        # AGI/Dodge formula is unchanged as per your request
        dodge_chance = player_stats.agility * 0.001
        if random.random() < dodge_chance:
            return 0, False  # 0 damage, not a crit (DODGED)

        attack_power = monster.get("ATK", 10)

        # --- MODIFIED DEFENSE CALCULATION ---
        # Old Formula: defense = player_stats.endurance * 1.5
        defense = calculate_tiered_bonus(player_stats.endurance, 1.5)  # 1.5 Def per END
        # --- END OF MODIFICATION ---

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

        # AGI/Dodge formula is unchanged as per your request
        dodge_chance = player_stats.agility * 0.001
        if random.random() < dodge_chance:
            return 0, False  # 0 damage, not a crit (DODGED)

        # This correctly uses the new tiered defense
        # by calling the modified monster_attack
        damage, is_crit = DamageFormula.monster_attack(monster, player_stats)
        multiplier = skill_data.get("power", 1.5)
        damage = int(damage * multiplier)

        return damage, is_crit
