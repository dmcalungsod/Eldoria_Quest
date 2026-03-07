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

    def test_divine_shield_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 100, "ATK": 50, "DEF": 5, "tier": "Normal"}
        player_skills = [{"key_id": "divine_shield"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_shield = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)
            # Monster DPS should be reduced by 10% before defense, resulting in less damage taken
            assert result_with_shield["damage_taken"] < result_baseline["damage_taken"]

    def test_aura_of_vitality_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 100, "ATK": 100, "DEF": 5, "tier": "Normal"}
        player_skills = [{"key_id": "aura_of_vitality"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_aura = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)
            # 2% of 1000 HP is 20 heal
            assert result_with_aura["damage_taken"] == max(0, result_baseline["damage_taken"] - 20)

    def test_meteor_swarm_integration(self):
        player_stats = {"STR": 10, "END": 10, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 1000, "ATK": 10, "DEF": 5, "tier": "Normal"}
        player_skills = [{"key_id": "meteor_swarm"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_meteor = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)

            import math
            expected_turns = max(1, math.ceil(result_baseline["turns_to_kill"] * 0.85))
            assert result_with_meteor["turns_to_kill"] == expected_turns
            assert result_with_meteor["damage_taken"] < result_baseline["damage_taken"]

    def test_mana_shield_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000, "MP": 200}
        monster = {"name": "Test Goblin", "HP": 100, "ATK": 100, "DEF": 5, "tier": "Normal"}
        player_skills = [{"key_id": "mana_shield"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_shield = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)
            # 50% of 200 MP is 100 absorb
            expected_absorb = min(result_baseline["damage_taken"], 100)
            assert result_with_shield["damage_taken"] == result_baseline["damage_taken"] - expected_absorb

    def test_summon_companion_integration(self):
        player_stats = {"STR": 50, "END": 20, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Goblin", "HP": 100, "ATK": 200, "DEF": 5, "tier": "Normal"}
        player_skills = [{"key_id": "summon_companion"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_companion = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)
            # 20% of 1000 HP is 200 buffer
            assert result_with_companion["damage_taken"] == max(0, result_baseline["damage_taken"] - 200)

    def test_pack_tactics_integration(self):
        player_stats = {"STR": 10, "END": 10, "DEF": 10, "AGI": 10, "DEX": 10, "MAG": 10, "LCK": 5, "HP": 1000}
        monster = {"name": "Test Boss", "HP": 1000, "ATK": 10, "DEF": 5, "tier": "Boss"}
        player_skills = [{"key_id": "pack_tactics"}]
        with mock.patch("random.uniform", return_value=1.0):
            result_baseline = AutoCombatFormula.resolve_clash(player_stats, monster)
            result_with_pack = AutoCombatFormula.resolve_clash(player_stats, monster, player_skills)

            assert result_with_pack["player_dps"] > result_baseline["player_dps"]
            assert result_with_pack["turns_to_kill"] < result_baseline["turns_to_kill"]
