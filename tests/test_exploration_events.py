"""
tests/test_exploration_events.py

Unit tests for the ExplorationEvents system.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Adjust path for standalone execution
sys.path.insert(0, ".")

from game_systems.adventure.exploration_events import ExplorationEvents
from game_systems.player.player_stats import PlayerStats


class TestExplorationEvents(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.events = ExplorationEvents(self.mock_db)

        # Setup common context
        # PlayerStats(str, end, agi, dex, mag, luck)
        self.stats = PlayerStats(10, 10, 10, 10, 10, 10)

        self.context = {
            "player_stats": self.stats,
            "vitals": {"current_hp": 50, "current_mp": 20},
            "player_row": {"discord_id": 12345},
            "loot": {}
        }

    def test_safe_room_event(self):
        """Test that safe room heals player."""
        initial_hp = 50
        initial_mp = 20

        result = self.events.handle_event("safe_room", self.context)

        self.assertFalse(result["dead"])
        self.assertGreater(result["vitals"]["current_hp"], initial_hp)
        self.assertGreater(result["vitals"]["current_mp"], initial_mp)

        # Verify DB call
        self.mock_db.set_player_vitals.assert_called_once()

        # Check logs
        self.assertTrue(any("Restored" in log for log in result["log"]))

    def test_hidden_stash_event(self):
        """Test hidden stash gives loot."""
        result = self.events.handle_event("hidden_stash", self.context)

        self.assertFalse(result["dead"])
        self.assertTrue(result["loot"]) # Should have something

        has_aurum = "aurum" in result["loot"]
        has_item = len(result["loot"]) > 0 and not has_aurum

        self.assertTrue(has_aurum or has_item)
        self.assertTrue(result["log"])

    def test_ancient_shrine_event(self):
        """Test ancient shrine gives XP."""
        result = self.events.handle_event("ancient_shrine", self.context)

        self.assertFalse(result["dead"])
        self.assertIn("exp", result["loot"])
        self.assertGreater(result["loot"]["exp"], 0)
        self.assertTrue(any("XP" in log for log in result["log"]))

    def test_trap_event_damage(self):
        """Test trap deals damage."""
        initial_hp = 50
        self.context["vitals"]["current_hp"] = initial_hp

        # Force a high random roll for dodge check (randint > dodge_chance) to ensure hit
        # dodge_chance for 10 AGI is 5.
        with patch('random.randint', return_value=100):
            result = self.events.handle_event("trap_pit", self.context)

            self.assertLess(result["vitals"]["current_hp"], initial_hp)
            self.mock_db.set_player_vitals.assert_called()
            self.assertTrue(any("damage" in log for log in result["log"]))

    def test_trap_event_dead(self):
        """Test trap can kill."""
        self.context["vitals"]["current_hp"] = 5

        # 10 stats -> Max HP 150. 10% is 15 damage.
        # Even with min roll it should kill (5 - 15 = -10).

        result = self.events.handle_event("trap_pit", self.context)

        self.assertTrue(result["dead"])
        self.assertLessEqual(result["vitals"]["current_hp"], 0)

    def test_unknown_event(self):
        """Test fallback for unknown event."""
        result = self.events.handle_event("unknown_xyz", self.context)
        self.assertFalse(result["dead"])
        self.assertEqual(result["vitals"], self.context["vitals"])

if __name__ == "__main__":
    unittest.main()
