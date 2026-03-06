"""
game_systems/combat/auto_combat_formula.py

Deterministic Auto-Combat Abstraction.
Calculates combat resolution in a single math operation for offline expeditions,
skipping the turn-by-turn simulation loop.
"""

import math
import random
from typing import Any

from game_systems.combat.damage_formula import DamageFormula
from game_systems.player.player_stats import calculate_tiered_bonus


class AutoCombatFormula:
    """
    Implements Timeweaver's deterministic clash formula.
    Returns calculated damage taken and turns passed.
    """

    @staticmethod
    def calculate_player_dps(
        player_stats, skills=None, stance="balanced", weather_multiplier=1.0
    ) -> float:
        """Calculates expected average Damage Per Turn (DPT) for the player."""
        str_val = DamageFormula._get_stat(player_stats, "STR")
        dex_val = DamageFormula._get_stat(player_stats, "DEX")
        mag_val = DamageFormula._get_stat(player_stats, "MAG")
        luck_val = DamageFormula._get_stat(player_stats, "LCK")

        # Attack Power
        str_bonus = calculate_tiered_bonus(str_val, 2.0)
        dex_bonus = calculate_tiered_bonus(dex_val, 1.0)
        mag_bonus = calculate_tiered_bonus(mag_val, 0.5)
        basic_attack_power = str_bonus + dex_bonus + mag_bonus

        # Skill abstraction: Assume 25% of turns use the player's best offensive skill
        # Calculate expected power based on DamageFormula's logic
        best_skill_power = 0.0
        if skills:
            for s in skills:
                if s.get("power_multiplier"):
                    skill_level = s.get("skill_level", 1)
                    skill_power = DamageFormula.calculate_skill_attack_power(
                        player_stats, s, skill_level
                    )
                    if skill_power > best_skill_power:
                        best_skill_power = skill_power

        # Blended Attack Power
        if best_skill_power > basic_attack_power:
            attack_power = (basic_attack_power * 0.75) + (best_skill_power * 0.25)
        else:
            attack_power = basic_attack_power



        # Crit expected value
        crit_chance = 0.03 + (luck_val * 0.002)
        crit_multiplier = 1.75
        expected_crit_bonus = 1.0 + (crit_chance * (crit_multiplier - 1.0))

        # Stance multiplier
        stance_mult = 1.0
        if stance == "aggressive":
            stance_mult = 1.2
        elif stance == "defensive":
            stance_mult = 0.8

        dps = attack_power * expected_crit_bonus * stance_mult * weather_multiplier
        return max(1.0, dps)

    @staticmethod
    def calculate_monster_mitigation(monster) -> float:
        """Calculates how much flat damage the monster ignores."""
        monster_def = monster.get("DEF", 0)
        defense_reduction = monster_def * (0.3 + (0.2 * min(1, monster_def / 100)))
        return defense_reduction

    @staticmethod
    def calculate_monster_dps(monster, player_stats) -> float:
        """Calculates expected average Damage Per Turn (DPT) from the monster."""
        attack_power = monster.get("ATK", 10)

        # Skill abstraction: 20% of turns use a skill that hits 1.5x harder
        has_skills = bool(monster.get("skills", []))
        if has_skills:
            attack_power *= 1.10

        # Crit expected value (5% chance, 1.5x mult)
        crit_chance = 0.05
        crit_multiplier = 1.5
        expected_crit_bonus = 1.0 + (crit_chance * (crit_multiplier - 1.0))

        # Accuracy/Dodge expected value
        agi = DamageFormula._get_stat(player_stats, "AGI")
        dodge_chance = min(0.9, agi * 0.001)

        base_accuracy = 1.0 + monster.get("accuracy_percent", 0.0)
        # Cap hit chance between 10% and 100%
        hit_chance = max(0.1, min(1.0, base_accuracy - dodge_chance))

        expected_power = attack_power * expected_crit_bonus * hit_chance
        return max(1.0, expected_power)

    @staticmethod
    def calculate_player_mitigation(player_stats) -> float:
        """Calculates flat defense reduction for the player."""
        end = DamageFormula._get_stat(player_stats, "END")
        flat_def = DamageFormula._get_stat(player_stats, "DEF")

        defense = calculate_tiered_bonus(end, 1.5) + flat_def
        defense_reduction = defense * (0.3 + (0.2 * min(1, defense / 100)))
        return defense_reduction

    @staticmethod
    def resolve_clash(
        player_stats,
        monster: dict,
        player_skills: list = None,
        stance: str = "balanced",
        fatigue_multiplier: float = 1.0,
        weather_multiplier: float = 1.0,
    ) -> dict[str, Any]:
        """
        Calculates the deterministic outcome of a battle.
        Returns:
            {
                "turns_to_kill": int,
                "damage_taken": int,
                "player_dps": float,
                "monster_dps": float,
            }
        """
        # 1. Power Abstraction
        player_dps_raw = AutoCombatFormula.calculate_player_dps(
            player_stats, player_skills, stance, weather_multiplier
        )
        monster_mitigation = AutoCombatFormula.calculate_monster_mitigation(monster)

        # Player net damage per turn
        player_net_dps = max(1.0, player_dps_raw - monster_mitigation)

        monster_dps_raw = AutoCombatFormula.calculate_monster_dps(monster, player_stats)
        player_mitigation = AutoCombatFormula.calculate_player_mitigation(player_stats)

        # Stance vulnerability
        stance_vuln = 1.0
        if stance == "aggressive":
            stance_vuln = 1.2
        elif stance == "defensive":
            stance_vuln = 0.8

        # Base damage clamped to 0
        base_damage = max(0.0, monster_dps_raw - player_mitigation)

        # Ensure minimum chip damage from monster (5% of its ATK) BEFORE multipliers
        chip_damage = monster.get("ATK", 10) * 0.05
        monster_net_dps = max(
            1.0, max(base_damage, chip_damage) * stance_vuln * fatigue_multiplier
        )

        # 2. Deterministic Clash
        monster_hp = monster.get("HP", 1)
        # Ceil to ensure at least 1 turn, representing the time taken
        turns_to_kill = math.ceil(monster_hp / player_net_dps)

        # Cap turns at 15 to prevent infinite auto-loops in extreme defense scenarios
        turns_to_kill = min(15, turns_to_kill)

        # Base damage taken over the combat duration
        base_damage_taken = turns_to_kill * monster_net_dps

        # 3. Variance (±10%)
        variance = random.uniform(0.9, 1.1)  # nosec B311
        final_damage_taken = int(base_damage_taken * variance)

        # 4. Apply Auto-Combat specific mechanics from skills
        if player_skills:
            for skill in player_skills:
                # Warrior: Bloodlust (Heal on kill)
                passive_bonus = skill.get("passive_bonus", {})
                if "kill_heal_percent" in passive_bonus:
                    # Healing is applied at the end of the combat since it's a kill heal
                    heal_amount = int((player_stats.get("HP", 100) if isinstance(player_stats, dict) else getattr(player_stats, "max_hp", 100)) * passive_bonus["kill_heal_percent"])
                    final_damage_taken = max(0, final_damage_taken - heal_amount)

                # Warrior: Reckless Swing (Self damage)
                # Assume skill is used 25% of the turns
                if "self_damage_percent" in skill:
                    # Recoil is applied per use. Uses = turns_to_kill * 0.25
                    uses = max(1, int(turns_to_kill * 0.25))
                    # Recoil is based on damage dealt by the skill, but we approximate to % of HP for auto-combat
                    # if the skill doesn't hit, but for auto-combat, let's use the player's max HP as a safe bet
                    recoil_amount = int((player_stats.get("HP", 100) if isinstance(player_stats, dict) else getattr(player_stats, "max_hp", 100)) * skill["self_damage_percent"]) * uses
                    final_damage_taken += recoil_amount

                # Rogue: next_hit_crit burst damage abstraction
                if "next_hit_crit" in skill.get("buff", {}):
                    # Abstract the impact of guaranteed crits by reducing expected incoming damage
                    final_damage_taken = int(final_damage_taken * 0.90)

                # Rogue: conditional_multiplier burst damage abstraction
                if "conditional_multiplier" in skill:
                    # Abstract the impact of conditional multipliers (like venomous strike)
                    final_damage_taken = int(final_damage_taken * 0.85)



        return {
            "turns_to_kill": int(turns_to_kill),
            "damage_taken": max(0, int(final_damage_taken)),
            "player_dps": round(player_net_dps, 2),
            "monster_dps": round(monster_net_dps, 2),
        }
