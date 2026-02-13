import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from game_systems.adventure.event_handler import EventHandler
from game_systems.adventure.adventure_session import AdventureSession
from game_systems.data.materials import MATERIALS

class TestWildGathering(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.quest_system = MagicMock()
        self.discord_id = 12345
        self.inventory_manager = MagicMock()

        # Mock quest system to return no quests
        self.quest_system.get_player_quests.return_value = []

        # Setup EventHandler
        self.event_handler = EventHandler(self.db, self.quest_system, self.discord_id)

    def test_wild_gathering_trigger(self):
        """Test that wild gathering triggers when no quest event is found."""

        # Mock random to ensure no regeneration (return > regen_chance)
        # and to ensure wild gathering success (return < 0.30)
        # resolve_non_combat calls random.randint(1, 100). regen_chance is 70.
        # So we need > 70. Let's say 80.
        # Then _perform_wild_gathering calls random.random(). We need < 0.30. Let's say 0.1.

        def side_effect_choice(seq):
            if isinstance(seq, list) and "medicinal_herb" in seq:
                return "medicinal_herb"
            # If it's the phrases list, return the first one
            return seq[0]

        with patch('random.randint', return_value=80), \
             patch('random.random', return_value=0.1), \
             patch('random.choice', side_effect=side_effect_choice):

             result = self.event_handler.resolve_non_combat(regen_chance=70)

             self.assertIn("loot", result)
             self.assertEqual(result["loot"], {"medicinal_herb": 1})
             # We check if the item name (or part of the phrase) is in the log.
             # The item name for "medicinal_herb" is "Medicinal Herb".
             self.assertTrue(any("Medicinal Herb" in log for log in result["log"]))

    def test_adventure_session_loot_processing(self):
        """Test that AdventureSession correctly processes the loot returned by EventHandler."""

        # Mock EventHandler to return loot
        mock_event_result = {
            "log": ["Found a herb!"],
            "dead": False,
            "loot": {"medicinal_herb": 1}
        }
        self.event_handler.resolve_non_combat = MagicMock(return_value=mock_event_result)

        # Initialize AdventureSession
        # We need to mock DB methods called in __init__
        # But AdventureSession __init__ is lightweight if row_data is None

        session = AdventureSession(self.db, self.quest_system, self.inventory_manager, self.discord_id)

        # Inject our event handler
        session.events = self.event_handler

        # Mock location
        with patch('game_systems.adventure.adventure_session.LOCATIONS', {"forest": {"name": "Forest"}}):
            session.location_id = "forest"

            # Mock other things to bypass combat checks
            session.active_monster = None

            # Mock save_state to avoid DB calls
            session.save_state = MagicMock()

            # Run simulate_step
            # We need to force non-combat path.
            # AdventureSession calls random.randint(1, 100) > REGEN_CHANCE (40) to trigger encounter.
            # We want NO encounter, so random <= 40.

            with patch('random.randint', return_value=10):
                result = session.simulate_step()

                # Check if loot was added to session
                self.assertIn("medicinal_herb", session.loot)
                self.assertEqual(session.loot["medicinal_herb"], 1)

if __name__ == '__main__':
    unittest.main()
