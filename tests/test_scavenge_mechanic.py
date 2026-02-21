import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pymongo BEFORE any imports
sys.modules["pymongo"] = MagicMock()
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

    def test_surge_replaces_dead_turn(self):
        """Test that full HP/MP now triggers SURGE (gathering attempt) instead of 'no event'."""
        # Force regen path
        with patch("random.randint") as mock_randint:
            # 1: random.randint(1,100) <= regen_chance (100) -> Enter regen
            # 1: random.randint(1,100) <= base_chance (35+25=60) -> Successful Gather
            mock_randint.side_effect = [1, 1]

            with patch("random.choices", return_value=["medicinal_herb"]):
                result = self.event_handler.resolve_non_combat(context=self.context, regen_chance=100)

        # Should have SURGE message
        log_str = "\n".join(result["log"])
        self.assertTrue(any(phrase in log_str for phrase in AdventureEvents.SURGE_PHRASES))
        # Should have loot
        self.assertIn("loot", result)
        self.assertIn("medicinal_herb", result["loot"])

    def test_scavenge_fallback(self):
        """Test that failed gathering (from Surge or otherwise) results in Scavenge."""
        # Case 1: Surge -> Failed Gather -> Scavenge
        self.mock_quest_system.get_player_quests.return_value = []

        with patch("random.randint") as mock_randint, patch("random.random") as mock_random:
            # Sequence:
            # 1. Regen check: 1 (success)
            # 2. Gather check: 100 (fail > 60)
            # 3. Scavenge amount (Aurum): 5
            # random.random for scavenge type: 0.1 (< 0.5 -> Aurum)

            mock_randint.side_effect = [1, 100, 5]
            mock_random.return_value = 0.1

            result = self.event_handler.resolve_non_combat(context=self.context, regen_chance=100)

        # Should have SURGE message
        log_str = "\n".join(result["log"])
        self.assertTrue(any(phrase in log_str for phrase in AdventureEvents.SURGE_PHRASES))

        # Should have Aurum Scavenge message
        self.assertTrue("Aurum" in log_str)

        # Should have Aurum loot
        self.assertIn("loot", result)
        self.assertIn("aurum", result["loot"])
        self.assertEqual(result["loot"]["aurum"], 5)

    def test_direct_wild_gather_scavenge(self):
        """Test failed gathering from normal exploration (not surge) triggers Scavenge."""
        self.mock_quest_system.get_player_quests.return_value = []

        # Set NOT full HP/MP so we don't accidentally surge if regen logic was wrong
        # But here we pass regen_chance=0 so we skip regen anyway.

        with patch("random.randint") as mock_randint, patch("random.random") as mock_random:
            # Sequence:
            # 1. Regen check: 100 (fail, assuming chance < 100, let's pass regen_chance=0)
            # 2. Faction check: 100 (fail, > 10)
            # 3. Gather check: 100 (fail > 35)
            # 4. Scavenge amount (XP): 10
            # random.random for scavenge type: 0.6 (> 0.5 -> XP)

            mock_randint.side_effect = [100, 100, 100, 10]
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
