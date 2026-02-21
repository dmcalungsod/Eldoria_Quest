import os
import time
import unittest

from database.database_manager import DatabaseManager
from game_systems.adventure.combat_handler import CombatHandler
from game_systems.items.consumable_manager import ConsumableManager
from game_systems.player.player_stats import PlayerStats

TEST_DB = "test_buffs.db"


class TestBuffSystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        # Initialize DB
        self.db = DatabaseManager(TEST_DB)
        with self.db.get_connection() as conn:
            # Create minimal schema
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (discord_id INTEGER PRIMARY KEY, name TEXT, class_id INTEGER, level INTEGER, experience INTEGER, exp_to_next INTEGER, current_hp INTEGER, current_mp INTEGER, vestige_pool INTEGER, aurum INTEGER, race TEXT, gender TEXT);
            CREATE TABLE IF NOT EXISTS stats (discord_id INTEGER PRIMARY KEY, stats_json TEXT);
            CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER, item_key TEXT, item_name TEXT, item_type TEXT, count INTEGER, rarity TEXT, slot TEXT, item_source_table TEXT, equipped INTEGER);
            CREATE TABLE IF NOT EXISTS active_buffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER,
                buff_id TEXT,
                name TEXT,
                stat TEXT,
                amount REAL,
                end_time TEXT
            );
            CREATE TABLE IF NOT EXISTS player_skills (id INTEGER PRIMARY KEY, discord_id INTEGER, skill_key TEXT, skill_level INTEGER, skill_exp REAL);
            CREATE TABLE IF NOT EXISTS skills (key_id TEXT PRIMARY KEY, type TEXT, name TEXT, mp_cost INTEGER, power_multiplier REAL, heal_power INTEGER, buff_data TEXT);
            CREATE TABLE IF NOT EXISTS global_boosts (boost_key TEXT PRIMARY KEY, multiplier REAL, end_time TEXT);
            CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, name TEXT, description TEXT);
            """)

            # Insert a class
            conn.execute("INSERT INTO classes (id, name, description) VALUES (1, 'Warrior', 'Strong')")

        self.discord_id = 12345
        self.db.create_player(self.discord_id, "TestHero", 1, {"STR": 10, "END": 10}, 100, 50)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_buff_lifecycle(self):
        # Add buff
        self.db.add_active_buff(self.discord_id, "test_buff", "Test Buff", "STR", 5, 2)

        buffs = self.db.get_active_buffs(self.discord_id)
        self.assertEqual(len(buffs), 1)
        self.assertEqual(buffs[0]["stat"], "STR")
        self.assertEqual(buffs[0]["amount"], 5)

        # Wait for expiry
        time.sleep(2.1)

        # Should still return empty if filtered by time
        buffs = self.db.get_active_buffs(self.discord_id)
        self.assertEqual(len(buffs), 0)

        # Clean
        self.db.clear_expired_buffs(self.discord_id)

        with self.db.get_connection() as conn:
            count = conn.execute("SELECT count(*) FROM active_buffs").fetchone()[0]
            self.assertEqual(count, 0)

    def test_consumable_buff_application(self):
        # Insert a buff item into inventory
        # "strength_brew" has STR+3, 120s
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO inventory (discord_id, item_key, item_name, item_type, count) VALUES (?, ?, ?, ?, ?)",
                (self.discord_id, "strength_brew", "Brew", "consumable", 1),
            )
            inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        cm = ConsumableManager(self.db)
        success, msg = cm.use_item(self.discord_id, inv_id)

        self.assertTrue(success)
        self.assertIn("Buffs applied", msg)
        self.assertIn("STR +3", msg)

        buffs = self.db.get_active_buffs(self.discord_id)
        self.assertEqual(len(buffs), 1)
        self.assertEqual(buffs[0]["stat"], "STR")
        self.assertEqual(buffs[0]["amount"], 3)

    def test_combat_handler_applies_buff(self):
        # Add buff manually
        self.db.add_active_buff(self.discord_id, "buff_1", "Strong", "STR", 50, 3600)

        # Monkeypatch PlayerStats.add_bonus_stat to verify call
        original_add_bonus = PlayerStats.add_bonus_stat
        log = []

        def mock_add_bonus(self, stat, amount):
            log.append((stat, amount))
            original_add_bonus(self, stat, amount)

        PlayerStats.add_bonus_stat = mock_add_bonus

        try:
            ch = CombatHandler(self.db, self.discord_id)

            # Need valid vitals
            self.db.set_player_vitals(self.discord_id, 100, 50)

            # We call resolve_turn with a dummy monster
            monster = {"HP": 10, "ATK": 1, "DEF": 0, "name": "Dummy", "skills": [], "drops": []}
            report = ch.create_empty_battle_report()

            # Use Manual Mode (context=None)
            ch.resolve_turn(monster, report, persist_vitals=False)

            # Verify log
            self.assertIn(("STR", 50.0), log)

        finally:
            PlayerStats.add_bonus_stat = original_add_bonus


if __name__ == "__main__":
    unittest.main()
