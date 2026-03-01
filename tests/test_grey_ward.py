# Mock pymongo before importing anything that uses it
import sys
import unittest
from unittest.mock import MagicMock

# Create a mock for pymongo
mock_pymongo = MagicMock()
mock_pymongo.errors = MagicMock()
mock_pymongo.errors.DuplicateKeyError = Exception
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_pymongo.errors

from game_systems.data.factions import FACTIONS  # noqa: E402
from game_systems.guild_system.faction_system import FactionSystem  # noqa: E402


class TestGreyWard(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = FactionSystem(self.mock_db)
        self.discord_id = 12345
        self.faction_id = "grey_ward"

    def test_grey_ward_exists(self):
        """Verify 'Grey Ward' exists in FACTIONS and has correct properties."""
        if self.faction_id not in FACTIONS:
            self.fail(f"The Grey Ward faction ({self.faction_id}) is missing from FACTIONS.")

        faction = FACTIONS[self.faction_id]
        self.assertEqual(faction["name"], "Grey Ward")
        self.assertEqual(faction["emoji"], "⚕️")
        self.assertIn("pragmatic order of alchemists", faction["description"])

        # Verify Ranks (Updated to match Alchemist Lore)
        ranks = faction["ranks"]
        self.assertEqual(ranks[1]["title"], "Scavenger")
        self.assertEqual(ranks[2]["title"], "Mixologist")
        self.assertEqual(ranks[3]["title"], "Apothecary")
        self.assertEqual(ranks[4]["title"], "Chirurgeon")
        self.assertEqual(ranks[5]["title"], "Transmuter")

        # Verify Rewards
        self.assertEqual(ranks[2]["reward"]["key"], "bitter_panacea")
        self.assertEqual(ranks[2]["reward"]["amount"], 3)
        self.assertEqual(ranks[3]["reward"]["key"], "phial_of_vitriol")
        self.assertEqual(ranks[3]["reward"]["amount"], 3)
        self.assertEqual(ranks[4]["reward"]["key"], "gathering_boost")
        self.assertEqual(ranks[4]["reward"]["value"], 0.1)
        self.assertEqual(ranks[5]["reward"]["value"], "Transmuter")

        # Verify Interests
        self.assertEqual(faction["interests"]["gathering"], 1.5)
        self.assertEqual(faction["interests"]["crafting"], 1.5)
        self.assertIn("Plant", faction["interests"]["monster_types"])
        self.assertIn("Slime", faction["interests"]["monster_types"])
        self.assertNotIn("Undead", faction["interests"]["monster_types"])

        # Verify Favored Locations
        favored = faction["favored_locations"]
        self.assertIn("whispering_thicket", favored)
        self.assertIn("deepgrove_roots", favored)
        self.assertIn("shrouded_fen", favored)
        self.assertIn("forgotten_ossuary", favored)
        self.assertIn("the_ashlands", favored)

    def test_join_grey_ward(self):
        """Test joining Grey Ward."""
        self.mock_db.get_player_faction_data.return_value = None

        success, msg = self.system.join_faction(self.discord_id, self.faction_id)
        self.assertTrue(success)
        self.assertIn("Grey Ward", msg)

    def test_grey_ward_reputation_gain(self):
        """Test reputation gain logic for The Grey Ward (favored locations)."""
        # Manually inject the faction into the system's knowledge if needed,
        # but the system reads directly from FACTIONS which we imported.

        # Mock database response to return Grey Ward membership
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": self.faction_id,
            "reputation": 0,
        }

        # We need to ensure get_player_faction uses the FACTIONS dict which now contains grey_ward (if we added it).
        # Since FACTIONS is imported at module level in faction_system.py,
        # changes to FACTIONS in data/factions.py will be reflected if we reload or if it's dynamic.
        # But here we are testing against the actual code.

        # Base: 30 mins -> 6 rep
        # Multiplier: 1.0 (base) + 0.0 (exploration not in interests) = 1.0
        # Favored Location Bonus: +0.5
        # Total Multiplier: 1.5
        # Expected: 6 * 1.5 = 9

        self.mock_db.update_faction_reputation.return_value = 9

        logs = self.system.grant_reputation_for_adventure(self.discord_id, 30, "whispering_thicket")

        self.mock_db.update_faction_reputation.assert_called_with(self.discord_id, 9)
        self.assertTrue(any("Favored Location Bonus" in log for log in logs))

    def test_grey_ward_reputation_gain_non_favored(self):
        """Test reputation gain in non-favored location."""
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": self.faction_id,
            "reputation": 0,
        }

        # Base: 30 mins -> 6 rep
        # Multiplier: 1.0 (base)
        # Expected: 6 * 1.0 = 6

        self.mock_db.update_faction_reputation.return_value = 6

        logs = self.system.grant_reputation_for_adventure(self.discord_id, 30, "forest_outskirts")

        self.mock_db.update_faction_reputation.assert_called_with(self.discord_id, 6)
        self.assertFalse(any("Favored Location Bonus" in log for log in logs))


if __name__ == "__main__":
    unittest.main()
