import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from database.database_manager import DatabaseManager  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.adventure.event_handler import EventHandler  # noqa: E402
from game_systems.player.player_stats import PlayerStats  # noqa: E402


class TestWildGathering(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock(spec=DatabaseManager)
        self.quest_system = MagicMock()
        self.discord_id = 12345
        self.inventory_manager = MagicMock()

        # Mock quest system to return no quests
        self.quest_system.get_player_quests.return_value = []

        # Mock DB stats
        self.mock_stats = {
            "STR": {"base": 10},
            "END": {"base": 10},
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 10},
            "LCK": {"base": 50},  # High luck
        }
        # get_player_stats_json returns a dict, not a string
        self.db.get_player_stats_json.return_value = self.mock_stats

        # Prepare context for new optimization
        self.stats_obj = PlayerStats.from_dict(self.mock_stats)
        self.context = {
            "player_stats": self.stats_obj,
            "vitals": {"current_hp": 100, "current_mp": 50},
            "stats_dict": self.stats_obj.get_total_stats_dict(),
        }

        # Setup EventHandler
        self.event_handler = EventHandler(self.db, self.quest_system, self.discord_id)

    def test_wild_gathering_trigger_with_location(self):
        """Test that wild gathering uses location data."""

        # Mock LOCATIONS in event_handler
        mock_locations = {"test_loc": {"gatherables": [("test_herb", 100)]}}

        # Mock MATERIALS to include test_herb
        with (
            patch("game_systems.adventure.event_handler.LOCATIONS", mock_locations),
            patch.dict(
                "game_systems.adventure.event_handler.MATERIALS",
                {"test_herb": {"name": "Test Herb"}},
            ),
        ):
            # Mock randoms
            # randint(1, 100) -> 80 (skip regen)
            # random() -> 0.1 (pass gather chance check < 0.35)
            # choices -> ["test_herb"]
            # random() again -> 0.9 (no extra item variance < 0.20)

            # side_effect:
            # 1. resolve_non_combat: 80 (Fail Regen, > 70)
            # 2. _perform_wild_gathering: 1 (Success Gather, <= 35)
            with (
                patch("random.randint", side_effect=[80, 1]),
                patch("random.random", side_effect=[0.9]),
                patch("random.choices", return_value=["test_herb"]),
            ):
                result = self.event_handler.resolve_non_combat(
                    context=self.context, location_id="test_loc", regen_chance=70
                )

                self.assertIn("loot", result)
                # Quantity check: Base 1 + (Luck 50 / 25) = 1 + 2 = 3. Cap is 3.
                self.assertEqual(result["loot"], {"test_herb": 3})
                self.assertTrue(any("Test Herb (x3)" in log for log in result["log"]))

    def test_wild_gathering_no_gatherables(self):
        """Test fallback when location has no gatherables."""

        mock_locations = {"empty_loc": {"gatherables": []}}

        with patch("game_systems.adventure.event_handler.LOCATIONS", mock_locations):
            # Should fallback to default pool
            # side_effect: 80 (Fail Regen), 1 (Success Gather)
            with (
                patch("random.randint", side_effect=[80, 1]),
                patch("random.random", side_effect=[0.9]),
                patch("random.choices", return_value=["medicinal_herb"]),
            ):  # Fallback pool item
                result = self.event_handler.resolve_non_combat(
                    context=self.context, location_id="empty_loc", regen_chance=70
                )
                self.assertIn("loot", result)
                self.assertIn("medicinal_herb", result["loot"])

    def test_adventure_session_integration(self):
        """Test that AdventureSession passes location_id correctly."""
        from unittest.mock import ANY

        session = AdventureSession(
            self.db, self.quest_system, self.inventory_manager, self.discord_id
        )
        session.events = MagicMock()
        session.events.resolve_non_combat.return_value = {"log": [], "dead": False}

        # Mock _fetch_session_context to return our context
        session._fetch_session_context = MagicMock(return_value=self.context)

        session.location_id = "test_forest"

        # Mock LOCATIONS
        with patch(
            "game_systems.adventure.adventure_session.LOCATIONS",
            {"test_forest": {"name": "Forest"}},
        ):
            # Force non-combat
            with patch("random.randint", return_value=10):
                session.simulate_step()

                # Check call args (weather and event_type are now passed by simulate_step)
                session.events.resolve_non_combat.assert_called_with(
                    context=self.context,
                    location_id="test_forest",
                    regen_chance=70,
                    location_name="Forest",
                    weather=ANY,
                    event_type=ANY,
                )


if __name__ == "__main__":
    unittest.main()
