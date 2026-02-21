"""
Game Systems Tests for Eldoria Quest
-------------------------------------
Tests combat, inventory, and player progression systems.
SAFE: Uses mocked DatabaseManager, never touches production data.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock external dependencies for environments where they aren't installed
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_manager import AdventureManager  # noqa: E402
from game_systems.combat.combat_engine import CombatEngine  # noqa: E402
from game_systems.combat.damage_formula import DamageFormula  # noqa: E402
from game_systems.items.inventory_manager import InventoryManager  # noqa: E402
from game_systems.player.level_up import LevelUpSystem  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestGameSystems(unittest.TestCase):
    def setUp(self):
        # Mock DatabaseManager
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_db.player_exists.return_value = True
        self.mock_bot = MagicMock()

    def test_player_stats(self):
        """Test PlayerStats class."""
        stats = PlayerStats(str_base=15, end_base=12, dex_base=10, agi_base=8, mag_base=5, lck_base=10)

        self.assertEqual(stats.strength, 15)
        self.assertEqual(stats.endurance, 12)

        # Test Bonus
        stats.add_bonus_stat("STR", 5)
        self.assertEqual(stats.strength, 20, "Bonus stat not added correctly")

        # Test Serialization
        stats_dict = stats.to_dict()
        restored_stats = PlayerStats.from_dict(stats_dict)
        self.assertEqual(restored_stats.strength, 20)

    def test_tiered_bonus_calculation(self):
        """Test the tiered bonus calculation logic explicitly."""
        from game_systems.player.player_stats import calculate_tiered_bonus

        # Helper for loop logic (reference implementation)
        def reference_calc(val, base):
            total = 0.0
            remaining = val
            tier = 0
            while remaining > 0:
                pts = min(remaining, 100)
                mult = 1.0 + (tier * 0.25)
                total += pts * base * mult
                remaining -= pts
                tier += 1
            return int(total // 1)  # match math.floor behavior

        test_cases = [0, 1, 50, 99, 100, 101, 150, 199, 200, 250, 300, 500, 1000, 1234, 5000]
        base_values = [1.0, 0.5, 2.0, 10.0]

        for val in test_cases:
            for base in base_values:
                expected = reference_calc(val, base)
                result = calculate_tiered_bonus(val, base)
                self.assertEqual(result, expected, f"Failed for val={val}, base={base}")

    def test_inventory_system(self):
        """Test inventory operations logic."""
        inv_manager = InventoryManager(self.mock_db)
        discord_id = 12345

        # Test adding item
        inv_manager.add_item(
            discord_id=discord_id,
            item_key="test_sword",
            item_name="Test Sword",
            item_type="equipment",
            rarity="Uncommon",
            amount=1,
            slot="sword",
            item_source_table="equipment",
        )

        # Verify DB call
        self.mock_db.add_inventory_item.assert_called_with(
            discord_id, "test_sword", "Test Sword", "equipment", "Uncommon", 1, "sword", "equipment"
        )

        # Test getting inventory
        mock_inv = [{"id": 1, "item_name": "Test Sword"}]
        self.mock_db.get_inventory_items.return_value = mock_inv

        inventory = inv_manager.get_inventory(discord_id)
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]["item_name"], "Test Sword")

    def test_damage_formulas(self):
        """Test damage calculation formulas."""
        player_stats = PlayerStats(str_base=15, end_base=12, dex_base=10, agi_base=8, mag_base=5, lck_base=10)
        monster = {"DEF": 5, "Level": 1}

        # Use mock for randomness to make tests deterministic if needed,
        # but DamageFormula logic might be deterministic enough for basic checks

        # Mocking random for critical hit check
        with patch("random.random", return_value=0.5):  # No crit
            damage, crit, _ = DamageFormula.player_attack(player_stats, monster)
            self.assertIsInstance(damage, int)
            self.assertFalse(crit)

    def test_combat_system(self):
        """Test combat engine initialization and turn execution."""
        discord_id = 12345

        # Setup mocks
        player_data = {"level": 5, "experience": 1000, "exp_to_next": 2000, "class_id": 1}
        stats_json = '{"STR": 10, "END": 10, "DEX": 10, "AGI": 10, "MAG": 10, "LCK": 10}'

        self.mock_db.get_player.return_value = player_data
        self.mock_db.get_player_stats_json.return_value = stats_json

        # Manually create stats object since DB mock returns string
        stats = PlayerStats(str_base=10)

        # Create a mock player wrapper (LevelUpSystem)
        # We need to mock this because CombatEngine uses it extensively
        player_wrapper = MagicMock(spec=LevelUpSystem)
        player_wrapper.stats = stats
        player_wrapper.level = 5
        player_wrapper.hp_current = 100
        player_wrapper.hp_max = 100

        test_monster = {"name": "Test Goblin", "HP": 50, "ATK": 10, "DEF": 5, "DEX": 8, "MAG": 0, "Level": 1, "EXP": 20}

        engine = CombatEngine(
            player=player_wrapper, monster=test_monster, player_skills=[], player_mp=30, player_class_id=1
        )

        # Mock random to ensure player hits and monster hits
        with patch("random.random", return_value=0.5):
            result = engine.run_combat_turn()

        self.assertIn("phrases", result)
        self.assertIn("hp_current", result)

    def test_level_up_system(self):
        """Test level-up logic."""
        discord_id = 12345
        stats = PlayerStats(str_base=10)

        level_system = LevelUpSystem(stats=stats, level=1, exp=0, exp_to_next=100)

        # Test adding EXP
        level_system.add_exp(50)
        self.assertEqual(level_system.exp, 50)
        self.assertEqual(level_system.level, 1)

        # Test Level Up
        level_system.add_exp(60)  # Total 110 > 100
        self.assertGreater(level_system.level, 1)

    def test_adventure_mp_persistence(self):
        """Test that MP is preserved after adventure unless leveled up."""
        discord_id = 12345
        manager = AdventureManager(self.mock_db, self.mock_bot)

        # Setup Player & Stats
        player_row = {
            "discord_id": discord_id,
            "level": 1,
            "experience": 0,
            "exp_to_next": 100,
            "current_hp": 20,
            "current_mp": 10,  # Current MP
            "vestige_pool": 0,
            "aurum": 0,
        }
        stats = PlayerStats(mag_base=10)  # Max MP > 10

        # Mocks
        self.mock_db.get_player.return_value = player_row
        self.mock_db.get_player_stats_json.return_value = stats.to_dict()
        self.mock_db.get_active_adventure.return_value = {
            "discord_id": discord_id,
            "location_id": "loc",
            "active": 1,
            "logs": "[]",
            "loot_collected": '{"exp": 10}',
            "active_monster_json": None,
        }
        self.mock_db.get_player_field.return_value = 1

        # Mock Session
        with patch("game_systems.adventure.adventure_manager.AdventureSession") as MockSession:
            session = MockSession.return_value
            session.loot = {"exp": 10}
            session.discord_id = discord_id

            manager.end_adventure(discord_id)

            # Check preservation using update_player_mixed
            # Args: (discord_id,) Kwargs: {set_fields: {...}, inc_fields: {...}}
            args, kwargs = self.mock_db.update_player_mixed.call_args
            set_fields = kwargs.get("set_fields")
            self.assertIsNotNone(set_fields)
            self.assertEqual(set_fields["current_mp"], 10, "MP should be preserved")

            # NOW TEST LEVEL UP CASE
            # Reset Mock
            self.mock_db.update_player_mixed.reset_mock()
            session.loot = {"exp": 200}  # Level up
            player_row["experience"] = 90

            manager.end_adventure(discord_id)

            args, kwargs = self.mock_db.update_player_mixed.call_args
            set_fields = kwargs.get("set_fields")
            self.assertIsNotNone(set_fields)
            self.assertEqual(set_fields["current_mp"], stats.max_mp, "MP should reset on level up")


def run_all_tests():
    """Runs the test suite for run_all_tests.py integration."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGameSystems)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
