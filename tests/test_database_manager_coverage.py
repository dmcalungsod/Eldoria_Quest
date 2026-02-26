import datetime
import unittest
from unittest.mock import MagicMock, patch

from pymongo.errors import DuplicateKeyError

from database.database_manager import DatabaseManager


class TestDatabaseManagerCoverage(unittest.TestCase):
    def setUp(self):
        # Reset Singleton
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        # Mock MongoClient
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_client.__getitem__.return_value = self.mock_db

        # Patch MongoClient used in __init__
        with patch('database.database_manager.MongoClient', return_value=self.mock_client):
            self.db = DatabaseManager(mongo_uri="mongodb://test:27017", db_name="test_db")

        # Mock collections
        self.mock_players = MagicMock()
        self.mock_stats = MagicMock()
        self.mock_inventory = MagicMock()
        self.mock_global_boosts = MagicMock()
        self.mock_player_skills = MagicMock()

        def get_col(name):
            if name == "players":
                return self.mock_players
            if name == "stats":
                return self.mock_stats
            if name == "inventory":
                return self.mock_inventory
            if name == "global_boosts":
                return self.mock_global_boosts
            if name == "player_skills":
                return self.mock_player_skills
            return MagicMock()

        self.db._col = MagicMock(side_effect=get_col)

    def tearDown(self):
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def test_get_combat_context_bundle_json_error(self):
        """Test error handling when stats_json is malformed."""
        self.mock_players.aggregate.return_value = [{
            "discord_id": 123,
            "stats_docs": [{"stats_json": "{invalid_json"}],
            "buffs": [],
            "player_skills": [],
            "active_session": []
        }]

        # Should not raise exception
        result = self.db.get_combat_context_bundle(123)
        self.assertIsNotNone(result)
        self.assertEqual(result["stats"], {})

    def test_get_profile_bundle_json_error(self):
        """Test error handling when stats_json is malformed in profile bundle."""
        self.mock_players.aggregate.return_value = [{
            "discord_id": 123,
            "stats_docs": [{"stats_json": "{invalid_json"}],
            "guild_docs": [],
            "name": "TestUser"
        }]

        result = self.db.get_profile_bundle(123)
        self.assertIsNotNone(result)
        self.assertEqual(result["stats"], {})

    def test_get_player_stats_json_error(self):
        """Test error handling in get_player_stats_json."""
        self.mock_stats.find_one.return_value = {"stats_json": "{bad"}
        result = self.db.get_player_stats_json(123)
        self.assertEqual(result, {})

    @patch('game_systems.core.world_time.WorldTime.now')
    def test_apply_passive_regen_missing_time(self, mock_now):
        """Test migration when last_regen_time is missing."""
        mock_now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
        self.mock_players.find_one.return_value = {"current_hp": 10, "current_mp": 10} # No last_regen_time

        hp, mp = self.db.apply_passive_regen(123)

        self.assertEqual(hp, 0)
        self.assertEqual(mp, 0)
        self.mock_players.update_one.assert_called_with(
            {"discord_id": 123},
            {"$set": {"last_regen_time": "2023-01-01T12:00:00"}}
        )

    @patch('game_systems.core.world_time.WorldTime.now')
    def test_apply_passive_regen_malformed_time(self, mock_now):
        """Test handling of malformed last_regen_time."""
        mock_now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
        self.mock_players.find_one.return_value = {
            "current_hp": 10,
            "current_mp": 10,
            "last_regen_time": "invalid-iso-format"
        }

        hp, mp = self.db.apply_passive_regen(123)

        self.assertEqual(hp, 0)
        self.assertEqual(mp, 0)
        self.mock_players.update_one.assert_called()

    @patch('game_systems.core.world_time.WorldTime.now')
    def test_apply_passive_regen_short_duration(self, mock_now):
        """Test that short durations don't trigger regen."""
        now = datetime.datetime(2023, 1, 1, 12, 0, 30) # 30 seconds later
        mock_now.return_value = now
        last_regen = datetime.datetime(2023, 1, 1, 12, 0, 0).isoformat()

        self.mock_players.find_one.return_value = {
            "current_hp": 10,
            "current_mp": 10,
            "last_regen_time": last_regen
        }

        hp, mp = self.db.apply_passive_regen(123)
        self.assertEqual(hp, 0)
        self.assertEqual(mp, 0)

    @patch('game_systems.core.world_time.WorldTime.now')
    def test_apply_passive_regen_calc_error(self, mock_now):
        """Test error in stats calculation during regen."""
        now = datetime.datetime(2023, 1, 1, 13, 0, 0) # 1 hour later
        mock_now.return_value = now
        last_regen = datetime.datetime(2023, 1, 1, 12, 0, 0).isoformat()

        self.mock_players.find_one.return_value = {
            "current_hp": 10,
            "current_mp": 10,
            "last_regen_time": last_regen
        }

        # Mock get_player_stats_json to return empty or cause error in PlayerStats.from_dict
        # Here we rely on PlayerStats.from_dict raising exception if dict is empty/invalid
        # Or simpler, we mock get_player_stats_json to return None
        self.db.get_player_stats_json = MagicMock(return_value=None)

        hp, mp = self.db.apply_passive_regen(123)
        self.assertEqual(hp, 0)
        self.assertEqual(mp, 0)

    def test_add_inventory_item_bulk_split(self):
        """Test adding item that needs to be split into new stacks."""
        # Setup: item with stack limit 5. Add 7.
        # Inventory not full.
        # existing: none.

        self.db.find_stackable_item = MagicMock(return_value=None)
        self.db.get_inventory_slot_count = MagicMock(return_value=0)
        self.db.calculate_inventory_limit = MagicMock(return_value=20)

        # Mock counters
        self.db._col("counters").find_one_and_update.return_value = {"seq": 10}

        # Logic is: remainder = 7. max_stack=5 (consumable)
        # needed_new_slots = ceil(7/5) = 2.

        result = self.db.add_inventory_item(
            discord_id=123,
            item_key="potion",
            item_name="Potion",
            item_type="consumable",
            rarity="common",
            amount=7
        )

        self.assertTrue(result)
        self.mock_inventory.insert_many.assert_called_once()
        args = self.mock_inventory.insert_many.call_args[0][0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0]["count"], 5)
        self.assertEqual(args[1]["count"], 2)

    def test_add_inventory_item_full(self):
        """Test failure when inventory is full."""
        self.db.find_stackable_item = MagicMock(return_value=None)
        self.db.get_inventory_slot_count = MagicMock(return_value=20)
        self.db.calculate_inventory_limit = MagicMock(return_value=20)

        result = self.db.add_inventory_item(
            discord_id=123,
            item_key="potion",
            item_name="Potion",
            item_type="consumable",
            rarity="common",
            amount=1
        )
        self.assertFalse(result)

    def test_add_inventory_items_bulk_partial_fail(self):
        """Test bulk add where some items fail due to space."""
        # 1 slot available. Try to add 2 stacks worth of items.
        self.db.get_inventory_slot_count = MagicMock(return_value=19)
        self.db.calculate_inventory_limit = MagicMock(return_value=20)

        items = [
            {"item_key": "p1", "item_name": "P1", "item_type": "consumable", "rarity": "c", "amount": 10}
        ]
        # Consumable stack=5. Amount=10 -> 2 stacks.
        # Only 1 slot avail.

        failed = self.db.add_inventory_items_bulk(123, items)

        # It should fail completely for that item group if it can't fit all new stacks?
        # Logic says: if needed_stacks <= available_slots: queue inserts. else: failed_items.append.
        # So yes, it fails completely for that item.

        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["item_key"], "p1")
        self.assertEqual(failed[0]["reason"], "Inventory Full")

    def test_purchase_item_refund_on_inventory_full(self):
        """Test refund when inventory add fails."""
        self.db.deduct_aurum = MagicMock(return_value=100) # New balance
        self.db.add_inventory_item = MagicMock(return_value=False) # Failed
        self.db.get_player_field = MagicMock(return_value=200)

        success, msg, bal = self.db.purchase_item(123, "k", {"name": "n", "rarity": "c"}, 50)

        self.assertFalse(success)
        self.assertEqual(msg, "Inventory Full.")
        self.assertEqual(bal, 150) # 100 + 50
        self.mock_players.update_one.assert_called_with(
            {"discord_id": 123},
            {"$inc": {"aurum": 50}}
        )

    def test_purchase_item_refund_on_exception(self):
        """Test refund when inventory add raises exception."""
        self.db.deduct_aurum = MagicMock(return_value=100)
        self.db.add_inventory_item = MagicMock(side_effect=Exception("Boom"))

        success, msg, bal = self.db.purchase_item(123, "k", {"name": "n", "rarity": "c"}, 50)

        self.assertFalse(success)
        self.assertEqual(msg, "System error (refunded).")
        self.assertEqual(bal, 150)

    def test_learn_skill_duplicate_refund(self):
        """Test refund when learning skill hits DuplicateKeyError."""
        self.db.player_has_skill = MagicMock(return_value=False)
        self.mock_players.update_one.return_value.modified_count = 1 # Deducted
        self.mock_player_skills.insert_one.side_effect = DuplicateKeyError("Dup")

        success, msg = self.db.learn_skill(123, "fireball", 10)

        self.assertFalse(success)
        self.assertIn("already learned", msg)
        # Verify refund
        self.mock_players.update_one.assert_called_with(
            {"discord_id": 123},
            {"$inc": {"vestige_pool": 10}}
        )

    def test_get_active_boosts_error(self):
        """Test error handling in get_active_boosts."""
        self.mock_global_boosts.find.side_effect = Exception("DB Error")
        boosts = self.db.get_active_boosts()
        self.assertEqual(boosts, [])

    def test_upgrade_skill_concurrent_level_change(self):
        """Test optimistic locking failure in upgrade_skill."""
        self.db.get_player_skill_row = MagicMock(return_value={"skill_level": 1})

        # 1. Deduct vestige succeeds
        self.mock_players.update_one.return_value.modified_count = 1

        # 2. Update skill fails (modified_count=0 because level changed)
        self.mock_player_skills.update_one.return_value.modified_count = 0

        success, msg, lvl = self.db.upgrade_skill(123, "fireball", 10)

        self.assertFalse(success)
        self.assertIn("Skill level changed", msg)
        # Verify refund
        self.mock_players.update_one.assert_called_with(
            {"discord_id": 123},
            {"$inc": {"vestige_pool": 10}}
        )

    def test_get_active_world_event_error(self):
        self.mock_db.__getitem__.return_value.find_one.side_effect = Exception("DB Error")
        # We need to access collection via _col for the mock to work if we mocked _col
        # But _col is mocked to return different mocks based on name.
        # We need to mock the specific collection 'world_events'

        mock_we = MagicMock()
        mock_we.find_one.side_effect = Exception("DB Error")

        original_side_effect = self.db._col.side_effect

        def side_effect(name):
            if name == "world_events":
                return mock_we
            return original_side_effect(name)

        self.db._col.side_effect = side_effect

        result = self.db.get_active_world_event()
        self.assertIsNone(result)

    def test_calculate_inventory_limit_error(self):
        """Test error handling in calculate_inventory_limit."""
        self.db.get_player_stats_json = MagicMock(return_value={"bad": "json"})

        with patch('game_systems.player.player_stats.PlayerStats.from_dict', side_effect=Exception("Stats Error")):
            # Assuming BASE_INVENTORY_SLOTS is 10
            limit = self.db.calculate_inventory_limit(123)
            self.assertEqual(limit, 10)

    def test_get_combat_skills_coverage(self):
        """Test get_combat_skills with various skill types."""
        self.mock_player_skills.find.return_value = [
            {"skill_key": "active_skill", "skill_level": 1},
            {"skill_key": "passive_skill", "skill_level": 1},
            {"skill_key": "unknown_skill", "skill_level": 1},
        ]

        self.db._skill_cache = {
            "active_skill": {"key_id": "active_skill", "name": "Active", "type": "Active"},
            "passive_skill": {"key_id": "passive_skill", "name": "Passive", "type": "Passive"},
        }

        skills = self.db.get_combat_skills(123)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "Active")

    def test_create_player_full_skills(self):
        """Test create_player_full inserts default skills."""
        self.db.insert_guild_member = MagicMock()

        self.db.create_player_full(
            123, "User", 1, "{}", 100, 50, "Human", "Male",
            default_skill_keys=["s1", "s2"]
        )

        self.mock_player_skills.insert_many.assert_called_once()
        args = self.mock_player_skills.insert_many.call_args[0][0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[0]["skill_key"], "s1")
