"""
Extended Database Tests for Eldoria Quest
-----------------------------------------
Covers additional database operations not included in test_database.py.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import datetime

# Mock pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager


class TestDatabaseManagerExtended(unittest.TestCase):
    def setUp(self):
        # Mock the MongoClient to prevent actual DB connection
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Bridge attribute access (db.players) and item access (db['players'])
        def get_collection(name):
            return getattr(self.mock_db, name)

        self.mock_db.__getitem__.side_effect = get_collection

        # Patch MongoClient in DatabaseManager
        self.mongo_patcher = patch("database.database_manager.MongoClient", return_value=self.mock_client)
        self.mongo_patcher.start()

        # Initialize DatabaseManager (singleton reset)
        DatabaseManager._instance = None
        self.db = DatabaseManager()

    def tearDown(self):
        self.mongo_patcher.stop()
        DatabaseManager._instance = None

    # ============================================================
    # PLAYER VITALS & REGEN
    # ============================================================

    def test_apply_passive_regen(self):
        # Mock current time
        mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0)
        with patch("game_systems.core.world_time.WorldTime.now", return_value=mock_now):
            # 1. Setup Player State (last regen 1 hour ago)
            last_regen = (mock_now - datetime.timedelta(hours=1)).isoformat()
            self.mock_db.players.find_one.return_value = {
                "current_hp": 50,
                "current_mp": 20,
                "last_regen_time": last_regen
            }

            # 2. Mock Stats (Max HP/MP)
            # returning a stats json
            self.mock_db.stats.find_one.return_value = {
                "stats_json": '{"STR": 10}'
            }

            # 3. Mock PlayerStats class
            with patch("game_systems.player.player_stats.PlayerStats") as MockPlayerStats:
                mock_stats_instance = MagicMock()
                mock_stats_instance.max_hp = 100
                mock_stats_instance.max_mp = 100
                MockPlayerStats.from_dict.return_value = mock_stats_instance

                # Execute
                hp_gain, mp_gain = self.db.apply_passive_regen(12345)

                # Verify
                # 1 hour elapsed.
                # HP Regen: 5% of 100 = 5
                # MP Regen: 10% of 100 = 10
                self.assertEqual(hp_gain, 5)
                self.assertEqual(mp_gain, 10)

                # Check update called
                self.assertTrue(self.mock_db.players.update_one.called)
                args, _ = self.mock_db.players.update_one.call_args
                self.assertEqual(args[1]["$set"]["current_hp"], 55) # 50 + 5
                self.assertEqual(args[1]["$set"]["current_mp"], 30) # 20 + 10

    def test_update_player_vitals_delta(self):
        # Test positive delta
        self.db.update_player_vitals_delta(12345, hp_delta=10, mp_delta=-5, max_hp=100, max_mp=50)

        self.assertTrue(self.mock_db.players.update_one.called)
        args, _ = self.mock_db.players.update_one.call_args
        self.assertEqual(args[0], {"discord_id": 12345})
        pipeline = args[1]
        self.assertIsInstance(pipeline, list)
        self.assertIn("$set", pipeline[0])

    # ============================================================
    # SKILLS
    # ============================================================

    def test_get_player_skills(self):
        # Mock skill cache to avoid DB lookup for definitions
        self.db._skill_cache = {
            "fireball": {"key_id": "fireball", "name": "Fireball", "type": "Active"}
        }

        # Mock player skills DB return
        mock_skills = [
            {"discord_id": 12345, "skill_key": "fireball", "skill_level": 2, "skill_exp": 100}
        ]
        self.mock_db.player_skills.find.return_value = mock_skills

        # Test
        skills = self.db.get_player_skills(12345)

        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "Fireball")
        self.assertEqual(skills[0]["skill_level"], 2)

    def test_learn_skill_success(self):
        # Mock checks
        self.db.player_has_skill = MagicMock(return_value=False)
        self.mock_db.players.update_one.return_value.modified_count = 1  # Successful vestige deduction

        # Test
        success, message = self.db.learn_skill(12345, "fireball", cost=100)

        self.assertTrue(success)
        self.assertEqual(message, "Skill Learned!")
        self.assertTrue(self.mock_db.player_skills.insert_one.called)

    def test_learn_skill_insufficient_vestige(self):
        self.db.player_has_skill = MagicMock(return_value=False)
        self.mock_db.players.update_one.return_value.modified_count = 0  # Failed deduction

        success, message = self.db.learn_skill(12345, "fireball", cost=100)

        self.assertFalse(success)
        self.assertEqual(message, "Insufficient Vestige.")
        self.assertFalse(self.mock_db.player_skills.insert_one.called)

    def test_upgrade_skill_success(self):
        # Mock checks
        self.mock_db.player_skills.find_one.return_value = {"skill_level": 1}

        # Mock vestige deduction success
        # Note: update_one is called twice (deduct vestige, update skill).
        # We need side_effect to return modified_count=1 for both calls.
        update_result = MagicMock()
        update_result.modified_count = 1
        self.mock_db.players.update_one.return_value = update_result
        self.mock_db.player_skills.update_one.return_value = update_result

        success, message, new_level = self.db.upgrade_skill(12345, "fireball", cost=50)

        self.assertTrue(success)
        self.assertEqual(new_level, 2)
        # Verify calls
        self.mock_db.players.update_one.assert_called() # Vestige deduction
        self.mock_db.player_skills.update_one.assert_called() # Level up

    # ============================================================
    # ADVENTURE
    # ============================================================

    def test_insert_adventure_session(self):
        self.db.insert_adventure_session(
            discord_id=12345,
            location_id="forest",
            start_time="2023-01-01T12:00:00",
            end_time="2023-01-01T13:00:00",
            duration_minutes=60
        )

        # Should delete existing first, then insert
        self.assertTrue(self.mock_db.adventure_sessions.delete_many.called)
        self.assertTrue(self.mock_db.adventure_sessions.insert_one.called)
        args, _ = self.mock_db.adventure_sessions.insert_one.call_args
        self.assertEqual(args[0]["location_id"], "forest")
        self.assertEqual(args[0]["status"], "in_progress")

    def test_update_adventure_session_optimistic(self):
        # Successful update
        self.mock_db.adventure_sessions.update_one.return_value.modified_count = 1

        success = self.db.update_adventure_session(
            discord_id=12345,
            logs="[]",
            loot_collected="{}",
            active=1,
            active_monster_json=None,
            previous_version=1,
            steps_completed=5
        )

        self.assertTrue(success)
        args, _ = self.mock_db.adventure_sessions.update_one.call_args
        self.assertEqual(args[1]["$set"]["version"], 2)

    def test_end_adventure_session(self):
        self.db.end_adventure_session(12345)

        self.mock_db.adventure_sessions.update_many.assert_called_with(
            {"discord_id": 12345},
            {"$set": {"active": 0}}
        )

    # ============================================================
    # INVENTORY EXTENDED
    # ============================================================

    def test_remove_inventory_item(self):
        # Mock total count
        # Mock aggregate return for get_inventory_item_count
        self.mock_db.inventory.aggregate.return_value = [{"total": 5}]

        # Mock find stacks
        stacks = [
            {"id": 101, "count": 2, "equipped": 0},
            {"id": 102, "count": 3, "equipped": 0}
        ]
        # Cursor mock
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = stacks
        self.mock_db.inventory.find.return_value = mock_cursor

        # Test removing 4 items
        # Should delete stack 101 (2 items), update stack 102 (-2 items, 1 left)
        success = self.db.remove_inventory_item(12345, "potion", 4)

        self.assertTrue(success)
        self.mock_db.inventory.delete_one.assert_called_with({"id": 101})
        self.mock_db.inventory.update_one.assert_called_with({"id": 102}, {"$inc": {"count": -2}})

    def test_consume_item_atomic(self):
        # Success case
        self.mock_db.inventory.find_one_and_update.return_value = {"id": 101, "count": 0}

        success = self.db.consume_item_atomic(101, 1)
        self.assertTrue(success)
        # Should try to delete if count reached 0
        self.mock_db.inventory.delete_one.assert_called_with({"id": 101, "count": 0})

    # ============================================================
    # TOURNAMENTS
    # ============================================================

    def test_create_tournament(self):
        # Mock counter
        self.mock_db.counters.find_one_and_update.return_value = {"seq": 1}

        t_id = self.db.create_tournament("PvP", "start", "end")

        self.assertEqual(t_id, 1)
        self.assertTrue(self.mock_db.tournaments.insert_one.called)
        args, _ = self.mock_db.tournaments.insert_one.call_args
        # Verify the renamed parameter is used correctly
        self.assertEqual(args[0]["type"], "PvP")

    def test_get_active_tournament_caching(self):
        # First call: fetch from DB
        mock_t = {"id": 1, "type": "PvP", "active": 1}
        self.mock_db.tournaments.find_one.return_value = mock_t

        t1 = self.db.get_active_tournament()
        self.assertEqual(t1, mock_t)
        self.mock_db.tournaments.find_one.assert_called_once()

        # Second call: should be cached (within 60s)
        t2 = self.db.get_active_tournament()
        self.assertEqual(t2, mock_t)
        self.mock_db.tournaments.find_one.assert_called_once() # Call count should not increase

    def test_update_tournament_score(self):
        self.db.update_tournament_score(12345, 1, 100)

        self.mock_db.tournament_scores.update_one.assert_called_with(
            {"discord_id": 12345, "tournament_id": 1},
            {"$inc": {"score": 100}},
            upsert=True
        )

    # ============================================================
    # WORLD EVENTS
    # ============================================================

    def test_world_event_lifecycle(self):
        # Set event
        self.db.set_active_world_event("invasion", "start", "end", {"power": 10})

        # Verify deactivate old and insert new
        self.assertTrue(self.mock_db.world_events.update_many.called) # end_active_world_event
        self.assertTrue(self.mock_db.world_events.insert_one.called)

        # Get event (mock return)
        mock_event = {"type": "invasion", "active": 1}
        self.mock_db.world_events.find_one.return_value = mock_event

        event = self.db.get_active_world_event()
        self.assertEqual(event, mock_event)

    # ============================================================
    # EQUIPMENT SETS
    # ============================================================

    def test_save_equipment_set(self):
        items = {"main_hand": {"item_key": "sword"}}
        self.db.save_equipment_set(12345, "MySet", items)

        self.mock_db.equipment_sets.update_one.assert_called()
        args, _ = self.mock_db.equipment_sets.update_one.call_args
        self.assertEqual(args[1]["$set"]["name"], "MySet")

    def test_get_equipment_sets(self):
        self.mock_db.equipment_sets.find.return_value = [{"name": "Set1"}, {"name": "Set2"}]

        sets = self.db.get_equipment_sets(12345)
        self.assertEqual(len(sets), 2)

    # ============================================================
    # FACTIONS
    # ============================================================

    def test_set_player_faction(self):
        self.db.set_player_faction(12345, "faction_a")

        self.mock_db.player_factions.update_one.assert_called_with(
            {"discord_id": 12345},
            {
                "$set": {
                    "faction_id": "faction_a",
                    "reputation": 0,
                    # We can't easily match the exact time string in mock, so we check keys
                    "join_date": unittest.mock.ANY
                }
            },
            upsert=True
        )

    def test_update_faction_reputation(self):
        self.mock_db.player_factions.find_one_and_update.return_value = {"reputation": 50}

        new_rep = self.db.update_faction_reputation(12345, 10)
        self.assertEqual(new_rep, 50)


if __name__ == "__main__":
    unittest.main()
