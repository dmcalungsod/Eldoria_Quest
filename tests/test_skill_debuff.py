import unittest
from unittest.mock import MagicMock

from game_systems.combat.combat_engine import CombatEngine
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats


class TestToxicBlade(unittest.TestCase):
    def test_toxic_blade_full_lifecycle(self):
        stats = PlayerStats(str_base=10, dex_base=20)
        player = MagicMock(spec=LevelUpSystem)
        player.stats = stats
        player.hp_current = 100
        player.level = 1
        player.stats.get_total_stats_dict = lambda: {
            "STR": 10,
            "DEX": 20,
            "HP": 100,
            "MP": 50,
        }

        monster = {
            "name": "Test Monster",
            "HP": 100,
            "max_hp": 100,
            "ATK": 10,
            "DEF": 0,
            "debuffs": [],
        }

        toxic_blade = {
            "key_id": "toxic_blade",
            "name": "Toxic Blade",
            "type": "Active",
            "mp_cost": 5,
            "power_multiplier": 0.8,
            "debuff": {"poison": 5, "duration": 3},
            "scaling_stat": "DEX",
            "scaling_factor": 2.6,
        }

        skills = [toxic_blade]

        # --- TURN 1: Apply Poison ---
        engine1 = CombatEngine(
            player=player,
            monster=monster,
            player_skills=skills,
            player_mp=50,
            player_class_id=3,
            action="skill:toxic_blade",
        )

        result1 = engine1.run_combat_turn()

        # Simulate Handler updating monster HP
        monster["HP"] = result1["monster_hp"]

        # Check Debuff Applied
        self.assertEqual(len(monster["debuffs"]), 1, "Turn 1: Monster should be poisoned")
        self.assertEqual(monster["debuffs"][0]["damage"], 7, "Turn 1: Poison damage should be 7")
        self.assertEqual(monster["debuffs"][0]["duration"], 3, "Turn 1: Duration should be 3")

        self.assertLess(
            monster["HP"],
            100,
            f"Turn 1: Monster should take attack damage. HP: {monster['HP']}",
        )
        hp_after_attack = monster["HP"]

        # --- TURN 2: Poison Tick ---
        engine2 = CombatEngine(
            player=player,
            monster=monster,  # Monster dict has debuffs now
            player_skills=skills,
            player_mp=45,
            player_class_id=3,
            action="defend",
        )

        result2 = engine2.run_combat_turn()
        monster["HP"] = result2["monster_hp"]

        hp_after_tick = monster["HP"]
        # Expected: HP decreases by 7 (poison)
        # Note: 'defend' action regenerates MP but doesn't deal damage to monster (unless reflect/counter, but monster attacks).
        # Wait, monster attacks in turn 2.
        # But we don't care about player HP.
        # Does monster heal? No.

        # Debuff damage is applied in _process_monster_debuffs.
        # self.monster_hp -= dmg.
        # result["monster_hp"] reflects this.

        expected_hp = hp_after_attack - 7
        self.assertEqual(
            hp_after_tick,
            expected_hp,
            f"Turn 2: Monster should take 7 poison damage. Expected {expected_hp}, got {hp_after_tick}",
        )

        # Duration check
        # Duration decrements in _process_monster_debuffs
        self.assertEqual(monster["debuffs"][0]["duration"], 2, "Turn 2: Duration should be 2")

        # --- TURN 3: Poison Tick ---
        engine3 = CombatEngine(
            player=player,
            monster=monster,
            player_skills=skills,
            player_mp=45,
            player_class_id=3,
            action="defend",
        )
        result3 = engine3.run_combat_turn()
        monster["HP"] = result3["monster_hp"]

        self.assertEqual(
            monster["HP"],
            hp_after_tick - 7,
            "Turn 3: Monster should take 7 poison damage",
        )
        self.assertEqual(monster["debuffs"][0]["duration"], 1, "Turn 3: Duration should be 1")

        # --- TURN 4: Poison Tick & Expire ---
        engine4 = CombatEngine(
            player=player,
            monster=monster,
            player_skills=skills,
            player_mp=45,
            player_class_id=3,
            action="defend",
        )
        result4 = engine4.run_combat_turn()
        monster["HP"] = result4["monster_hp"]

        # Duration 1 -> 0. Damage applied one last time?
        # Logic:
        # dmg = debuff["damage"]
        # self.monster_hp -= dmg
        # debuff["duration"] -= 1
        # if debuff["duration"] > 0: keep

        # So yes, it applies damage then decrements. 1 -> 0. Removed.

        self.assertEqual(
            monster["HP"],
            hp_after_tick - 14,
            "Turn 4: Monster should take 7 poison damage",
        )
        self.assertEqual(len(monster["debuffs"]), 0, "Turn 4: Poison should expire")

        print("Test Passed: Full lifecycle of Toxic Blade poison verified!")


if __name__ == "__main__":
    unittest.main()
