import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo BEFORE any imports
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Adjust path to import game modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can safely import modules that depend on pymongo
from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_events import AdventureEvents  # noqa: E402
from game_systems.adventure.event_handler import EventHandler  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestDeadTurns(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_quest_system = MagicMock()
        self.discord_id = 12345
        self.event_handler = EventHandler(self.mock_db, self.mock_quest_system, self.discord_id)

        # Common Mock Returns
        self.mock_db.get_player_stats_json.return_value = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 10},
        }
        # Calculated Max HP (END=10): 50 + (10 * 10) = 150
        # Calculated Max MP (MAG=10): 20 + (10 * 5) = 70

        # Default to Full HP/MP for Surge tests
        self.mock_db.get_player_vitals.return_value = {"current_hp": 150, "current_mp": 70}

        # Mock Context
        self.player_stats = PlayerStats(str_base=10, end_base=10, dex_base=10, agi_base=10, mag_base=10, lck_base=10)
        self.context = {
            "player_stats": self.player_stats,
            "vitals": {"current_hp": 150, "current_mp": 70},
            "stats_dict": self.player_stats.get_total_stats_dict(),
            "player_row": {"class_id": 1},
        }

    def test_full_rest_prevention(self):
        """Test that full HP/MP now returns 'Already Rested' message instead of SURGE."""
        # Force regen path by high regen_chance
        result = self.event_handler.resolve_non_combat(context=self.context, regen_chance=100)

        # Should have "Already Rested" message
        log_str = "\n".join(result["log"])
        self.assertIn("already fully rested", log_str)
        # Should NOT have loot
        self.assertNotIn("loot", result)

    def test_scavenge_fallback_on_failed_gather(self):
        """Test that failed gathering (from exploration fallback) results in Scavenge."""
        # Ensure regen fails so we fall back to Quest -> Wild Gather
        # Or just pass regen_chance=0
        self.mock_quest_system.get_player_quests.return_value = []

        with patch("random.randint") as mock_randint, patch("random.random") as mock_random:
            # Sequence:
            # 1. Regen check: 100 (fail, since we pass regen_chance=0 to be sure, but let's assume standard flow)
            # Actually, let's just use regen_chance=0 to skip regen logic entirely.
            # 2. Gather check: 99 (fail > 35 base chance)
            # 3. Scavenge amount (Aurum): 5
            # random.random for scavenge type: 0.1 (< 0.5 -> Aurum)

            # Note: resolve_non_combat calls random.randint(1, 100) for regen check.
            # If we pass regen_chance=0, it skips regen.
            # Then it calls _perform_quest_event -> _perform_wild_gathering.
            # _perform_wild_gathering calls random.randint(1, 100) for gather chance.

            # Side effect: [gather_roll, scavenge_amount]
            # Wait, resolve_non_combat calls randint once for regen check.
            # So side effect: [regen_roll, gather_roll, scavenge_amount]

            mock_randint.side_effect = [100, 99, 5]
            mock_random.return_value = 0.1

            # Ensure regen_chance allows failing regen check
            result = self.event_handler.resolve_non_combat(context=self.context, regen_chance=50)

        # Should NOT have SURGE message
        log_str = "\n".join(result["log"])
        self.assertFalse(any(phrase in log_str for phrase in AdventureEvents.SURGE_PHRASES))

        # Should have Aurum Scavenge message
        self.assertTrue("Aurum" in log_str)

        # Should have Aurum loot
        self.assertIn("loot", result)
        self.assertIn("aurum", result["loot"])
        self.assertEqual(result["loot"]["aurum"], 5)

    def test_direct_wild_gather_scavenge(self):
        """Test failed gathering from normal exploration triggers Scavenge."""
        self.mock_quest_system.get_player_quests.return_value = []

        with patch("random.randint") as mock_randint, patch("random.random") as mock_random:
            # Sequence:
            # 1. Regen check: 99 (fail)
            # 2. Gather check: 99 (fail)
            # 3. Scavenge amount (XP): 10
            # random.random for scavenge type: 0.6 (> 0.5 -> XP)

            mock_randint.side_effect = [99, 99, 10]
            mock_random.return_value = 0.6

            result = self.event_handler.resolve_non_combat(context=self.context, regen_chance=0)

        # Should NOT have SURGE message
        log_str = "\n".join(result["log"])
        self.assertFalse(any(phrase in log_str for phrase in AdventureEvents.SURGE_PHRASES))

        # Should have XP Scavenge message
        self.assertTrue("XP" in log_str)

        # Should have XP loot
        self.assertIn("loot", result)
        self.assertIn("exp", result["loot"])
        self.assertEqual(result["loot"]["exp"], 10)


if __name__ == "__main__":
    unittest.main()
