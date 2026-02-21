import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.getcwd())

# MOCK PYMONGO BEFORE IMPORT
sys.modules["pymongo"] = MagicMock()

# Now import
from game_systems.adventure import adventure_session  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402


class MockDatabaseManager:
    def __init__(self):
        self.sessions = {}
        self.players = {
            123: {
                "discord_id": 123,
                "current_hp": 100,
                "current_mp": 50,
                "class_id": 1,
                "level": 1,
                "experience": 0,
                "exp_to_next": 1000,
            }
        }
        self.stats = {
            123: {
                "stats_json": '{"STR": {"base": 10}, "END": {"base": 10}, "DEX": {"base": 10}, "MAG": {"base": 10}, "HP": {"base": 100}, "MP": {"base": 50}}'
            }
        }
        self.buffs = []
        self.boosts = []
        self.skills = []

    def get_combat_context_bundle(self, discord_id):
        # Return minimal context
        return {
            "player": self.players[discord_id],
            "stats": json.loads(self.stats[discord_id]["stats_json"]),
            "buffs": self.buffs,
            "skills": self.skills,
            "active_session": self.sessions.get(discord_id),
        }

    def get_active_adventure(self, discord_id):
        return self.sessions.get(discord_id)

    def get_active_world_event(self):
        return None

    def update_adventure_session(
        self, discord_id, logs, loot_collected, active, active_monster_json, previous_version
    ):
        if discord_id not in self.sessions:
            return False

        current = self.sessions[discord_id]
        if current.get("active") != 1:
            return False

        # Simulate MongoDB logic:
        # If previous_version is 1, we match if "version" is 1 OR if "version" is missing.
        current_ver = current.get("version") # None if missing

        match = False
        if previous_version == 1:
            if current_ver == 1 or current_ver is None:
                match = True
        else:
            if current_ver == previous_version:
                match = True

        if not match:
            return False

        self.sessions[discord_id].update({
            "discord_id": discord_id,
            "active": active,
            "logs": logs,
            "loot_collected": loot_collected,
            "active_monster_json": active_monster_json,
            "version": previous_version + 1,
        })
        return True

    def get_player_stats_json(self, discord_id):
        return json.loads(self.stats[discord_id]["stats_json"])

    def get_active_boosts(self):
        return self.boosts

    def set_player_vitals(self, discord_id, hp, mp):
        self.players[discord_id]["current_hp"] = hp
        self.players[discord_id]["current_mp"] = mp


class TestAdventureSessionConcurrency(unittest.TestCase):
    def setUp(self):
        self.db = MockDatabaseManager()
        self.user_id = 123

        # Patch LOCATIONS to ensure simulate_step proceeds
        self.locations_patcher = patch.dict(adventure_session.LOCATIONS, {"loc_1": {"name": "Test Location", "monsters": []}})
        self.locations_patcher.start()

        # Setup initial active session
        self.initial_monster = {
            "name": "Goblin",
            "HP": 100,
            "max_hp": 100,
            "level": 1,
            "tier": "Normal",
            "xp": 10,
            "drops": [],
            "atk": 10,
            "def": 0
        }

        # Create session manually in "DB"
        self.db.sessions[self.user_id] = {
            "discord_id": self.user_id,
            "location_id": "loc_1",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": json.dumps(self.initial_monster),
            "version": 1,
        }

    def tearDown(self):
        self.locations_patcher.stop()

    def test_concurrent_attacks(self):
        """
        Simulates two concurrent attack requests.
        Ensures that optimistic locking prevents the second request from overwriting the first.
        """

        # 1. Thread A reads state
        bundle_a = self.db.get_combat_context_bundle(self.user_id)
        session_a = AdventureSession(self.db, MagicMock(), MagicMock(), self.user_id, bundle_a["active_session"])

        # 2. Thread B reads state (SAME state)
        bundle_b = self.db.get_combat_context_bundle(self.user_id)
        session_b = AdventureSession(self.db, MagicMock(), MagicMock(), self.user_id, bundle_b["active_session"])

        # Mock side effect to simulate damage
        def side_effect_combat(monster, *args, **kwargs):
            monster["HP"] = 90
            return {
                "winner": None,
                "phrases": ["Hit for 10"],
                "hp_current": 100,
                "mp_current": 50,
                "monster_hp": 90,
                "turn_report": {},
                "active_boosts": {}
            }

        session_a.combat.resolve_turn = MagicMock(side_effect=side_effect_combat)
        session_b.combat.resolve_turn = MagicMock(side_effect=side_effect_combat)

        # Execute A (Should Succeed)
        result_a = session_a.simulate_step(context_bundle=bundle_a, action="attack")

        # Check DB state after A
        session_data = self.db.get_active_adventure(self.user_id)
        monster_a = json.loads(session_data["active_monster_json"])
        self.assertEqual(monster_a["HP"], 90)
        self.assertFalse(result_a.get("dead", False))

        # Execute B (Should Fail due to version mismatch)
        result_b = session_b.simulate_step(context_bundle=bundle_b, action="attack")

        # Check DB state after B (Should still be 90, not corrupted or reverted)
        session_data = self.db.get_active_adventure(self.user_id)
        monster_b = json.loads(session_data["active_monster_json"])
        self.assertEqual(monster_b["HP"], 90)

        # Verify B failed with System Error
        logs_b = result_b.get("sequence", [])
        combined_logs = "".join([str(x) for x in logs_b])
        self.assertTrue("System Error" in combined_logs or "conflict" in combined_logs,
                        f"Expected error in logs, got: {combined_logs}")

        # Verify A's version incremented
        self.assertEqual(session_data.get("version"), 2)

    def test_legacy_session_update(self):
        """
        Tests that a session WITHOUT a version field (legacy) can be successfully updated
        and migrated to version 2.
        """
        # Create a legacy session (no version field)
        legacy_user_id = 456
        self.db.players[legacy_user_id] = self.db.players[123].copy()
        self.db.players[legacy_user_id]["discord_id"] = legacy_user_id
        self.db.stats[legacy_user_id] = self.db.stats[123]

        self.db.sessions[legacy_user_id] = {
            "discord_id": legacy_user_id,
            "location_id": "loc_1",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": json.dumps(self.initial_monster),
            # NO "version" key
        }

        bundle = self.db.get_combat_context_bundle(legacy_user_id)
        session = AdventureSession(self.db, MagicMock(), MagicMock(), legacy_user_id, bundle["active_session"])

        # Verify session initialized with default version 1
        self.assertEqual(session.version, 1)

        # Mock side effect
        session.combat.resolve_turn = MagicMock(return_value={
            "winner": None,
            "phrases": ["Migrated!"],
            "hp_current": 100,
            "mp_current": 50,
            "monster_hp": 90,
            "turn_report": {},
            "active_boosts": {}
        })

        # Execute Step
        result = session.simulate_step(context_bundle=bundle, action="attack")

        self.assertFalse(result.get("dead", False))

        # Verify DB state
        session_data = self.db.get_active_adventure(legacy_user_id)
        # Should now have version 2
        self.assertEqual(session_data.get("version"), 2)
        print("Legacy migration successful: Version upgraded from None to 2.")


if __name__ == "__main__":
    unittest.main()
