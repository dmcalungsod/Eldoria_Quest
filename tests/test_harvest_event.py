import datetime
import sys
import unittest
from unittest.mock import MagicMock, patch
import os

sys.path.append(os.getcwd())

# Mock pymongo BEFORE importing DatabaseManager
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.events.world_event_system import WorldEventSystem  # noqa: E402
from game_systems.adventure.adventure_events import AdventureEvents  # noqa: E402
from game_systems.adventure.event_handler import EventHandler  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402

class TestHarvestEvent(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.event_system = WorldEventSystem(self.mock_db)
        self.mock_quest_system = MagicMock()
        self.handler = EventHandler(self.mock_db, self.mock_quest_system, 12345)

    def test_harvest_event_config(self):
        # Test config existence and values
        self.assertIn("harvest_festival", self.event_system.EVENT_CONFIGS)
        config = self.event_system.EVENT_CONFIGS["harvest_festival"]
        self.assertEqual(config["modifiers"]["gathering_boost"], 2.0)

    def test_harvest_atmosphere(self):
        # Test regeneration atmosphere

        # We need to force the 40% chance.
        with patch('game_systems.adventure.adventure_events.random') as mock_random:
            # 1. High HP check (HP=1.0 > 0.8): Need > 0.30 to fail. -> 0.99
            # 2. Atmosphere check: Need < 0.40 to pass. -> 0.1
            # 3. Weather check: Need > 0.30 to fail (so we don't override Harvest). -> 0.99
            mock_random.random.side_effect = [0.99, 0.1, 0.99]
            mock_random.choice.side_effect = lambda x: x[0] # Pick first item

            logs = AdventureEvents.regeneration(event_type="harvest_festival")

            # Check if one of the harvest strings is in the logs
            found = False
            for log in logs:
                if any(h_str in log for h_str in AdventureEvents.ATMOSPHERE_HARVEST):
                    found = True
                    break
            self.assertTrue(found, "Harvest atmosphere string not found in logs")

    def test_wild_gathering_boost(self):
        # Setup context with gathering boost
        stats = PlayerStats()
        stats.set_base_stat("LCK", 0) # No luck bonus
        context = {
            "player_stats": stats,
            "active_boosts": {"gathering_boost": 2.0},
            "vitals": {"current_hp": 100, "current_mp": 100}
        }

        # We need to patch random inside event_handler
        with patch('game_systems.adventure.event_handler.random') as mock_random:
            # 1. randint(1, 100) <= base_chance -> 1 (Success)
            # 2. random.choices -> ["medicinal_herb"]
            # 3. random.random() < 0.20 (variance) -> 1.0 (Fail)

            mock_random.randint.return_value = 1
            mock_random.choices.return_value = ["medicinal_herb"]
            mock_random.random.return_value = 1.0

            # Call method
            result = self.handler._perform_wild_gathering(context, "forest_clearing")

            # Verify loot
            self.assertIn("loot", result)
            self.assertIn("medicinal_herb", result["loot"])

            # Base quantity is 1 (luck=0). Boost is 2.0. Result should be 2.
            # quantity = min(3, 1 + 0) = 1
            # quantity = int(1 * 2.0) = 2
            self.assertEqual(result["loot"]["medicinal_herb"], 2)

            # Verify log contains "(Bonus)"
            self.assertTrue(any("(Bonus)" in log for log in result["log"]))

    def test_wild_gathering_no_boost(self):
        # Setup context WITHOUT gathering boost
        stats = PlayerStats()
        stats.set_base_stat("LCK", 0)
        context = {
            "player_stats": stats,
            "active_boosts": {},
            "vitals": {"current_hp": 100, "current_mp": 100}
        }

        with patch('game_systems.adventure.event_handler.random') as mock_random:
            mock_random.randint.return_value = 1
            mock_random.choices.return_value = ["medicinal_herb"]
            mock_random.random.return_value = 1.0

            result = self.handler._perform_wild_gathering(context, "forest_clearing")

            self.assertEqual(result["loot"]["medicinal_herb"], 1)
            self.assertFalse(any("(Bonus)" in log for log in result["log"]))

if __name__ == "__main__":
    unittest.main()
