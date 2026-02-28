import unittest

from game_systems.player.player_stats import PlayerStats


class TestInventoryScaling(unittest.TestCase):
    def test_max_inventory_slots_base(self):
        """Test base capacity with minimum stats."""
        stats = PlayerStats(str_base=1, dex_base=1)
        # Base 10 + floor(1 * 0.5) + floor(1 * 0.25) = 10 + 0 + 0 = 10
        self.assertEqual(stats.max_inventory_slots, 10)

    def test_max_inventory_slots_high_str(self):
        """Test capacity with high Strength."""
        stats = PlayerStats(str_base=20, dex_base=1)
        # Base 10 + floor(20 * 0.5) + floor(1 * 0.25) = 10 + 10 + 0 = 20
        self.assertEqual(stats.max_inventory_slots, 20)

    def test_max_inventory_slots_high_dex(self):
        """Test capacity with high Dexterity."""
        stats = PlayerStats(str_base=1, dex_base=20)
        # Base 10 + floor(1 * 0.5) + floor(20 * 0.25) = 10 + 0 + 5 = 15
        self.assertEqual(stats.max_inventory_slots, 15)

    def test_max_inventory_slots_mixed(self):
        """Test capacity with mixed stats."""
        stats = PlayerStats(str_base=10, dex_base=10)
        # Base 10 + floor(10 * 0.5) + floor(10 * 0.25) = 10 + 5 + 2 = 17
        self.assertEqual(stats.max_inventory_slots, 17)

    def test_max_inventory_slots_caching(self):
        """Test that the value is cached and updated when stats change."""
        stats = PlayerStats(str_base=10, dex_base=10)
        initial_slots = stats.max_inventory_slots
        self.assertEqual(initial_slots, 17)

        # Verify cache is set (implementation detail check)
        self.assertEqual(stats._cached_max_slots, 17)

        # Change stat
        stats.add_base_stat("STR", 10) # STR becomes 20
        # Expected: 10 + 10 + 2 = 22

        # Verify cache is invalidated
        self.assertIsNone(stats._cached_max_slots)

        self.assertEqual(stats.max_inventory_slots, 22)

if __name__ == '__main__':
    unittest.main()
