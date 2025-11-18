"""
damage_formula.py

Handles damage calculations for combat.
Exposes a static class 'DamageFormula' used by CombatEngine.
"""

import random
from typing import Tuple

# --- IMPORT THE NEW HELPER ---
from game_systems.player.player_stats import calculate_tiered_bonus


class DamageFormula:
    @staticmethod
    def player_attack(player_stats, monster):
        """
        Calculates damage dealt by the player to a monster.
        Returns: (damage_dealt: int, is_critical: bool, event_type: str)
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

        event_type = "hit" # Default event

        if is_crit:
            damage = int(damage * 1.5)
            event_type = "crit" # --- NEW: Set event type

        return max(1, damage), is_crit, event_type

    # --- THIS METHOD IS MODIFIED ---
    @staticmethod
    def player_skill(player_stats, monster, skill_data, skill_level: int):
        """
        Calculates damage dealt by a player's skill.
        Now routes to different stats based on skill key.
        Returns: (damage_dealt: int, is_critical: bool, event_type: str)
        """
        skill_key = skill_data.get("key_id", "")

        # --- MODIFIED STAT-BASED DAMAGE ROUTING ---
        if skill_key in ["fireball", "explosion", "ice_lance", "smite"]:
            # Magic-based
            base_stat_value = player_stats.magic
            base_effect_per_point = 3.0
        elif skill_key == "power_strike" or skill_key == "cleave":
            # Strength-based
            base_stat_value = player_stats.strength
            base_effect_per_point = 2.5
        elif (
            skill_key == "true_shot"
            or skill_key == "multi_shot"
            or skill_key == "double_strike"
            or skill_key == "toxic_blade"
        ):
            # Dexterity-based
            base_stat_value = player_stats.dexterity
            base_effect_per_point = 2.8
        else:
            # Default fallback
            base_stat_value = player_stats.magic
            base_effect_per_point = 1.0

        attack_power = calculate_tiered_bonus(base_stat_value, base_effect_per_point)
        # --- END OF MODIFICATION ---

        luck_val = player_stats.luck

        # --- NEW SKILL LEVEL SCALING ---
        base_multiplier = skill_data.get("power_multiplier", 1.0)
        # Formula: FinalMultiplier = BaseMultiplier + (10% * (SkillLevel - 1))
        final_multiplier = base_multiplier + (0.1 * (skill_level - 1))
        attack_power *= final_multiplier
        # --- END NEW SKILL LEVEL SCALING ---

        monster_def = monster.get("DEF", 0)
        base_damage = max(1, attack_power - (monster_def / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        # Crit formula is unchanged
        crit_chance = 0.05 + (luck_val * 0.005)
        is_crit = random.random() < crit_chance

        event_type = "hit" # Default event

        if is_crit:
            damage = int(damage * 1.5)
            event_type = "crit" # --- NEW: Set event type

        return max(1, damage), is_crit, event_type

    # --- THIS METHOD IS MODIFIED ---
    @staticmethod
    def player_heal(
        player_stats, current_hp: int, skill_data: dict, skill_level: int
    ) -> Tuple[int, int, str]:
        """
        Calculates healing from a player's skill.
        Returns: (amount_healed: int, new_hp: int, event_type: str)
        """
        base_heal = skill_data.get("heal_power", 0)
        mag_val = player_stats.magic
        max_hp = player_stats.max_hp

        # --- MODIFIED HEAL CALCULATION ---
        magic_bonus = calculate_tiered_bonus(mag_val, 2)  # 2 Heal per MAG

        # --- NEW SKILL LEVEL SCALING ---
        # Formula: FinalHeal = BaseHeal * (1 + (20% * (SkillLevel - 1)))
        level_multiplier = 1.0 + (0.2 * (skill_level - 1))
        final_base_heal = base_heal * level_multiplier
        # --- END NEW SKILL LEVEL SCALING ---

        total_heal = final_base_heal + magic_bonus
        # --- END OF MODIFICATION ---

        variance = random.uniform(0.9, 1.1)
        heal_amount = int(total_heal * variance)

        new_hp = min(current_hp + heal_amount, max_hp)
        actual_healed = new_hp - current_hp

        return actual_healed, new_hp, "heal"

    @staticmethod
    def monster_attack(monster, player_stats):
        """
        Calculates damage dealt by a monster to the player.
        Returns: (damage_dealt: int, is_critical: bool, event_type: str)
        """

        # AGI/Dodge formula is unchanged as per your request
        dodge_chance = player_stats.agility * 0.001
        if random.random() < dodge_chance:
            return 0, False, "dodge"  # 0 damage, not a crit (DODGED)

        attack_power = monster.get("ATK", 10)

        # --- MODIFIED DEFENSE CALCULATION ---
        defense = calculate_tiered_bonus(player_stats.endurance, 1.5)  # 1.5 Def per END
        # --- END OF MODIFICATION ---

        base_damage = max(1, attack_power - (defense / 2))
        variance = random.uniform(0.9, 1.1)
        damage = int(base_damage * variance)

        is_crit = random.random() < 0.05
        event_type = "hit" # Default event

        if is_crit:
            damage = int(damage * 1.5)
            event_type = "crit" # --- NEW: Set event type

        return max(1, damage), is_crit, event_type

    @staticmethod
    def monster_skill(monster, player_stats, skill_data):
        """
        Calculates damage for a monster's special skill.
        Returns: (damage_dealt: int, is_critical: bool, event_type: str)
        """

        # AGI/Dodge formula is unchanged as per your request
        dodge_chance = player_stats.agility * 0.001
        if random.random() < dodge_chance:
            return 0, False, "dodge"  # 0 damage, not a crit (DODGED)

        # --- THIS IS THE FIX ---
        # We must capture all 3 values from monster_attack now
        damage, is_crit, event_type = DamageFormula.monster_attack(monster, player_stats)
        # --- END OF FIX ---

        multiplier = skill_data.get("power", 1.5)
        damage = int(damage * multiplier)

        # The event_type ("hit" or "crit") is passed through from monster_attack
        return damage, is_crit, event_type
