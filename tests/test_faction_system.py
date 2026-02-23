# Mock pymongo before importing anything that uses it
import sys
import unittest
from unittest.mock import MagicMock

sys.modules["pymongo"] = MagicMock()

from game_systems.guild_system.faction_system import FactionSystem  # noqa: E402


class TestFactionSystem(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.system = FactionSystem(self.mock_db)
        self.discord_id = 12345

    def test_join_faction_success(self):
        self.mock_db.get_player_faction_data.return_value = None

        success, msg = self.system.join_faction(self.discord_id, "pathfinders")

        self.assertTrue(success)
        self.assertIn("joined", msg)
        self.mock_db._col.return_value.insert_one.assert_called_once()

    def test_join_faction_already_member(self):
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "pathfinders"
        }

        success, msg = self.system.join_faction(self.discord_id, "iron_vanguard")

        self.assertFalse(success)
        self.assertIn("already a member", msg)

    def test_join_faction_invalid_id(self):
        success, msg = self.system.join_faction(self.discord_id, "invalid_faction")
        self.assertFalse(success)

    def test_leave_faction(self):
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "pathfinders"
        }

        success, msg = self.system.leave_faction(self.discord_id)

        self.assertTrue(success)
        self.mock_db.leave_faction.assert_called_once_with(self.discord_id)

    def test_add_reputation_simple(self):
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "pathfinders",
            "reputation": 100,
        }
        self.mock_db.update_faction_reputation.return_value = 200

        success, msg, ranks = self.system.add_reputation(self.discord_id, 100)

        self.assertTrue(success)
        self.assertEqual(len(ranks), 0)

    def test_add_reputation_rank_up(self):
        # Initial: 100 rep (Tier 1)
        # Add 400 -> 500 rep (Tier 2, Scout)
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "pathfinders",
            "reputation": 100,
        }

        # Simulate update returning new total
        self.mock_db.update_faction_reputation.return_value = 500

        success, msg, ranks = self.system.add_reputation(self.discord_id, 400)

        self.assertTrue(success)
        # Expecting Rank Up message AND Reward message
        self.assertGreaterEqual(len(ranks), 1)
        self.assertTrue(any("Scout" in r for r in ranks))
        # Verify reward claim
        self.mock_db.add_inventory_item.assert_called_once()

    def test_grant_reputation_for_kill(self):
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "iron_vanguard",  # Likes boss kills
            "reputation": 0,
        }

        monster_data = {"tier": "Boss", "name": "Big Bad"}

        # Should call add_reputation
        # We need to mock add_reputation or just check the DB call it makes
        # Since add_reputation calls update_faction_reputation, we can check that.

        # Let's trust logic calls add_reputation
        self.mock_db.update_faction_reputation.return_value = 100  # Arbitrary return

        logs = self.system.grant_reputation_for_kill(self.discord_id, monster_data)

        # Iron Vanguard: Base 50 for Boss + multiplier 2.0 = 100 rep
        # Logic: int(50 * (1.0 + 2.0)) = 150 rep (Wait, check logic)

        # My logic was:
        # base_rep = 50 (Boss)
        # multiplier = 1.0 + interests.get("boss_kills", 0.0) -> 1.0 + 2.0 = 3.0
        # final = 50 * 3.0 = 150

        self.mock_db.update_faction_reputation.assert_called_with(self.discord_id, 150)

    def test_grant_reputation_for_adventure(self):
        self.mock_db.get_player_faction_data.return_value = {
            "faction_id": "pathfinders",
            "reputation": 0,
        }

        # Duration 30 mins -> 6 base rep
        # Multiplier: 1.0 + 1.5 (exploration) = 2.5
        # Final: 6 * 2.5 = 15

        self.mock_db.update_faction_reputation.return_value = 15

        logs = self.system.grant_reputation_for_adventure(
            self.discord_id, 30, "any_loc"
        )

        self.mock_db.update_faction_reputation.assert_called_with(self.discord_id, 15)


if __name__ == "__main__":
    unittest.main()
