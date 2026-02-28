import os
import sys
import time
import logging
import unittest
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.append(os.getcwd())

# Mock modules before importing
if "pymongo" not in sys.modules:
    sys.modules["pymongo"] = MagicMock()
    sys.modules["pymongo.errors"] = MagicMock()
if "discord" not in sys.modules:
    sys.modules["discord"] = MagicMock()

from game_systems.adventure.adventure_resolution import AdventureResolutionEngine


class MockDatabase:
    def __init__(self):
        self.sessions = {}
        self.players = {}
        self.status_updates = {}
        self.vitals_updates = []

    def get_combat_context_bundle(self, discord_id):
        return {
            "player": {"current_hp": 100, "current_mp": 100},
            "stats": {"HP": 100, "MP": 100},
            "buffs": [],
            "skills": [],
        }

    def update_adventure_status(self, discord_id, status):
        self.status_updates[discord_id] = status

    def update_player_vitals_delta(self, discord_id, dhp, dmp, mhp, mmp):
        self.vitals_updates.append((discord_id, dhp, dmp))

    def update_adventure_session(self, *args, **kwargs):
        pass

    def end_adventure_session(self, *args):
        pass

    def _col(self, name):
        return MagicMock()

    def get_active_boosts(self):
        return []


class FastAdventureSession:
    def __init__(self, db, quest, inv, discord_id, row_data=None):
        self.steps_completed = row_data.get("steps_completed", 0) if row_data else 0
        self.discord_id = discord_id
        self.location_id = "forest_outskirts"
        self.logs = []
        self.loot = {}
        self.version = 1

    def simulate_step(self, context_bundle=None, background=False, persist=False, weather=None, time_phase=None):
        return {"dead": False, "vitals": {"current_hp": 100, "current_mp": 100}}

    def save_state(self):
        pass

    def _fetch_session_context(self, bundle=None):
        player_stats = MagicMock()
        player_stats.max_hp = 100
        player_stats.max_mp = 100

        return {
            "vitals": {"current_hp": 100, "current_mp": 100},
            "player_stats": player_stats,
            "stats_dict": {"HP": 100, "MP": 100},
            "player_row": {"current_hp": 100, "current_mp": 100},
            "skills": [],
            "active_boosts": {},
            "event_type": None,
        }


class TestAdventureSchedulerStress(unittest.TestCase):
    @patch("game_systems.adventure.adventure_resolution.AdventureSession", side_effect=FastAdventureSession)
    def test_scheduler_stress_10k_sessions(self, mock_session_cls):
        """Stress test resolving 10,000 adventure sessions to verify throughput and integrity."""
        mock_db = MockDatabase()
        mock_bot = MagicMock()

        NUM_SESSIONS = 10000
        sessions = [
            {
                "discord_id": 100000 + i,
                "duration_minutes": 60,
                "steps_completed": 0,
                "start_time": "2023-01-01T00:00:00",
            }
            for i in range(NUM_SESSIONS)
        ]

        engine = AdventureResolutionEngine(mock_bot, mock_db)

        # We disable info logging to prevent I/O bottleneck during the stress test
        logger = logging.getLogger("eldoria.resolution")
        old_level = logger.getEffectiveLevel()
        logger.setLevel(logging.WARNING)

        start_time = time.time()

        for session_doc in sessions:
            engine.resolve_session(session_doc)

        end_time = time.time()
        logger.setLevel(old_level)

        duration = end_time - start_time
        throughput = NUM_SESSIONS / duration if duration > 0 else NUM_SESSIONS

        print(f"\nStress Test Finished: 10,000 sessions in {duration:.4f}s ({throughput:.2f} sessions/sec)")

        self.assertEqual(len(mock_db.status_updates), NUM_SESSIONS, "Not all sessions were updated.")
        self.assertGreater(throughput, 1000, "Throughput is too low; should be >1000 sessions/sec")


if __name__ == "__main__":
    import logging
    unittest.main()
