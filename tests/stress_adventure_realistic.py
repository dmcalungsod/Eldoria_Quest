import json
import logging
import os
import sys
import time
from unittest.mock import MagicMock

# Add root to sys.path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("stress_test_realistic")

# --- MOCK MODULES ---
sys.modules["discord"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Now we can import game systems safely
from game_systems.adventure.adventure_resolution import AdventureResolutionEngine


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

    def update_player_vitals_delta(self, discord_id, dhp, dmp, mhp, mmp):
        return True

    def update_adventure_session(self, discord_id, **kwargs):
        return True

    def update_adventure_status(self, discord_id, status):
        return True

    def set_player_vitals(self, discord_id, hp, mp):
        return True

    def add_active_buffs_bulk(self, discord_id, buffs):
        return True

    def add_title(self, discord_id, title):
        return True

    def get_player_quests(self, discord_id):
        return []

    def update_progress(self, discord_id, quest_id, obj_type, task, amount):
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

    def increment_guild_stat(self, discord_id, field, amount=1):
        return True

    def increment_specific_monster_kill(self, discord_id, monster_name, amount=1):
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

    def update_stat_exp(self, *args, **kwargs):
        return True

    def get_skill_with_definition(self, discord_id, skill_key):
        return {"skill_level": 1, "skill_exp": 0, "name": skill_key}

    def update_player_skill(self, *args, **kwargs):
        return True

    def get_guild_member_field(self, discord_id, field):
        if field == "rank":
            return "F"
        return None

    def add_inventory_item(self, *args, **kwargs):
        return True

    def update_player_mixed(self, *args, **kwargs):
        return True

    def end_adventure_session(self, *args, **kwargs):
        return True

    def _col(self, name):
        # Return a mock collection that can handle find()
        mock_col = MagicMock()
        mock_col.find.return_value = []  # Return empty list for find
        mock_col.find_one.return_value = None
        return mock_col


def run_realistic_stress_test():
    logger.info("Initializing Realistic Stress Test...")

    mock_db = RealisticMockDatabase()
    mock_bot = MagicMock()

    # Initialize Engine
    engine = AdventureResolutionEngine(mock_bot, mock_db)

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

    logger.info(f"Generated {NUM_SESSIONS} sessions (Duration: 60m / 4 steps).")
    logger.info("Starting Resolution Loop...")

    start_time = time.time()
    processed_count = 0

    for session_doc in sessions:
        engine.resolve_session(session_doc)
        processed_count += 1

        if processed_count % 1000 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Processed {processed_count} sessions... ({processed_count / elapsed:.2f} sess/s)")

    end_time = time.time()
    duration = end_time - start_time

    throughput = NUM_SESSIONS / duration
    logger.info(f"Finished {NUM_SESSIONS} sessions in {duration:.4f}s")
    logger.info(f"Throughput: {throughput:.2f} sessions/sec")

    total_steps = NUM_SESSIONS * 4
    steps_throughput = total_steps / duration
    logger.info(f"Step Throughput: {steps_throughput:.2f} steps/sec")

    if throughput < 167:
        logger.warning("⚠️ Throughput is below target (10k/60s = 167/s). Optimization needed.")
    else:
        logger.info("✅ Throughput meets requirements.")


if __name__ == "__main__":
    run_realistic_stress_test()
