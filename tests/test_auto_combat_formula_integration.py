import unittest.mock as mock

from game_systems.combat.auto_combat_formula import AutoCombatFormula


class TestAutoCombatFormulaIntegration:
    def test_kill_heal_percent_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 100, "ATK": 10, "DEF": 5, "tier": "Normal"}
        player_skills = [{"name": "Bloodlust", "type": "Passive", "passive_bonus": {"kill_heal_percent": 0.05}}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_heal = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)

            assert result_with_heal["damage_taken"] == max(0, result_baseline["damage_taken"] - 50)

    def test_self_damage_percent_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 1000, "ATK": 10, "DEF": 5, "tier": "Normal"}
        player_skills = [{"name": "Reckless Swing", "self_damage_percent": 0.1, "power_multiplier": 1.5}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_recoil = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)

            turns_baseline = result_baseline["turns_to_kill"]
            turns_recoil = result_with_recoil["turns_to_kill"]

            assert turns_recoil <= turns_baseline
            recoil_uses = max(1, int(turns_recoil * 0.25))
            expected_recoil_damage = recoil_uses * 100

            monster_dps = result_with_recoil["monster_dps"]
            base_damage_taken = int(turns_recoil * monster_dps)

            assert result_with_recoil["damage_taken"] == base_damage_taken + expected_recoil_damage

    def test_next_hit_crit_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Dummy", "HP": 1000, "ATK": 20, "DEF": 5}

        # Test baseline
        res_baseline = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills=[])

        # Test with next_hit_crit
        skills_crit = [{"key_id": "shadow_step", "buff": {"next_hit_crit": 1}}]
        res_crit = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills=skills_crit)

        # The damage taken should be reduced by 10%
        assert res_crit["damage_taken"] < res_baseline["damage_taken"]

    def test_conditional_multiplier_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Dummy", "HP": 1000, "ATK": 20, "DEF": 5}

        # Test baseline
        res_baseline = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills=[])

        # Test with conditional_multiplier
        skills_cond = [{"key_id": "venomous_strike", "conditional_multiplier": {"condition": "target_poisoned", "multiplier": 2.0}}]
        res_cond = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills=skills_cond)

        # The damage taken should be reduced by 15%
        assert res_cond["damage_taken"] < res_baseline["damage_taken"]
