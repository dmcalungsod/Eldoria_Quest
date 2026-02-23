"""
damage_formula.py

Handles damage calculations for combat.
Rebalanced: Lower minimum damage floor, better crit reward.
"""

import random

from game_systems.player.player_stats import calculate_tiered_bonus


class DamageFormula:
    STAT_PROPERTY_MAP = {
        "STR": "strength",
        "END": "endurance",
        "DEX": "dexterity",
        "AGI": "agility",
        "MAG": "magic",
        "LCK": "luck",
    }

    @staticmethod
    def _get_stat(stats_obj, stat_code):
        if isinstance(stats_obj, dict):
            return stats_obj.get(stat_code, 0)

        property_name = DamageFormula.STAT_PROPERTY_MAP.get(stat_code)
        if property_name:
            return getattr(stats_obj, property_name, 0)
        return 0

    @staticmethod
    def player_attack(player_stats, monster):
        str_val = DamageFormula._get_stat(player_stats, "STR")
        dex_val = DamageFormula._get_stat(player_stats, "DEX")
        mag_val = DamageFormula._get_stat(player_stats, "MAG")
        luck_val = DamageFormula._get_stat(player_stats, "LCK")

        # --- REBALANCED BASIC ATTACK ---
        # Adaptive Offense: Uses the highest stat to determine damage scaling.
        # This allows DEX and MAG classes to have viable basic attacks without
        # relying solely on MP or being forced to build STR.

        # 1. Identify Primary Stat
        stats = {"STR": str_val, "DEX": dex_val, "MAG": mag_val}
        primary_stat = max(stats, key=stats.get)
        primary_val = stats[primary_stat]

        # 2. Calculate Primary Bonus
        # STR/DEX get 2.0x (Physical weapons are impactful)
        # MAG gets 1.5x (Magic bolts are weaker than steel but consistent)
        if primary_stat == "MAG":
            primary_mult = 1.5
        else:
            primary_mult = 2.0

        primary_bonus = calculate_tiered_bonus(primary_val, primary_mult)

        # 3. Calculate Secondary Bonus (0.5x for other stats)
        secondary_bonus = 0
        for stat, val in stats.items():
            if stat != primary_stat:
                secondary_bonus += calculate_tiered_bonus(val, 0.5)

        attack_power = primary_bonus + secondary_bonus

        # Defense
        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))

        base_damage = max(1, attack_power - defense_reduction)

        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # Crit (Buffed slightly to 1.75x)
        crit_chance = 0.03 + (luck_val * 0.002)
        is_crit = random.random() < crit_chance

        event_type = "hit"
        if is_crit:
            damage = int(damage * 1.75)
            event_type = "crit"

        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_skill(player_stats, monster, skill_data, skill_level: int):
        # Data-driven scaling
        scaling_stat = skill_data.get("scaling_stat", "MAG").upper()
        scaling_factor = float(skill_data.get("scaling_factor", 1.0))

        base_stat_value = DamageFormula._get_stat(player_stats, scaling_stat)
        attack_power = calculate_tiered_bonus(base_stat_value, scaling_factor)

        base_multiplier = float(skill_data.get("power_multiplier", 1.0))
        final_multiplier = base_multiplier + (0.08 * (skill_level - 1))
        attack_power *= final_multiplier

        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))

        base_damage = max(1, attack_power - defense_reduction)

        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        luck_val = DamageFormula._get_stat(player_stats, "LCK")
        crit_chance = 0.03 + (luck_val * 0.002)
        is_crit = random.random() < crit_chance

        event_type = "hit"
        if is_crit:
            damage = int(damage * 1.75)
            event_type = "crit"

        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_heal(player_stats, current_hp: int, skill_data: dict, skill_level: int) -> tuple[int, int, str]:
        base_heal = float(skill_data.get("heal_power", 0))

        # Use scaling stat if available (default MAG)
        scaling_stat = skill_data.get("scaling_stat", "MAG")
        scaling_factor = float(skill_data.get("scaling_factor", 1.5))
        stat_val = DamageFormula._get_stat(player_stats, scaling_stat)

        if isinstance(player_stats, dict) and "HP" in player_stats:
            max_hp = player_stats["HP"]
        elif hasattr(player_stats, "max_hp"):
            max_hp = player_stats.max_hp
        else:
            # Replicate PlayerStats logic properly
            end_val = DamageFormula._get_stat(player_stats, "END")
            max_hp = 50 + calculate_tiered_bonus(end_val, 10.0)

        stat_bonus = calculate_tiered_bonus(stat_val, scaling_factor)
        level_multiplier = 1.0 + (0.15 * (skill_level - 1))
        final_base_heal = base_heal * level_multiplier

        total_heal = final_base_heal + stat_bonus
        max_allowed = max_hp * 0.6
        total_heal = min(total_heal, max_allowed)

        variance = random.uniform(0.9, 1.1)
        heal_amount = int(total_heal * variance)
        new_hp = min(current_hp + heal_amount, max_hp)
        actual_healed = new_hp - current_hp

        return actual_healed, new_hp, "heal"

    @staticmethod
    def monster_attack(monster, player_stats):
        """
        Calculates monster damage.
        Reduced Chip Damage to 5%.
        """
        agi = DamageFormula._get_stat(player_stats, "AGI")
        dodge_chance = agi * 0.001
        if random.random() < dodge_chance:
            return 0, False, "dodge"

        attack_power = monster.get("ATK", 10)
        end = DamageFormula._get_stat(player_stats, "END")
        flat_def = DamageFormula._get_stat(player_stats, "DEF")

        defense = calculate_tiered_bonus(end, 1.5) + flat_def
        defense_reduction = defense * (0.3 + (0.2 * min(1, defense / 100)))

        base_damage = max(0, attack_power - defense_reduction)

        # --- REBALANCED DEFENSE PENETRATION ---
        # 5% minimum damage instead of 10%
        min_damage = max(attack_power * 0.05, 1)

        final_damage = max(base_damage, min_damage)

        variance = random.uniform(0.9, 1.1)
        damage = int(final_damage * variance)

        is_crit = random.random() < 0.05
        event_type = "hit"

        if is_crit:
            damage = int(damage * 1.5)
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

    @staticmethod
    def monster_heal(monster_max_hp: int, current_hp: int, skill_data: dict) -> tuple[int, int, str]:
        """
        Calculates monster healing.
        """
        heal_amount = float(skill_data.get("heal_power", 0))

        # Variance
        variance = random.uniform(0.9, 1.1)
        heal_amount = int(heal_amount * variance)

        new_hp = min(current_hp + heal_amount, monster_max_hp)
        actual_healed = int(new_hp - current_hp)

        return actual_healed, int(new_hp), "heal"
