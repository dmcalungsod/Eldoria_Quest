"""
damage_formula.py

Handles damage calculations for combat.
Hardened: Safe type checking, negative damage prevention, and robust math.
"""

import random
import math
from game_systems.player.player_stats import calculate_tiered_bonus


class DamageFormula:
    @staticmethod
    def _get_stat(stats_obj, stat_name):
        """Helper to get stat value whether input is dict or Object."""
        if isinstance(stats_obj, dict):
            return stats_obj.get(stat_name, 0)
        # Assuming object has lower_case property
        return getattr(stats_obj, stat_name.lower(), 0)

    @staticmethod
    def player_attack(player_stats, monster):
        """
        Calculates damage dealt by the player to a monster.
        Returns: (damage_dealt: int, is_critical: bool, event_type: str)
        """
        str_val = DamageFormula._get_stat(player_stats, "STR")
        dex_val = DamageFormula._get_stat(player_stats, "DEX")
        mag_val = DamageFormula._get_stat(player_stats, "MAG")
        luck_val = DamageFormula._get_stat(player_stats, "LCK")

        # --- ATTACK POWER ---
        str_bonus = calculate_tiered_bonus(str_val, 2)
        dex_bonus = calculate_tiered_bonus(dex_val, 1)
        mag_bonus = calculate_tiered_bonus(mag_val, 0.5)
        
        attack_power = str_bonus + dex_bonus + mag_bonus

        # --- DEFENSE ---
        monster_def = monster.get("DEF", 0)
        # Diminishing returns on defense
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))
        
        base_damage = max(1, attack_power - defense_reduction)

        # --- VARIANCE ---
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # --- CRIT ---
        crit_chance = 0.03 + (luck_val * 0.003)
        is_crit = random.random() < crit_chance

        event_type = "hit"
        if is_crit:
            damage = int(damage * 2.0)
            event_type = "crit"

        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_skill(player_stats, monster, skill_data, skill_level: int):
        """
        Calculates damage dealt by a player's skill.
        Routes to different stats based on skill key.
        """
        skill_key = skill_data.get("key_id", "")

        # Stat Routing
        # Uses _get_stat helper for safety
        if skill_key in ["fireball", "explosion", "ice_lance", "smite"]:
            base_stat_value = DamageFormula._get_stat(player_stats, "MAG")
            base_effect_per_point = 2.8
        elif skill_key in ["power_strike", "cleave"]:
            base_stat_value = DamageFormula._get_stat(player_stats, "STR")
            base_effect_per_point = 2.7
        elif skill_key in ["true_shot", "multi_shot", "double_strike", "toxic_blade"]:
            base_stat_value = DamageFormula._get_stat(player_stats, "DEX")
            base_effect_per_point = 2.6
        else:
            base_stat_value = DamageFormula._get_stat(player_stats, "MAG")
            base_effect_per_point = 1.0

        attack_power = calculate_tiered_bonus(base_stat_value, base_effect_per_point)

        # Scaling
        base_multiplier = float(skill_data.get("power_multiplier", 1.0))
        final_multiplier = base_multiplier + (0.08 * (skill_level - 1))
        attack_power *= final_multiplier

        # Defense
        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))
        
        base_damage = max(1, attack_power - defense_reduction)

        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # Crit
        luck_val = DamageFormula._get_stat(player_stats, "LCK")
        crit_chance = 0.03 + (luck_val * 0.003)
        is_crit = random.random() < crit_chance

        event_type = "hit"
        if is_crit:
            damage = int(damage * 2.0)
            event_type = "crit"

        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_heal(player_stats, current_hp: int, skill_data: dict, skill_level: int) -> tuple[int, int, str]:
        """
        Calculates healing.
        Returns: (amount_healed, new_hp, event_type)
        """
        base_heal = float(skill_data.get("heal_power", 0))
        mag_val = DamageFormula._get_stat(player_stats, "MAG")
        
        # Access max_hp safely depending on object type
        if isinstance(player_stats, dict):
            # Fallback estimation if simple dict
            end_val = player_stats.get("END", 1)
            max_hp = 50 + (end_val * 10) 
        else:
            max_hp = player_stats.max_hp

        magic_bonus = calculate_tiered_bonus(mag_val, 1.5)
        
        level_multiplier = 1.0 + (0.15 * (skill_level - 1))
        final_base_heal = base_heal * level_multiplier

        total_heal = final_base_heal + magic_bonus

        # Cap at 50% HP per heal
        max_allowed = max_hp * 0.5
        total_heal = min(total_heal, max_allowed)

        variance = random.uniform(0.9, 1.1)
        heal_amount = int(total_heal * variance)

        new_hp = min(current_hp + heal_amount, max_hp)
        actual_healed = new_hp - current_hp

        return actual_healed, new_hp, "heal"

    @staticmethod
    def monster_attack(monster, player_stats):
        """
        Calculates monster damage against player.
        """
        # Dodge check
        agi = DamageFormula._get_stat(player_stats, "AGI")
        dodge_chance = agi * 0.001
        if random.random() < dodge_chance:
            return 0, False, "dodge"

        attack_power = monster.get("ATK", 10)

        # Defense calc
        end = DamageFormula._get_stat(player_stats, "END")
        defense = calculate_tiered_bonus(end, 1.5)
        defense_reduction = defense * (0.3 + (0.2 * min(1, defense / 100)))

        base_damage = max(1, attack_power - defense_reduction)
        
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        is_crit = random.random() < 0.04
        event_type = "hit"

        if is_crit:
            damage = int(damage * 2.0)
            event_type = "crit"

        return max(1, damage), is_crit, event_type

    @staticmethod
    def monster_skill(monster, player_stats, skill_data):
        """
        Calculates monster skill damage.
        """
        # Dodge check
        agi = DamageFormula._get_stat(player_stats, "AGI")
        dodge_chance = agi * 0.001
        if random.random() < dodge_chance:
            return 0, False, "dodge"

        # Base calculation uses standard attack logic
        damage, is_crit, event_type = DamageFormula.monster_attack(monster, player_stats)

        # Apply Skill Multiplier
        multiplier = float(skill_data.get("power", 1.5))
        damage = int(damage * multiplier)

        return damage, is_crit, event_type