import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mocking necessary modules before import
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.items.consumable_manager import ConsumableManager  # noqa: E402
from game_systems.player.level_up import LevelUpSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestPlayerPoison(unittest.TestCase):
    def test_01_combat_engine_applies_poison(self):
        """Test that CombatEngine applies poison to player when hit by a skill with debuff."""
        # Setup
        stats = PlayerStats(str_base=10, end_base=10)
        player = MagicMock(spec=LevelUpSystem)
        player.stats = stats
        player.hp_current = 100
        player.level = 1
        player.stats.get_total_stats_dict = lambda: {"HP": 100, "MP": 50, "DEF": 0, "AGI": 10}

        monster = {"name": "Slime", "HP": 50, "ATK": 10, "DEF": 0, "MP": 20}

        # Skill with debuff
        poison_skill = {
            "name": "Poison Spit",
            "power": 1.0,
            "mp_cost": 0,
            "debuff": {"poison": 5, "duration": 3}
        }

        # Mock AI to use this skill
        with patch("game_systems.combat.combat_engine.MonsterAI") as MockAI, \
             patch("game_systems.combat.combat_engine.DamageFormula") as MockDamage:

            MockAI.choose_action.return_value = {"type": "skill", "skill": poison_skill}
            MockDamage.monster_skill.return_value = (10, False, "hit")
            MockDamage.player_attack.return_value = (10, False, "hit")

            # Init Engine
            engine = CombatEngine(
                player=player,
                monster=monster,
                player_skills=[],
                player_mp=50,
                player_class_id=1,
                action="auto", # Changed from defend to auto/attack to ensure hit
                player_debuffs=[]
            )

            result = engine.run_combat_turn()

            # Check if player_debuffs returned in result
            self.assertIn("player_debuffs", result)
            debuffs = result["player_debuffs"]
            self.assertEqual(len(debuffs), 1, "Player should be poisoned when not defending.")
            self.assertEqual(debuffs[0]["type"], "poison")
            self.assertEqual(debuffs[0]["damage"], 5)

    def test_02_consumable_manager_cures_poison(self):
        """Test that ConsumableManager cures poison."""
        mock_db = MagicMock()
        manager = ConsumableManager(mock_db)

        # Mock active poison buff
        mock_db.get_active_buffs.return_value = [
            {"buff_id": "p1", "name": "Poison", "stat": "poison", "amount": 5}
        ]

        # Mock item
        mock_db.get_inventory_item.return_value = {
            "item_key": "antidote_basic",
            "item_type": "consumable",
            "item_name": "Antidote"
        }

        mock_db.get_player_vitals.return_value = {"current_hp": 80, "current_mp": 50}
        mock_db.get_player_stats_json.return_value = {"str": 10}
        mock_db.consume_item_atomic.return_value = True

        # Mock CONSUMABLES dict
        antidote_data = {
            "id": "antidote_basic",
            "name": "Antidote",
            "type": "antidote",
            "effect": {"cure_poison": True},
            "rarity": "Common"
        }

        with patch.dict("game_systems.items.consumable_manager.CONSUMABLES", {"antidote_basic": antidote_data}), \
             patch("game_systems.items.consumable_manager.PlayerStats"):

            success, msg = manager.use_item(123, 1)

            if not success:
                print(f"Current behavior: {msg}")

            self.assertTrue(success, "Should successfully use antidote")
            self.assertIn("poison", msg.lower())

if __name__ == "__main__":
    unittest.main()
