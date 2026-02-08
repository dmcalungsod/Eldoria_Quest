
import os
import sys
import time

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager


@pytest.fixture
def db():
    db_name = "test_boost_cache.db"
    if os.path.exists(db_name):
        os.remove(db_name)

    # Initialize DB
    manager = DatabaseManager(db_name)

    # Create required tables
    with manager.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_boosts (
                boost_key TEXT PRIMARY KEY,
                multiplier REAL NOT NULL,
                end_time TEXT NOT NULL
            )
        """)

    yield manager

    # Cleanup
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
        except OSError:
            pass

def test_boost_caching(db):
    """Verify that boosts are cached and invalidated correctly."""

    # 1. Set initial boost
    db.set_global_boost("exp_boost", 2.0, 1)

    # 2. First fetch (should hit DB and cache)
    start_time = time.time()
    boosts1 = db.get_active_boosts()
    duration1 = time.time() - start_time

    assert len(boosts1) == 1
    assert boosts1[0]["boost_key"] == "exp_boost"
    assert boosts1[0]["multiplier"] == 2.0

    # 3. Second fetch (should hit cache)
    # We can't easily assert on internal state without accessing private members,
    # but we can check if modifying DB directly (bypassing manager) is ignored until invalidation

    # Modify DB directly (bypassing manager methods to simulate external change or verify cache isolation)
    # If cache is working, get_active_boosts should still return old value
    with db.get_connection() as conn:
        conn.execute("UPDATE global_boosts SET multiplier = 5.0 WHERE boost_key = 'exp_boost'")

    boosts2 = db.get_active_boosts()
    # Verify cache isolation: direct DB update shouldn't reflect immediately
    assert boosts2[0]["multiplier"] == 2.0

    # 4. Update boost via manager (should invalidate cache)
    db.set_global_boost("exp_boost", 3.0, 1)

    boosts3 = db.get_active_boosts()
    assert len(boosts3) == 1
    assert boosts3[0]["multiplier"] == 3.0

    # 5. Clear boosts (should invalidate cache)
    db.clear_global_boosts()
    boosts4 = db.get_active_boosts()
    assert len(boosts4) == 0


def test_cache_ttl(db):
    """Verify that cache expires after TTL."""
    # 1. Set boost
    db.set_global_boost("ttl_test", 2.0, 1)

    # 2. Cache it
    db.get_active_boosts()

    # 3. Modify DB directly
    with db.get_connection() as conn:
        conn.execute("UPDATE global_boosts SET multiplier = 10.0 WHERE boost_key = 'ttl_test'")

    # 4. Should still be cached
    res1 = db.get_active_boosts()
    assert res1[0]["multiplier"] == 2.0

    # 5. Fast forward time beyond TTL (61 seconds)
    # Manually backdate the cache timestamp to simulate expiration
    # (Avoiding mocking time.time which can be tricky with builtins)
    db._boost_cache_time = time.time() - 100

    # 6. Fetch again - should refresh from DB
    res2 = db.get_active_boosts()
    assert res2[0]["multiplier"] == 10.0
