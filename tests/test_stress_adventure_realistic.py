import json
import logging
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# --- MOCK MODULES AT MODULE LEVEL FOR DISCOVERY ---
# These are necessary if game_systems are imported at the top level
# of other modules, but it's cleaner to mock in setUp if possible.
# However, due to how adventure_resolution might import things,
# we may need some global mocks. We'll try to do it in setUp first,
# but if that fails, we'll put them here.

class RealisticMockDatabase:
    def __init__(self):
        self.sessions = {}
        self.players = {}
        # Pre-generate some static return data to avoid overhead during test
        self.static_context = {
            "player": {
                "current_hp": 100,
                "current_mp": 100,
                "level": 10,
                "class_id": 1,
                "experience": 500,
                "exp_to_next": 1000,
                "name": "TestPlayer",
            },
            "stats": {"HP": 100, "MP": 100, "STR": 10, "END": 10, "DEX": 10, "AGI": 10, "MAG": 10, "LCK": 10},
            "buffs": [],
            "skills": [
                {
                    "name": "Basic Attack",
                    "mp_cost": 0,
                    "description": "Simple attack",
                    "damage_scale": 1.0,
                    "type": "physical",
                    "key": "basic_attack",
                },
                {
                    "name": "Power Strike",
                    "mp_cost": 10,
                    "description": "Strong attack",
                    "damage_scale": 1.5,
                    "type": "physical",
                    "key": "power_strike",
                },
            ],
        }
        self.static_vitals = {"current_hp": 100, "current_mp": 100}

    def get_combat_context_bundle(self, discord_id):
        ctx = self.static_context.copy()
        ctx["player"] = self.static_context["player"].copy()
        ctx["player"]["discord_id"] = discord_id
        return ctx

    def get_active_boosts(self):
        return []

    def get_player_vitals(self, discord_id):
        return self.static_vitals.copy()

    def update_player_vitals_delta(self, discord_id, _dhp, _dmp, _mhp, _mmp):
        return True

    def update_adventure_session(self, discord_id, **_kwargs):
        return True

    def update_adventure_status(self, discord_id, _status):
        return True

    def set_player_vitals(self, discord_id, _hp, _mp):
        return True

    def add_active_buffs_bulk(self, discord_id, _buffs):
        return True

    def add_title(self, discord_id, _title):
        return True

    def get_player_quests(self, discord_id):
        return []

    def update_progress(self, discord_id, _quest_id, _obj_type, _task, _amount):
        return True

    def get_active_tournament(self):
        return None

    def get_active_world_event(self):
        return None

    def get_player_field(self, discord_id, field):
        if field == "level":
            return 10
        return None

    def get_player_stats_json(self, discord_id):
        return self.static_context["stats"]

    def get_player(self, discord_id):
        return self.static_context["player"]

    def get_combat_skills(self, discord_id):
        return self.static_context["skills"]

    def clear_expired_buffs(self, discord_id):
        pass

    def get_active_buffs(self, discord_id):
        return []

    def increment_guild_stat(self, discord_id, field, _amount=1):
        return True

    def increment_specific_monster_kill(self, discord_id, _monster_name, _amount=1):
        return True

    def get_stat_exp_row(self, discord_id):
        # Return mock row for stat exp
        return {
            "stats_json": json.dumps(
                {
                    "STR": {"base": 10},
                    "DEX": {"base": 10},
                    "INT": {"base": 10},
                    "END": {"base": 10},
                    "LCK": {"base": 10},
                    "AGI": {"base": 10},
                }
            ),
            "str_exp": 0,
            "end_exp": 0,
            "dex_exp": 0,
            "agi_exp": 0,
            "mag_exp": 0,
            "lck_exp": 0,
        }

    def update_stat_exp(self, *_args, **_kwargs):
        return True

    def get_skill_with_definition(self, discord_id, skill_key):
        return {"skill_level": 1, "skill_exp": 0, "name": skill_key}

    def update_player_skill(self, *_args, **_kwargs):
        return True

    def get_guild_member_field(self, discord_id, field):
        if field == "rank":
            return "F"
        return None

    def add_inventory_item(self, *_args, **_kwargs):
        return True

    def update_player_mixed(self, *_args, **_kwargs):
        return True

    def end_adventure_session(self, *_args, **_kwargs):
        return True

    def _col(self, _name):
        # Return a mock collection that can handle find()
        mock_col = MagicMock()
        mock_col.find.return_value = []  # Return empty list for find
        mock_col.find_one.return_value = None
        return mock_col


class TestStressAdventureRealistic(unittest.TestCase):
    def setUp(self):
        # We need to mock discord and pymongo in sys.modules *before* importing game_systems
        # However, because tests are run in a suite, other tests might have already imported them.
        # So we patch sys.modules but carefully.
        self.module_patcher = patch.dict(
            "sys.modules",
            {
                "discord": MagicMock(),
                "pymongo": MagicMock(),
                "pymongo.errors": MagicMock(),
            },
        )
        self.module_patcher.start()

        # Now import the actual engine
        from game_systems.adventure.adventure_resolution import AdventureResolutionEngine
        self.AdventureResolutionEngine = AdventureResolutionEngine

        # Configure logging to suppress noisy output during the stress test
        self.logger = logging.getLogger("stress_test_realistic")
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        self.module_patcher.stop()

    def test_realistic_stress(self):
        """Stress test the Adventure Resolution Engine with 10k realistic sessions."""
        mock_db = RealisticMockDatabase()
        mock_bot = MagicMock()

        # Initialize Engine
        engine = self.AdventureResolutionEngine(mock_bot, mock_db)

        # Generate 10k sessions
        NUM_SESSIONS = 10000
        sessions = []
        location_id = "shrouded_fen"

        for i in range(NUM_SESSIONS):
            sessions.append(
                {
                    "discord_id": 100000 + i,
                    "duration_minutes": 60,  # 4 steps (15 min each)
                    "steps_completed": 0,
                    "start_time": "2023-01-01T00:00:00",
                    "location_id": location_id,
                    "active": 1,
                    "version": 1,
                    "logs": "[]",
                    "loot_collected": "{}",
                    "active_monster_json": None,
                    "supplies": {},
                }
            )

        start_time = time.time()

        for session_doc in sessions:
            engine.resolve_session(session_doc)

        end_time = time.time()
        duration = end_time - start_time

        throughput = NUM_SESSIONS / duration

        print(f"\n[Stress Test] Processed {NUM_SESSIONS} sessions in {duration:.4f}s")
        print(f"[Stress Test] Throughput: {throughput:.2f} sessions/sec")

        # We assert that the throughput is greater than or equal to 167
        # as specified in the original manual test script (10k/60s)
        self.assertGreaterEqual(
            throughput,
            167,
            f"Throughput {throughput:.2f} is below target 167 sessions/sec"
        )
