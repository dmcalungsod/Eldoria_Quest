import logging
import os
import sys
import time
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database_manager import DatabaseManager

# Configure minimal logging
logging.basicConfig(level=logging.ERROR)


def benchmark_create_player_synthetic():
    """
    Synthetic benchmark to simulate DB latency.
    Since a real MongoDB instance is not available in this environment,
    we simulate network round-trip time (RTT) for DB operations.
    """

    # Simulated Latency in seconds
    LATENCY_PER_OP = 0.002  # 2ms per round-trip

    # Mock Collection
    class MockCollection:
        def insert_one(self, doc):
            time.sleep(LATENCY_PER_OP)
            return MagicMock()

        def insert_many(self, docs):
            time.sleep(LATENCY_PER_OP)  # One round trip for many
            return MagicMock()

        def find_one(self, *args, **kwargs):
            time.sleep(LATENCY_PER_OP)
            return None  # Simulate not found

        def update_one(self, *args, **kwargs):
            time.sleep(LATENCY_PER_OP)
            return MagicMock()

    # Mock Database
    class MockDB:
        def __getitem__(self, name):
            return MockCollection()

    # Instantiate Manager with Mock
    # We cheat a bit by patching the .db attribute after init
    # But wait, __init__ tries to connect.
    # We need to mock MongoClient before importing or before init.
    # Since we already imported, we'll subclass or patch.

    # Let's just manually patch the instance
    db_manager = DatabaseManager.__new__(DatabaseManager)
    db_manager._initialized = True
    db_manager.db = MockDB()
    db_manager._class_cache = {}
    db_manager._skill_cache = {}

    # Mock _skill_cache to avoid DB lookup in loops if any
    # (Actually create_player_full doesn't look up skills, it inserts them)

    # Parameters for creation
    class_id = 1
    stats_json = "{}"
    max_hp = 100
    max_mp = 50
    race = "Human"
    gender = "Male"
    default_skill_keys = ["slash", "defend", "inspect", "sprint", "meditate"]

    # --- 1. Loop Implementation (Unoptimized) ---
    def create_player_loop(discord_id):
        username = f"User_{discord_id}"

        # Player (1 RTT)
        db_manager._col("players").insert_one({})

        # Stats (1 RTT)
        db_manager._col("stats").insert_one({})

        # Default Skills (5 RTTs for 5 skills)
        for sk in default_skill_keys:
            db_manager._col("player_skills").insert_one({})

        # Guild Membership (1 RTT)
        # Manually inline the guild member insert to avoid calling method which might have overhead
        db_manager._col("guild_members").insert_one({})

    # --- 2. Batch Implementation (Optimized) ---
    def create_player_batch(discord_id):
        # Using the actual method logic but mapping it to our mock
        # We need to call the actual method but ensure it uses our mock db
        # DatabaseManager.create_player_full uses self._col() which uses self.db

        # We need to ensure insert_guild_member uses our mock too.
        # It does, via self._col().

        # However, create_player_full calls self.insert_guild_member.
        # We need to make sure db_manager has that method (it does).

        db_manager.create_player_full(
            discord_id=discord_id,
            username=f"User_{discord_id}",
            class_id=class_id,
            stats_json_str=stats_json,
            max_hp=max_hp,
            max_mp=max_mp,
            race=race,
            gender=gender,
            default_skill_keys=default_skill_keys,
        )

    # --- Run Benchmarks ---
    iterations = 50
    print(
        f"Benchmarking with {iterations} iterations (Simulated Latency: {LATENCY_PER_OP * 1000}ms/op)..."
    )

    # Measure Loop
    start_time = time.time()
    for i in range(iterations):
        create_player_loop(1000 + i)
    loop_duration = time.time() - start_time
    print(
        f"Loop implementation: {loop_duration:.4f} seconds ({loop_duration / iterations * 1000:.2f} ms/op)"
    )

    # Measure Batch
    start_time = time.time()
    for i in range(iterations):
        create_player_batch(2000 + i)
    batch_duration = time.time() - start_time
    print(
        f"Batch implementation: {batch_duration:.4f} seconds ({batch_duration / iterations * 1000:.2f} ms/op)"
    )

    # Calculate improvement
    if loop_duration > 0:
        speedup = (loop_duration - batch_duration) / loop_duration * 100
        print(f"Improvement: {speedup:.2f}% faster")


if __name__ == "__main__":
    benchmark_create_player_synthetic()
