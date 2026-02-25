import logging
import os
import sys
import time
from unittest.mock import MagicMock, patch

# Add root to sys.path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("stress_test")

# Mock discord and pymongo
sys.modules["discord"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

from game_systems.adventure.adventure_resolution import AdventureResolutionEngine


# Mock DB Class
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

    # Add other methods if needed by AdventureResolutionEngine initialization
    def _col(self, name):
        return MagicMock()


class FastAdventureSession:
    def __init__(self, db, quest, inv, discord_id, row_data=None):
        self.steps_completed = row_data.get("steps_completed", 0) if row_data else 0
        self.discord_id = discord_id
        self.logs = []
        self.loot = {}
        self.version = 1

    def simulate_step(self, context_bundle=None, background=False, persist=False):
        # Simulate CPU work if needed
        # time.sleep(0.0001)
        return {"dead": False, "vitals": {"current_hp": 100, "current_mp": 100}}

    def save_state(self):
        pass


def run_stress_test():
    logger.info("Initializing Stress Test (Scheduler Only)...")

    mock_db = MockDatabase()
    mock_bot = MagicMock()

    # Generate 10k sessions
    NUM_SESSIONS = 10000
    sessions = []
    for i in range(NUM_SESSIONS):
        sessions.append(
            {
                "discord_id": 100000 + i,
                "duration_minutes": 60,
                "steps_completed": 0,
                "start_time": "2023-01-01T00:00:00",
                # ... other fields ignored by mocked session
            }
        )

    logger.info(f"Generated {NUM_SESSIONS} sessions.")

    # Initialize Engine
    engine = AdventureResolutionEngine(mock_bot, mock_db)

    # Patch AdventureSession to avoid complex logic
    # We simulate a session that processes steps and returns simple results
    with patch("game_systems.adventure.adventure_resolution.AdventureSession", side_effect=FastAdventureSession):
        logger.info("Starting Resolution Loop...")
        start_time = time.time()

        for session_doc in sessions:
            engine.resolve_session(session_doc)

        end_time = time.time()
        duration = end_time - start_time

        throughput = NUM_SESSIONS / duration
        logger.info(f"Finished in {duration:.4f}s")
        logger.info(f"Throughput: {throughput:.2f} sessions/sec")

        # Verification
        assert len(mock_db.status_updates) == NUM_SESSIONS
        logger.info("✅ Verified: All sessions updated.")


if __name__ == "__main__":
    run_stress_test()
