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

    # ------------------------------------------------------------------
    # Private shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_stat(stats_obj, stat_code):
        if isinstance(stats_obj, dict):
            return stats_obj.get(stat_code, 0)

        property_name = DamageFormula.STAT_PROPERTY_MAP.get(stat_code)
        if property_name:
            return getattr(stats_obj, property_name, 0)
        return 0

    @staticmethod
    def _apply_crit(damage: int, crit_chance: float, crit_mult: float = 1.75) -> tuple[int, bool, str]:
        """Rolls for a critical hit. Returns (damage, is_crit, event_type)."""
        is_crit = random.random() < crit_chance  # nosec B311
        if is_crit:
            return int(damage * crit_mult), True, "crit"
        return damage, False, "hit"

    @staticmethod
    def _check_dodge(agi: int) -> bool:
        """Returns True if the attack is dodged based on player agility."""
        return random.random() < (agi * 0.001)  # nosec B311

    # ------------------------------------------------------------------
    # Public calculation methods
    # ------------------------------------------------------------------

    @staticmethod
    def player_attack(player_stats, monster):
        str_val = DamageFormula._get_stat(player_stats, "STR")
        dex_val = DamageFormula._get_stat(player_stats, "DEX")
        mag_val = DamageFormula._get_stat(player_stats, "MAG")
        luck_val = DamageFormula._get_stat(player_stats, "LCK")

        # Attack
        str_bonus = calculate_tiered_bonus(str_val, 2.0)
        dex_bonus = calculate_tiered_bonus(dex_val, 1.0)
        mag_bonus = calculate_tiered_bonus(mag_val, 0.5)
        attack_power = str_bonus + dex_bonus + mag_bonus

        # Defense
        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))
        base_damage = max(1, attack_power - defense_reduction)

        variance = random.uniform(0.9, 1.1)  # nosec B311
        damage = int(base_damage * variance)

        # Crit (1.75x)
        crit_chance = 0.03 + (luck_val * 0.002)
        damage, is_crit, event_type = DamageFormula._apply_crit(damage, crit_chance)
        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_skill(player_stats, monster, skill_data, skill_level: int):
        # Data-driven scaling
        scaling_stat = skill_data.get("scaling_stat", "MAG").upper()
        scaling_factor = float(skill_data.get("scaling_factor", 1.0))

        base_stat_value = DamageFormula._get_stat(player_stats, scaling_stat)
        attack_power = calculate_tiered_bonus(base_stat_value, scaling_factor)

        # Secondary stat scaling: add 0.5x from other core offensive stats
        # (prevents skills falling behind normal attacks that sum all 3 stats)
        for stat in ["STR", "DEX", "MAG"]:
            if stat != scaling_stat:
                val = DamageFormula._get_stat(player_stats, stat)
                attack_power += calculate_tiered_bonus(val, 0.5)

        base_multiplier = float(skill_data.get("power_multiplier", 1.0))
        final_multiplier = base_multiplier + (0.08 * (skill_level - 1))
        attack_power *= final_multiplier

        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))
        base_damage = max(1, attack_power - defense_reduction)

        variance = random.uniform(0.9, 1.1)  # nosec B311
        damage = int(base_damage * variance)

        luck_val = DamageFormula._get_stat(player_stats, "LCK")
        crit_chance = 0.03 + (luck_val * 0.002)
        damage, is_crit, event_type = DamageFormula._apply_crit(damage, crit_chance)
        return max(1, damage), is_crit, event_type

    @staticmethod
    def player_heal(player_stats, current_hp: int, skill_data: dict, skill_level: int) -> tuple[int, int, str]:
        base_heal = float(skill_data.get("heal_power", 0))

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
        total_heal = min(base_heal * level_multiplier + stat_bonus, max_hp * 0.6)

        variance = random.uniform(0.9, 1.1)  # nosec B311
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
        # Accuracy Check (Blind/Debuff Support)
        accuracy_percent = monster.get("accuracy_percent", 0.0)
        if random.random() > (1.0 + accuracy_percent):  # nosec B311
            return 0, False, "miss"

        agi = DamageFormula._get_stat(player_stats, "AGI")
        if DamageFormula._check_dodge(agi):
            return 0, False, "dodge"

        attack_power = monster.get("ATK", 10)
        end = DamageFormula._get_stat(player_stats, "END")
        flat_def = DamageFormula._get_stat(player_stats, "DEF")

        defense = calculate_tiered_bonus(end, 1.5) + flat_def
        defense_reduction = defense * (0.3 + (0.2 * min(1, defense / 100)))
        base_damage = max(0, attack_power - defense_reduction)

        # 5% minimum chip damage
        final_damage = max(base_damage, max(attack_power * 0.05, 1))

        variance = random.uniform(0.9, 1.1)  # nosec B311
        damage = int(final_damage * variance)

        damage, is_crit, event_type = DamageFormula._apply_crit(damage, 0.05, crit_mult=1.5)
        return max(1, damage), is_crit, event_type

    @staticmethod
    def monster_skill(monster, player_stats, skill_data):
        """Calculates monster skill damage."""
        agi = DamageFormula._get_stat(player_stats, "AGI")
        if DamageFormula._check_dodge(agi):
            return 0, False, "dodge"

        # Base calculation uses standard attack logic, then apply skill multiplier
        damage, is_crit, event_type = DamageFormula.monster_attack(monster, player_stats)
        multiplier = float(skill_data.get("power", 1.5))
        return int(damage * multiplier), is_crit, event_type

    @staticmethod
    def monster_heal(monster_max_hp: int, current_hp: int, skill_data: dict) -> tuple[int, int, str]:
        """Calculates monster healing."""
        heal_amount = int(float(skill_data.get("heal_power", 0)) * random.uniform(0.9, 1.1))  # nosec B311
        new_hp = min(current_hp + heal_amount, monster_max_hp)
        return int(new_hp - current_hp), int(new_hp), "heal"
