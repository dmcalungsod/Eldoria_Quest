# Mock pymongo before importing anything that uses it
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.modules["pymongo"] = MagicMock()

from game_systems.adventure.event_handler import EventHandler  # noqa: E402
from game_systems.data.factions import FACTIONS  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestFactionEncounters(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_quest = MagicMock()
        self.discord_id = 12345
        self.handler = EventHandler(self.mock_db, self.mock_quest, self.discord_id)

        # Mock FactionSystem within Handler
        self.handler.faction_system = MagicMock()

        # Common context
        self.context = {
            "vitals": {"current_hp": 100, "current_mp": 50},
            "player_stats": MagicMock(max_hp=200, max_mp=100)
        }

    def test_perform_faction_encounter_member(self):
        # Setup: Player is a Pathfinder
        self.handler.faction_system.get_player_faction.return_value = {
            "faction_id": "pathfinders"
        }

        # Force random choice to pick Pathfinders and the first encounter
        with patch("random.random", return_value=0.1), \
             patch("random.choice") as mock_choice:

            encounter_data = {
                "text": "A scout appears.",
                "reward_member": {"type": "item", "key": "map_fragment", "amount": 1, "rep": 15},
                "reward_non_member": {"type": "xp", "amount": 10}
            }

            # Mock random.choice to handle different calls
            def side_effect(arg):
                # If choosing from encounters list (list of dicts)
                if isinstance(arg, list) and len(arg) > 0 and isinstance(arg[0], dict):
                    return encounter_data
                # If choosing from faction keys
                return "pathfinders"

            mock_choice.side_effect = side_effect

            result = self.handler._perform_faction_encounter(self.context)

            self.assertIsNotNone(result)
            self.assertIn("log", result)
            # Check for item box or log message
            self.assertTrue(any("Received:" in l for l in result["log"]))

            # Verify Reputation Grant
            self.handler.faction_system.grant_reputation.assert_called_with(
                self.discord_id, 15, source="Faction Encounter"
            )

    def test_perform_faction_encounter_non_member(self):
        # Setup: Player is Iron Vanguard
        self.handler.faction_system.get_player_faction.return_value = {
            "faction_id": "iron_vanguard"
        }

        # Force target to be Pathfinders (random >= 0.5)
        with patch("random.random", return_value=0.8), \
             patch("random.choice") as mock_choice:

            encounter_data = {
                "text": "A scout appears.",
                "reward_member": {"type": "item", "key": "map_fragment", "amount": 1},
                "reward_non_member": {"type": "xp", "amount": 25, "text": "They share a route."}
            }

            def side_effect(arg):
                if isinstance(arg, list) and len(arg) > 0 and isinstance(arg[0], dict):
                    return encounter_data
                return "pathfinders"

            mock_choice.side_effect = side_effect

            result = self.handler._perform_faction_encounter(self.context)

            self.assertIsNotNone(result)
            # Expect XP reward
            self.assertIn("loot", result)
            self.assertEqual(result["loot"].get("exp"), 25)
            # Verify NO Reputation Grant
            self.handler.faction_system.grant_reputation.assert_not_called()

    def test_perform_faction_encounter_no_faction(self):
        # Setup: Player has no faction
        self.handler.faction_system.get_player_faction.return_value = None

        with patch("random.choice") as mock_choice:
            encounter_data = {
                "text": "A scout appears.",
                "reward_member": {},
                "reward_non_member": {"type": "xp", "amount": 10}
            }

            def side_effect(arg):
                if isinstance(arg, list) and len(arg) > 0 and isinstance(arg[0], dict):
                    return encounter_data
                return "pathfinders"

            mock_choice.side_effect = side_effect

            result = self.handler._perform_faction_encounter(self.context)

            self.assertIsNotNone(result)
            self.assertIn("loot", result)
            self.assertEqual(result["loot"].get("exp"), 10)

if __name__ == '__main__':
    unittest.main()
