"""
Database Manager for Eldoria Quest
----------------------------------
MongoDB-backed database layer using pymongo.
Singleton pattern with connection pooling and atomic operations.
"""

import datetime
import json
import logging
import math
import os
import time
from contextlib import contextmanager
from typing import Any

from pymongo import InsertOne, MongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError

from game_systems.core.world_time import WorldTime
from game_systems.data.skills_data import SKILLS as SKILL_DEFINITIONS

# Configure logging
logger = logging.getLogger("eldoria.db")

# Default fallback — overridden by env var
DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "eldoria_quest"

BASE_INVENTORY_SLOTS = 10
MAX_INVENTORY_SLOTS = 20  # Deprecated: Use calculate_inventory_limit
MAX_STACK_CONSUMABLE = 5
MAX_STACK_MATERIAL = 50
MAX_STACK_EQUIPMENT = 1
MAX_STACK_DEFAULT = 10


class DatabaseManager:
    """
    Handles all database operations for Eldoria Quest.
    Uses MongoDB via pymongo. Singleton pattern with connection pooling.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, mongo_uri: str | None = None, db_name: str | None = None):
        if self._initialized:
            return

        self._mongo_uri = mongo_uri or os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
        self._db_name = db_name or os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)

        # Strip .db extension if carried over from SQLite config
        if self._db_name.endswith(".db"):
            self._db_name = self._db_name.replace(".db", "").replace(".", "_")

        self._client = MongoClient(self._mongo_uri)
        self.db = self._client[self._db_name]

        self._class_cache: dict[int, dict] = {}
        self._skill_cache: dict[str, dict] = {}  # Cache for skill definitions
        self._boost_cache: list[dict] = []
        self._boost_cache_time: float = 0.0

        self._world_event_cache: dict | None = None
        self._world_event_cache_time: float = 0.0

        self._tournament_cache: dict | None = None
        self._tournament_cache_time: float = 0.0

        logger.info(f"Connected to MongoDB: {self._db_name}")
        self._initialized = True

    # ============================================================
    # HELPERS
    # ============================================================

    def _ensure_skill_cache(self):
        """Loads all skills from DB into cache if empty."""
        if self._skill_cache:
            return

        skill_docs = self._col("skills").find({})
        for doc in skill_docs:
            # Pre-parse buff_data if it's a string
            if doc.get("buff_data") and isinstance(doc["buff_data"], str):
                try:
                    doc["buff_data"] = json.loads(doc["buff_data"])
                except json.JSONDecodeError:
                    doc["buff_data"] = {}

            self._skill_cache[doc["key_id"]] = doc

        # OVERLAY: Ensure static skill properties match the codebase (Source of Truth)
        # This prevents stale database records (e.g., missing scaling stats) from breaking logic.
        for key, code_def in SKILL_DEFINITIONS.items():
            if key in self._skill_cache:
                self._skill_cache[key].update(
                    {
                        "name": code_def.get("name"),
                        "description": code_def.get("description"),
                        "scaling_stat": code_def.get("scaling_stat", "MAG"),
                        "scaling_factor": code_def.get("scaling_factor", 1.0),
                        "power_multiplier": code_def.get("power_multiplier", 1.0),
                        "mp_cost": code_def.get("mp_cost", 0),
                        "heal_power": code_def.get("heal_power", 0),
                        "buff_data": code_def.get("buff_data"),
                    }
                )

    def _col(self, name: str):
        """Shorthand to get a collection."""
        return self.db[name]

    @contextmanager
    def get_connection(self):
        """
        Compatibility shim — yields self so legacy code using
        `with db.get_connection() as conn:` continues to work
        during incremental migration. New code should call
        DatabaseManager methods directly.
        """
        yield self

    # ============================================================
    # PLAYER CORE
    # ============================================================

    def player_exists(self, discord_id: int) -> bool:
        """Checks if a player profile exists."""
        return self._col("players").find_one({"discord_id": discord_id}, {"_id": 1}) is not None

    def create_player(
        self,
        discord_id: int,
        name: str,
        class_id: int,
        stats_data: dict[str, Any],
        initial_hp: int,
        initial_mp: int,
        race: str | None = None,
        gender: str | None = None,
    ):
        """Creates a new player with stats."""
        self._col("players").insert_one(
            {
                "discord_id": discord_id,
                "name": name,
                "class_id": class_id,
                "race": race,
                "gender": gender,
                "level": 1,
                "experience": 0,
                "exp_to_next": 1000,
                "current_hp": initial_hp,
                "current_mp": initial_mp,
                "vestige_pool": 0,
                "aurum": 0,
                "titles": [],
                "active_title": None,
                "crafting_level": 1,
                "crafting_xp": 0,
                "last_regen_time": WorldTime.now().isoformat(),
            }
        )
        self._col("stats").insert_one(
            {
                "discord_id": discord_id,
                "stats_json": json.dumps(stats_data),
                "str_exp": 0.0,
                "end_exp": 0.0,
                "dex_exp": 0.0,
                "agi_exp": 0.0,
                "mag_exp": 0.0,
                "lck_exp": 0.0,
            }
        )
        logger.info(f"Created new player: {name} ({discord_id})")

    def get_player(self, discord_id: int) -> dict | None:
        """Fetches the main player record."""
        doc = self._col("players").find_one({"discord_id": discord_id}, {"_id": 0})
        return doc

    def get_combat_context_bundle(self, discord_id: int) -> dict[str, Any] | None:
        """
        Fetches all necessary data for combat in a single batch.
        Returns a dict with 'player', 'stats', 'buffs', 'skills'.
        Returns None if player not found.
        """
        now_iso = WorldTime.now().isoformat()

        # Optimized: Single Aggregation Pipeline to reduce DB round-trips from 4 to 1
        pipeline = [
            {"$match": {"discord_id": discord_id}},
            {
                "$lookup": {
                    "from": "stats",
                    "let": {"did": "$discord_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$discord_id", "$$did"]}}},
                        {"$project": {"_id": 0}},
                    ],
                    "as": "stats_docs",
                }
            },
            {
                "$lookup": {
                    "from": "active_buffs",
                    "let": {"did": "$discord_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$discord_id", "$$did"]},
                                        {"$gt": ["$end_time", now_iso]},
                                    ]
                                }
                            }
                        },
                        {"$project": {"_id": 0}},
                    ],
                    "as": "buffs",
                }
            },
            {
                "$lookup": {
                    "from": "player_skills",
                    "let": {"did": "$discord_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$discord_id", "$$did"]}}},
                        {"$project": {"_id": 0}},
                    ],
                    "as": "player_skills",
                }
            },
            {
                "$lookup": {
                    "from": "adventure_sessions",
                    "let": {"did": "$discord_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$discord_id", "$$did"]},
                                        {"$eq": ["$active", 1]},
                                    ]
                                }
                            }
                        },
                        {"$project": {"_id": 0}},
                    ],
                    "as": "active_session",
                }
            },
            {"$project": {"_id": 0}},
        ]

        result = list(self._col("players").aggregate(pipeline))

        if not result:
            return None

        data = result[0]

        # 1. Process Stats
        stats_data = {}
        if data.get("stats_docs"):
            stats_row = data["stats_docs"][0]
            if stats_row.get("stats_json"):
                try:
                    stats_data = json.loads(stats_row["stats_json"])
                except json.JSONDecodeError:
                    logger.error(f"Corrupted stats_json for user {discord_id}")

        # 2. Process Buffs
        # Buffs are already list of dicts from lookup
        buffs = data.get("buffs", [])

        # 3. Process Skills
        player_skill_docs = data.get("player_skills", [])
        self._ensure_skill_cache()
        skills = []
        for ps in player_skill_docs:
            skill_def = self._skill_cache.get(ps["skill_key"])
            if skill_def and skill_def["type"] == "Active":
                skills.append(
                    {
                        "key_id": skill_def["key_id"],
                        "name": skill_def["name"],
                        "type": skill_def["type"],
                        "skill_level": ps["skill_level"],
                        "mp_cost": skill_def.get("mp_cost", 0),
                        "power_multiplier": skill_def.get("power_multiplier", 1.0),
                        "heal_power": skill_def.get("heal_power", 0),
                        "buff_data": skill_def.get("buff_data"),
                        "scaling_stat": skill_def.get("scaling_stat", "MAG"),
                        "scaling_factor": skill_def.get("scaling_factor", 1.0),
                    }
                )

        # 4. Extract Session
        active_session = data.get("active_session", [])
        session_data = active_session[0] if active_session else None

        # 5. Extract Player Row (remove joined fields)
        player_row = {
            k: v for k, v in data.items() if k not in ["stats_docs", "buffs", "player_skills", "active_session"]
        }

        return {
            "player": player_row,
            "stats": stats_data,
            "buffs": buffs,
            "skills": skills,
            "active_session": session_data,
        }

    def get_profile_bundle(self, discord_id: int) -> dict | None:
        """
        Fetches player, stats, and guild data in a single aggregation.
        Reduces DB round-trips for the profile UI.
        """
        # Optimized: Single Aggregation Pipeline to reduce DB round-trips
        pipeline = [
            {"$match": {"discord_id": discord_id}},
            {
                "$lookup": {
                    "from": "stats",
                    "localField": "discord_id",
                    "foreignField": "discord_id",
                    "as": "stats_docs",
                }
            },
            {
                "$lookup": {
                    "from": "guild_members",
                    "localField": "discord_id",
                    "foreignField": "discord_id",
                    "as": "guild_docs",
                }
            },
            {"$project": {"stats_docs._id": 0, "guild_docs._id": 0}},
        ]

        result = list(self._col("players").aggregate(pipeline))

        if not result:
            return None

        data = result[0]

        # 1. Process Stats
        stats_data = {}
        if data.get("stats_docs"):
            stats_row = data["stats_docs"][0]
            if stats_row.get("stats_json"):
                try:
                    stats_data = json.loads(stats_row["stats_json"])
                except json.JSONDecodeError:
                    logger.error(f"Corrupted stats_json for user {discord_id}")

        # 2. Process Guild
        guild_data = None
        if data.get("guild_docs"):
            guild_data = data["guild_docs"][0]

        # 3. Clean Player Data
        # Remove the joined arrays to return a clean player dict
        player_data = {k: v for k, v in data.items() if k not in ["stats_docs", "guild_docs"]}

        return {
            "player": player_data,
            "stats": stats_data,
            "guild": guild_data,
        }

    # ============================================================
    # STATS & VITALS
    # ============================================================

    def get_player_stats_json(self, discord_id: int) -> dict[str, Any]:
        """Fetches and parses the JSON stats block."""
        row = self._col("stats").find_one({"discord_id": discord_id}, {"_id": 0, "stats_json": 1})
        if not row or not row.get("stats_json"):
            return {}
        try:
            return json.loads(row["stats_json"])
        except json.JSONDecodeError:
            logger.error(f"Corrupted stats_json for user {discord_id}")
            return {}

    def get_player_stats_row(self, discord_id: int) -> dict | None:
        """Fetches the raw stats row (including practice EXP columns)."""
        return self._col("stats").find_one({"discord_id": discord_id}, {"_id": 0})

    def update_player_stats(self, discord_id: int, stats_data: dict[str, Any]):
        """Updates the JSON stats block."""
        self._col("stats").update_one(
            {"discord_id": discord_id},
            {"$set": {"stats_json": json.dumps(stats_data)}},
        )

    def get_player_vitals(self, discord_id: int) -> dict | None:
        """Fetches current HP/MP."""
        doc = self._col("players").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "current_hp": 1, "current_mp": 1},
        )
        return doc

    def set_player_vitals(self, discord_id: int, hp: int, mp: int):
        """Updates current HP/MP."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$set": {"current_hp": hp, "current_mp": mp}},
        )

    def apply_passive_regen(self, discord_id: int) -> tuple[int, int]:
        """
        Calculates and applies passive HP/MP regeneration based on time elapsed.
        Rate: 5% Max HP per hour, 10% Max MP per hour.
        Updates last_regen_time to now.
        """
        # Avoid circular import
        from game_systems.player.player_stats import PlayerStats

        now = WorldTime.now()

        # 1. Fetch current state
        player = self._col("players").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "current_hp": 1, "current_mp": 1, "last_regen_time": 1},
        )
        if not player:
            return 0, 0

        # Migration: If last_regen_time is missing, set to now and return (no free heal on first run)
        if "last_regen_time" not in player:
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$set": {"last_regen_time": now.isoformat()}},
            )
            return 0, 0

        last_regen_str = player["last_regen_time"]
        try:
            last_regen = datetime.datetime.fromisoformat(last_regen_str)
        except ValueError:
            # Corrupted time, reset
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$set": {"last_regen_time": now.isoformat()}},
            )
            return 0, 0

        # Calculate elapsed hours
        elapsed_seconds = (now - last_regen).total_seconds()
        elapsed_hours = elapsed_seconds / 3600.0

        # Minimum threshold: 1 minute (1/60 hours) to avoid micro-updates
        if elapsed_hours < (1.0 / 60.0):
            return 0, 0

        # 2. Fetch Max Stats
        stats_json = self.get_player_stats_json(discord_id)
        if not stats_json:
            return 0, 0

        try:
            stats = PlayerStats.from_dict(stats_json)
            max_hp = stats.max_hp
            max_mp = stats.max_mp
        except Exception as e:
            logger.error(f"Error calculating max stats for regen {discord_id}: {e}")
            return 0, 0

        # 3. Calculate Regeneration
        # 5% HP per hour, 10% MP per hour
        hp_regen_amount = int(max_hp * 0.05 * elapsed_hours)
        mp_regen_amount = int(max_mp * 0.10 * elapsed_hours)

        # Bug Fix: Do NOT update time if gain is 0. This allows time to accumulate.
        if hp_regen_amount <= 0 and mp_regen_amount <= 0:
            return 0, 0

        current_hp = player.get("current_hp", 0)
        current_mp = player.get("current_mp", 0)

        # Clamp to Max
        new_hp = min(max_hp, current_hp + hp_regen_amount)
        new_mp = min(max_mp, current_mp + mp_regen_amount)

        actual_hp_gain = new_hp - current_hp
        actual_mp_gain = new_mp - current_mp

        # 4. Atomic Update
        # Only update if there's a change or to advance time
        self._col("players").update_one(
            {"discord_id": discord_id},
            {
                "$set": {
                    "current_hp": new_hp,
                    "current_mp": new_mp,
                    "last_regen_time": now.isoformat(),
                }
            },
        )

        if actual_hp_gain > 0 or actual_mp_gain > 0:
            logger.info(
                f"Passive Regen for {discord_id}: +{actual_hp_gain} HP, +{actual_mp_gain} MP ({elapsed_hours:.2f}h)"
            )

        return actual_hp_gain, actual_mp_gain

    def update_player_vitals_delta(self, discord_id: int, hp_delta: int, mp_delta: int, max_hp: int, max_mp: int):
        """
        Updates HP/MP by a delta, clamping to [0, max].
        Uses MongoDB aggregation pipeline in update for atomicity.
        """
        pipeline = [
            {
                "$set": {
                    "current_hp": {
                        "$min": [
                            max_hp,
                            {"$max": [0, {"$add": ["$current_hp", hp_delta]}]},
                        ]
                    },
                    "current_mp": {
                        "$min": [
                            max_mp,
                            {"$max": [0, {"$add": ["$current_mp", mp_delta]}]},
                        ]
                    },
                }
            }
        ]
        self._col("players").update_one({"discord_id": discord_id}, pipeline)

    def update_player_level_data(self, discord_id: int, level: int, exp: int, exp_to_next: int):
        """Updates level and experience values."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$set": {"level": level, "experience": exp, "exp_to_next": exp_to_next}},
        )

    # ============================================================
    # CLASS & SKILLS
    # ============================================================

    def get_class(self, class_id: int) -> dict[str, Any] | None:
        """Fetches class definition with caching."""
        if class_id in self._class_cache:
            return self._class_cache[class_id]

        row = self._col("classes").find_one({"id": class_id}, {"_id": 0})
        if row:
            self._class_cache[class_id] = row
            return row
        return None

    def get_player_skills(self, discord_id: int) -> list[dict]:
        """Fetches all learned skills joined with skill definitions."""
        player_skill_docs = list(
            self._col("player_skills").find(
                {"discord_id": discord_id},
                {"_id": 0},
            )
        )

        self._ensure_skill_cache()
        results = []
        for ps in player_skill_docs:
            skill_def = self._skill_cache.get(ps["skill_key"])
            if skill_def:
                results.append(
                    {
                        "name": skill_def["name"],
                        "type": skill_def["type"],
                        "skill_level": ps["skill_level"],
                        "skill_exp": ps.get("skill_exp", 0),
                    }
                )
        results.sort(key=lambda x: (x["type"], x["name"]))
        return results

    def get_combat_skills(self, discord_id: int) -> list[dict[str, Any]]:
        """Fetches detailed skill info for combat (Active skills only)."""
        player_skill_docs = list(
            self._col("player_skills").find(
                {"discord_id": discord_id},
                {"_id": 0},
            )
        )

        self._ensure_skill_cache()
        skills = []
        for ps in player_skill_docs:
            skill_def = self._skill_cache.get(ps["skill_key"])
            if skill_def and skill_def["type"] == "Active":
                skills.append(
                    {
                        "key_id": skill_def["key_id"],
                        "name": skill_def["name"],
                        "type": skill_def["type"],
                        "skill_level": ps["skill_level"],
                        "mp_cost": skill_def.get("mp_cost", 0),
                        "power_multiplier": skill_def.get("power_multiplier", 1.0),
                        "heal_power": skill_def.get("heal_power", 0),
                        "buff_data": skill_def.get("buff_data"),
                        "scaling_stat": skill_def.get("scaling_stat", "MAG"),
                        "scaling_factor": skill_def.get("scaling_factor", 1.0),
                    }
                )
        return skills

    # ============================================================
    # GUILD SYSTEM
    # ============================================================

    def get_guild_member_data(self, discord_id: int) -> dict | None:
        """Fetches guild membership details (Rank, Points)."""
        return self._col("guild_members").find_one({"discord_id": discord_id}, {"_id": 0})

    def get_guild_card_data(self, discord_id: int) -> dict | None:
        """Fetches data specifically for the Guild Card UI."""
        player = self._col("players").find_one({"discord_id": discord_id}, {"_id": 0, "name": 1})
        guild = self._col("guild_members").find_one({"discord_id": discord_id}, {"_id": 0, "rank": 1, "join_date": 1})
        if not player or not guild:
            return None
        return {
            "name": player["name"],
            "rank": guild["rank"],
            "join_date": guild["join_date"],
        }

    # ============================================================
    # FACTION SYSTEM (New methods for Factions)
    # ============================================================

    def get_player_faction_data(self, discord_id: int) -> dict | None:
        """Fetches the player's faction membership (faction_id, reputation)."""
        return self._col("player_factions").find_one({"discord_id": discord_id}, {"_id": 0})

    def set_player_faction(self, discord_id: int, faction_id: str):
        """Sets the player's faction, resetting reputation to 0 if changing."""
        self._col("player_factions").update_one(
            {"discord_id": discord_id},
            {
                "$set": {
                    "faction_id": faction_id,
                    "reputation": 0,
                    "join_date": WorldTime.now().isoformat(),
                }
            },
            upsert=True,
        )

    def leave_faction(self, discord_id: int):
        """Removes the player from their current faction."""
        self._col("player_factions").delete_one({"discord_id": discord_id})

    def update_faction_reputation(self, discord_id: int, amount: int) -> int:
        """Updates (increments) faction reputation. Returns new total."""
        result = self._col("player_factions").find_one_and_update(
            {"discord_id": discord_id},
            {"$inc": {"reputation": amount}},
            return_document=True,
        )
        return result["reputation"] if result else 0

    def get_faction_leaderboard(self, faction_id: str, limit: int = 10) -> list[dict]:
        """Fetches top players for a specific faction."""
        pipeline = [
            {"$match": {"faction_id": faction_id}},
            {"$sort": {"reputation": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "players",
                    "localField": "discord_id",
                    "foreignField": "discord_id",
                    "as": "player_info",
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "discord_id": 1,
                    "reputation": 1,
                    "name": {"$arrayElemAt": ["$player_info.name", 0]},
                }
            },
        ]
        return list(self._col("player_factions").aggregate(pipeline))

    # ============================================================
    # GLOBAL SYSTEMS (Boosts)
    # ============================================================

    def get_active_boosts(self) -> list[dict[str, Any]]:
        """Fetches currently active global server boosts (Cached for 60s)."""
        now_ts = time.time()
        if now_ts - self._boost_cache_time < 60:
            return self._boost_cache

        now_iso = WorldTime.now().isoformat()
        try:
            self._boost_cache = list(
                self._col("global_boosts").find(
                    {"end_time": {"$gt": now_iso}},
                    {"_id": 0, "boost_key": 1, "multiplier": 1, "end_time": 1},
                )
            )
            self._boost_cache_time = now_ts
            return self._boost_cache
        except Exception as e:
            logger.error(f"Error fetching active boosts: {e}")
            return []

    def set_global_boost(self, key: str, multiplier: float, duration_hours: int):
        """
        Sets a global boost (e.g., exp_boost, loot_boost).
        Updates the record if it already exists (upsert).
        """
        end_time = (WorldTime.now() + datetime.timedelta(hours=duration_hours)).isoformat()
        self._col("global_boosts").update_one(
            {"boost_key": key},
            {
                "$set": {
                    "boost_key": key,
                    "multiplier": multiplier,
                    "end_time": end_time,
                }
            },
            upsert=True,
        )
        self._boost_cache_time = 0.0  # Invalidate cache
        logger.info(f"Global Boost Activated: {key} x{multiplier} for {duration_hours}h")

    def clear_global_boosts(self):
        """Removes all active global boosts."""
        self._col("global_boosts").delete_many({})
        self._boost_cache_time = 0.0  # Invalidate cache
        logger.info("All Global Boosts cleared.")

    # ============================================================
    # ACTIVE BUFFS
    # ============================================================

    def add_active_buff(
        self,
        discord_id: int,
        buff_id: str,
        name: str,
        stat: str,
        amount: float,
        duration_s: int,
    ):
        """Adds a buff to the player."""
        # Equilibrium Fix: Prevent stacking of same buff name (Refresh instead)
        self._col("active_buffs").delete_many({"discord_id": discord_id, "name": name})

        end_time = (WorldTime.now() + datetime.timedelta(seconds=duration_s)).isoformat()
        self._col("active_buffs").insert_one(
            {
                "discord_id": discord_id,
                "buff_id": buff_id,
                "name": name,
                "stat": stat,
                "amount": amount,
                "end_time": end_time,
            }
        )

    def add_active_buffs_bulk(self, discord_id: int, buffs: list[dict]):
        """
        Adds multiple buffs to the player in a single transaction.
        Optimized to replace 2*N queries with 2 queries.
        buffs structure: [{"buff_id": ..., "name": ..., "stat": ..., "amount": ..., "duration_s": ...}]
        """
        if not buffs:
            return

        # 1. Identify unique buff names to clear (Prevent stacking by name)
        unique_names = list({b["name"] for b in buffs})

        # 2. Batch Delete existing buffs with these names
        self._col("active_buffs").delete_many(
            {"discord_id": discord_id, "name": {"$in": unique_names}}
        )

        # 3. Calculate End Times and Prepare Documents
        now = WorldTime.now()
        docs = []
        for b in buffs:
            end_time = (now + datetime.timedelta(seconds=b["duration_s"])).isoformat()
            docs.append(
                {
                    "discord_id": discord_id,
                    "buff_id": b.get("buff_id"),
                    "name": b["name"],
                    "stat": b["stat"],
                    "amount": b["amount"],
                    "end_time": end_time,
                }
            )

        # 4. Batch Insert
        if docs:
            self._col("active_buffs").insert_many(docs)

    def get_active_buffs(self, discord_id: int) -> list[dict[str, Any]]:
        """Fetches active buffs for the player."""
        now = WorldTime.now().isoformat()
        return list(
            self._col("active_buffs").find(
                {"discord_id": discord_id, "end_time": {"$gt": now}},
                {"_id": 0},
            )
        )

    def clear_expired_buffs(self, discord_id: int):
        """Removes expired buffs."""
        now = WorldTime.now().isoformat()
        self._col("active_buffs").delete_many(
            {"discord_id": discord_id, "end_time": {"$lte": now}},
        )

    # ============================================================
    # ADVENTURE SESSIONS (New methods for external call sites)
    # ============================================================

    def delete_adventure_session(self, discord_id: int, active: int | None = None):
        """Deletes adventure sessions for a player."""
        query = {"discord_id": discord_id}
        if active is not None:
            query["active"] = active
        self._col("adventure_sessions").delete_many(query)

    def insert_adventure_session(
        self,
        discord_id: int,
        location_id: str,
        start_time: str,
        end_time: str,
        duration_minutes: int,
        supplies: dict[str, int] | None = None,
        status: str = "in_progress",
    ):
        """Creates a new adventure session."""
        # Remove any existing sessions first (replace behavior)
        self._col("adventure_sessions").delete_many({"discord_id": discord_id})
        self._col("adventure_sessions").insert_one(
            {
                "discord_id": discord_id,
                "location_id": location_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": duration_minutes,
                "active": 1,
                "status": status,
                "supplies": supplies or {},
                "logs": "[]",
                "loot_collected": "{}",
                "active_monster_json": None,
                "steps_completed": 0,
                "version": 1,
            }
        )

    def get_adventures_ending_before(self, timestamp_iso: str) -> list[dict]:
        """Fetches active adventures that end before the given timestamp."""
        return list(
            self._col("adventure_sessions").find(
                {
                    "active": 1,
                    "status": "in_progress",
                    "end_time": {"$lte": timestamp_iso},
                },
                {"_id": 0},
            )
        )

    def update_adventure_status(self, discord_id: int, status: str):
        """Updates the status of an active adventure."""
        self._col("adventure_sessions").update_one(
            {"discord_id": discord_id, "active": 1},
            {"$set": {"status": status}},
        )

    def get_active_adventure(self, discord_id: int) -> dict | None:
        """Fetches the active adventure session for a player."""
        return self._col("adventure_sessions").find_one(
            {"discord_id": discord_id, "active": 1},
            {"_id": 0},
        )

    def update_adventure_session(
        self,
        discord_id: int,
        logs: str,
        loot_collected: str,
        active: int,
        active_monster_json: str | None,
        previous_version: int,
        steps_completed: int | None = None,
    ) -> bool:
        """
        Updates an active adventure session with optimistic locking.
        Returns True if successful, False if version mismatch (concurrent update).
        Handles legacy sessions (missing version) by accepting {version: 1} OR {version: exists(False)}.
        """
        query = {"discord_id": discord_id, "active": 1}

        if previous_version == 1:
            # Match version 1 OR missing version field (legacy migration)
            query["$or"] = [{"version": 1}, {"version": {"$exists": False}}]
        else:
            query["version"] = previous_version

        update_fields = {
            "logs": logs,
            "loot_collected": loot_collected,
            "active": active,
            "active_monster_json": active_monster_json,
            "version": previous_version + 1,
        }

        if steps_completed is not None:
            update_fields["steps_completed"] = steps_completed

        result = self._col("adventure_sessions").update_one(
            query,
            {"$set": update_fields},
        )
        return result.modified_count > 0

    def end_adventure_session(self, discord_id: int):
        """Marks all adventure sessions as inactive."""
        self._col("adventure_sessions").update_many(
            {"discord_id": discord_id},
            {"$set": {"active": 0}},
        )

    # ============================================================
    # INVENTORY (New methods for external call sites)
    # ============================================================

    def calculate_inventory_limit(self, discord_id: int) -> int:
        """
        Calculates dynamic inventory limit based on player stats (STR/DEX).
        Delegates to PlayerStats.max_inventory_slots.
        """
        # Avoid circular import
        from game_systems.player.player_stats import PlayerStats

        stats_json = self.get_player_stats_json(discord_id)
        if not stats_json:
            return BASE_INVENTORY_SLOTS

        try:
            stats = PlayerStats.from_dict(stats_json)
            return stats.max_inventory_slots
        except Exception as e:
            logger.error(f"Error calculating inventory limit for {discord_id}: {e}")
            return BASE_INVENTORY_SLOTS

    def get_inventory_slot_count(self, discord_id: int) -> int:
        """Counts the number of distinct item slots (documents) used (excluding equipped)."""
        return self._col("inventory").count_documents({"discord_id": discord_id, "equipped": {"$ne": 1}})

    def get_inventory_items(
        self, discord_id: int, item_type: str | None = None, equipped: int | None = None
    ) -> list[dict]:
        """Fetches inventory items with optional filters."""
        query: dict[str, Any] = {"discord_id": discord_id}
        if item_type is not None:
            query["item_type"] = item_type
        if equipped is not None:
            query["equipped"] = equipped
        return list(self._col("inventory").find(query, {"_id": 0}))

    def get_inventory_item_by_id(self, inv_id: int, discord_id: int) -> dict | None:
        """Fetches a single inventory item by its id."""
        return self._col("inventory").find_one(
            {"id": inv_id, "discord_id": discord_id},
            {"_id": 0},
        )

    def find_stackable_item(
        self,
        discord_id: int,
        item_key: str,
        rarity: str,
        slot: str | None = None,
        item_source_table: str | None = None,
        equipped: int = 0,
        max_stack: int | None = None,
    ) -> dict | None:
        """Finds an existing unequipped stack to merge into."""
        query = {
            "discord_id": discord_id,
            "item_key": item_key,
            "rarity": rarity,
            "slot": slot,
            "item_source_table": item_source_table,
            "equipped": equipped,
        }
        if max_stack is not None:
            query["count"] = {"$lt": max_stack}

        return self._col("inventory").find_one(query, {"_id": 0})

    def add_inventory_item(
        self,
        discord_id: int,
        item_key: str,
        item_name: str,
        item_type: str,
        rarity: str,
        amount: int = 1,
        slot: str | None = None,
        item_source_table: str | None = None,
    ) -> bool:
        """Adds an item to inventory with stack merging. Returns True if successful, False if full."""
        # Determine Max Stack
        if item_type == "consumable":
            max_stack = MAX_STACK_CONSUMABLE
        elif item_type == "material":
            max_stack = MAX_STACK_MATERIAL
        elif item_type == "equipment":
            max_stack = MAX_STACK_EQUIPMENT
        else:
            max_stack = MAX_STACK_DEFAULT

        # 1. Try to merge into an existing stack that has space
        existing = self.find_stackable_item(
            discord_id,
            item_key,
            rarity,
            slot,
            item_source_table,
            max_stack=max_stack,
        )

        amount_to_add_to_stack = 0
        if existing:
            space = max(0, max_stack - existing["count"])
            amount_to_add_to_stack = min(amount, space)

        remainder = amount - amount_to_add_to_stack
        needed_new_slots = 0
        if remainder > 0:
            needed_new_slots = math.ceil(remainder / max_stack)

        # 2. Check Capacity
        if needed_new_slots > 0:
            current_slots = self.get_inventory_slot_count(discord_id)
            max_slots = self.calculate_inventory_limit(discord_id)
            available_slots = max(0, max_slots - current_slots)
            if needed_new_slots > available_slots:
                return False

        # 3. Apply Updates
        if amount_to_add_to_stack > 0 and existing:
            self._col("inventory").update_one(
                {"id": existing["id"]},
                {"$inc": {"count": amount_to_add_to_stack}},
            )

        if remainder > 0:
            # Insert new stacks
            # Reserve IDs in bulk
            counter_doc = self._col("counters").find_one_and_update(
                {"_id": "inventory_id"},
                {"$inc": {"seq": needed_new_slots}},
                upsert=True,
                return_document=True,
            )
            end_seq = counter_doc["seq"]
            start_seq = end_seq - needed_new_slots + 1

            new_docs = []
            current_remainder = remainder
            for i in range(needed_new_slots):
                stack_amount = min(current_remainder, max_stack)
                new_docs.append(
                    {
                        "id": start_seq + i,
                        "discord_id": discord_id,
                        "item_key": item_key,
                        "item_name": item_name,
                        "item_type": item_type,
                        "rarity": rarity,
                        "slot": slot,
                        "item_source_table": item_source_table,
                        "count": stack_amount,
                        "equipped": 0,
                    }
                )
                current_remainder -= stack_amount

            if new_docs:
                self._col("inventory").insert_many(new_docs)

        return True

    def add_inventory_items_bulk(self, discord_id: int, items: list[dict]) -> list[dict]:
        """
        Efficiently adds multiple items to inventory.
        Handles stacking and bulk insertion to reduce DB round-trips.
        Returns a list of items that could NOT be added due to slot limits.
        """
        if not items:
            return []

        # 1. Consolidate items to minimize operations
        consolidated = {}
        for item in items:
            # Key matches find_stackable_item logic: (item_key, rarity, slot, item_source_table)
            key = (
                item["item_key"],
                item["rarity"],
                item.get("slot"),
                item.get("item_source_table"),
            )
            if key not in consolidated:
                consolidated[key] = {
                    "item_key": item["item_key"],
                    "item_name": item["item_name"],
                    "item_type": item["item_type"],
                    "rarity": item["rarity"],
                    "slot": item.get("slot"),
                    "item_source_table": item.get("item_source_table"),
                    "amount": 0,
                }
            consolidated[key]["amount"] += item["amount"]

        # 2. Fetch all relevant existing stacks
        item_keys = [k[0] for k in consolidated.keys()]
        query = {
            "discord_id": discord_id,
            "equipped": 0,
            "item_key": {"$in": item_keys},
        }
        # Fetch existing stacks, sort by count descending (fill almost full stacks first? No, actually sort by count ASC to fill small stacks first)
        # Sort doesn't strictly matter for correctness, just efficiency.
        existing_docs = list(self._col("inventory").find(query).sort("count", 1))

        # Map existing docs: key -> list of docs
        existing_map = {}
        for doc in existing_docs:
            key = (
                doc["item_key"],
                doc["rarity"],
                doc.get("slot"),
                doc.get("item_source_table"),
            )
            if key not in existing_map:
                existing_map[key] = []
            existing_map[key].append(doc)

        operations = []
        new_items_data = []
        failed_items = []

        current_slots = self.get_inventory_slot_count(discord_id)
        max_slots = self.calculate_inventory_limit(discord_id)
        available_slots = max(0, max_slots - current_slots)

        # 3. Process each consolidated item group
        for key, item_data in consolidated.items():
            amount = item_data["amount"]
            item_type = item_data["item_type"]

            # Determine Max Stack
            if item_type == "consumable":
                max_stack = MAX_STACK_CONSUMABLE
            elif item_type == "material":
                max_stack = MAX_STACK_MATERIAL
            elif item_type == "equipment":
                max_stack = MAX_STACK_EQUIPMENT
            else:
                max_stack = MAX_STACK_DEFAULT

            # A. Fill Existing Stacks
            existing_stacks = existing_map.get(key, [])
            for stack in existing_stacks:
                if amount <= 0:
                    break

                current_count = stack["count"]
                space = max(0, max_stack - current_count)

                if space > 0:
                    add_to_stack = min(amount, space)
                    operations.append(UpdateOne({"id": stack["id"]}, {"$inc": {"count": add_to_stack}}))
                    amount -= add_to_stack

            # B. Create New Stacks for Remainder
            if amount > 0:
                needed_stacks = math.ceil(amount / max_stack)

                if needed_stacks <= available_slots:
                    # Queue inserts
                    available_slots -= needed_stacks

                    # Prepare data (will assign IDs later)
                    current_remainder = amount
                    for _ in range(needed_stacks):
                        stack_amount = min(current_remainder, max_stack)
                        new_items_data.append(
                            {
                                "item_key": item_data["item_key"],
                                "item_name": item_data["item_name"],
                                "item_type": item_data["item_type"],
                                "rarity": item_data["rarity"],
                                "slot": item_data.get("slot"),
                                "item_source_table": item_data.get("item_source_table"),
                                "amount": stack_amount,
                            }
                        )
                        current_remainder -= stack_amount
                else:
                    # FAILED - Not enough slots
                    # Note: We return the REMAINDER as failed. The parts filled into existing stacks are kept.
                    failed_items.append(
                        {
                            "item_key": item_data["item_key"],
                            "item_name": item_data["item_name"],
                            "amount": amount,
                            "reason": "Inventory Full",
                        }
                    )

        # 4. Generate IDs for new items
        if new_items_data:
            count = len(new_items_data)
            counter_doc = self._col("counters").find_one_and_update(
                {"_id": "inventory_id"},
                {"$inc": {"seq": count}},
                upsert=True,
                return_document=True,
            )
            end_seq = counter_doc["seq"]
            start_seq = end_seq - count + 1

            for i, item_data in enumerate(new_items_data):
                new_id = start_seq + i
                operations.append(
                    InsertOne(
                        {
                            "id": new_id,
                            "discord_id": discord_id,
                            "item_key": item_data["item_key"],
                            "item_name": item_data["item_name"],
                            "item_type": item_data["item_type"],
                            "rarity": item_data["rarity"],
                            "slot": item_data["slot"],
                            "item_source_table": item_data["item_source_table"],
                            "count": item_data["amount"],
                            "equipped": 0,
                        }
                    )
                )

        # 5. Execute
        if operations:
            self._col("inventory").bulk_write(operations)
            logger.info(f"Bulk added items for {discord_id}. Failures: {len(failed_items)}")

        return failed_items

    def get_inventory_item_count(self, discord_id: int, item_key: str) -> int:
        """Returns the total count of an item across all stacks."""
        pipeline = [
            {"$match": {"discord_id": discord_id, "item_key": item_key}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}},
        ]
        result = list(self._col("inventory").aggregate(pipeline))
        return result[0]["total"] if result else 0

    def consume_item_atomic(self, inv_id: int, amount: int = 1) -> bool:
        """
        Atomically decrements item count if sufficient quantity exists.
        Returns True if successful, False if insufficient.
        """
        # Attempt to decrement count only if currently >= amount
        result = self._col("inventory").find_one_and_update(
            {"id": inv_id, "count": {"$gte": amount}},
            {"$inc": {"count": -amount}},
            return_document=True,  # Return the new document
        )

        if result:
            # If count reached 0, clean up the item
            if result["count"] == 0:
                # Use stricter filter to avoid deleting if count increased concurrently
                self._col("inventory").delete_one({"id": inv_id, "count": 0})
            return True
        return False

    def remove_inventory_item(self, discord_id: int, item_key: str, amount: int = 1) -> bool:
        """
        Removes items from inventory. Prioritizes unequipped stacks.
        Returns True if successful, False if insufficient quantity.
        """
        if amount <= 0:
            return False

        # 1. Check total count
        total = self.get_inventory_item_count(discord_id, item_key)
        if total < amount:
            return False

        # 2. Fetch all stacks, sorted by equipped (0 first) then count (asc)
        stacks = list(
            self._col("inventory")
            .find(
                {"discord_id": discord_id, "item_key": item_key},
            )
            .sort([("equipped", 1), ("count", 1)])
        )

        remaining_to_remove = amount

        for stack in stacks:
            if remaining_to_remove <= 0:
                break

            remove_from_stack = min(stack["count"], remaining_to_remove)

            if remove_from_stack == stack["count"]:
                self._col("inventory").delete_one({"id": stack["id"]})
            else:
                self._col("inventory").update_one({"id": stack["id"]}, {"$inc": {"count": -remove_from_stack}})

            remaining_to_remove -= remove_from_stack

        return remaining_to_remove == 0

    def _next_inventory_id(self) -> int:
        """Generates the next auto-increment ID for inventory."""
        counter = self._col("counters").find_one_and_update(
            {"_id": "inventory_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        return counter["seq"]

    def update_inventory_count(self, inv_id: int, new_count: int):
        """Updates item count."""
        self._col("inventory").update_one({"id": inv_id}, {"$set": {"count": new_count}})

    def increment_inventory_count(self, inv_id: int, amount: int = 1):
        """Increments item count."""
        self._col("inventory").update_one({"id": inv_id}, {"$inc": {"count": amount}})

    def decrement_inventory_count(self, inv_id: int, amount: int = 1):
        """Decrements item count. Does NOT delete at zero."""
        self._col("inventory").update_one({"id": inv_id}, {"$inc": {"count": -amount}})

    def delete_inventory_item(self, inv_id: int):
        """Deletes an inventory item by id."""
        self._col("inventory").delete_one({"id": inv_id})

    def delete_inventory_by_type(self, discord_id: int, item_type: str):
        """Deletes all inventory items of a specific type for a player."""
        self._col("inventory").delete_many({"discord_id": discord_id, "item_type": item_type})

    def set_item_equipped(self, inv_id: int, equipped: int):
        """Sets the equipped status of an inventory item."""
        self._col("inventory").update_one({"id": inv_id}, {"$set": {"equipped": equipped}})

    def get_equipped_in_slot(self, discord_id: int, slot: str) -> dict | None:
        """Finds the currently equipped item in a specific slot."""
        return self._col("inventory").find_one(
            {"discord_id": discord_id, "slot": slot, "equipped": 1},
            {"_id": 0},
        )

    def insert_equipped_split(self, discord_id: int, item: dict):
        """Inserts a new equipped single-stack item (for stack splitting on equip)."""
        new_id = self._next_inventory_id()
        self._col("inventory").insert_one(
            {
                "id": new_id,
                "discord_id": discord_id,
                "item_key": item["item_key"],
                "item_name": item["item_name"],
                "item_type": item["item_type"],
                "rarity": item["rarity"],
                "slot": item["slot"],
                "item_source_table": item.get("item_source_table"),
                "count": 1,
                "equipped": 1,
            }
        )

    def split_stack_to_equipped(self, discord_id: int, source_inv_id: int, item: dict) -> bool:
        """
        Atomically splits 1 item from a stack and inserts it as a new EQUIPPED item.
        Handles failures via compensation (refund).
        """
        # 1. Decrement Source Stack (Atomic Check & Update)
        result = self._col("inventory").update_one({"id": source_inv_id, "count": {"$gt": 1}}, {"$inc": {"count": -1}})

        if result.modified_count == 0:
            return False

        try:
            # 2. Insert New Equipped Item
            self.insert_equipped_split(discord_id, item)
            return True
        except Exception as e:
            logger.error(f"Failed to split stack {source_inv_id} for {discord_id}: {e}")
            # 3. Compensation: Refund the item
            self._col("inventory").update_one({"id": source_inv_id}, {"$inc": {"count": 1}})
            return False

    # ============================================================
    # EQUIPMENT DATA (New methods for external call sites)
    # ============================================================

    def get_equipment_id_by_name(self, name: str) -> int | None:
        """Finds the database ID for an equipment item by its name."""
        doc = self._col("equipment").find_one({"name": name}, {"id": 1})
        if doc:
            return doc["id"]
        return None

    def get_item_from_source_table(self, table_name: str, item_id: str) -> dict | None:
        """Fetches an item from equipment or class_equipment collection."""
        valid_tables = {"equipment", "class_equipment"}
        if table_name not in valid_tables:
            return None
        return self._col(table_name).find_one({"id": item_id}, {"_id": 0})

    # ============================================================
    # QUEST SYSTEM (New methods for external call sites)
    # ============================================================

    def get_quests_by_tier(self, tier: str) -> list[dict]:
        """Fetches all quests for a given tier/rank."""
        return list(
            self._col("quests").find(
                {"tier": tier},
                {"_id": 0, "id": 1, "title": 1, "tier": 1, "summary": 1},
            )
        )

    def get_quest_details(self, quest_id: int) -> dict | None:
        """Fetches full quest details."""
        return self._col("quests").find_one({"id": quest_id}, {"_id": 0})

    def get_player_quest_ids(self, discord_id: int) -> set[int]:
        """Fetches all quest IDs a player has (active or completed)."""
        docs = self._col("player_quests").find(
            {"discord_id": discord_id},
            {"_id": 0, "quest_id": 1},
        )
        return {d["quest_id"] for d in docs}

    def get_player_quests_joined(self, discord_id: int) -> list[dict]:
        """Fetches in-progress quests with quest details."""
        pq_docs = list(
            self._col("player_quests").find(
                {"discord_id": discord_id, "status": "in_progress"},
                {"_id": 0},
            )
        )
        results = []
        for pq in pq_docs:
            quest = self._col("quests").find_one({"id": pq["quest_id"]}, {"_id": 0})
            if quest:
                results.append(
                    {
                        "id": quest["id"],
                        "title": quest["title"],
                        "summary": quest.get("summary", ""),
                        "location": quest.get("location"),
                        "status": pq["status"],
                        "progress": pq["progress"],
                        "objectives": quest.get("objectives", "{}"),
                    }
                )
        return results

    def player_has_quest(self, discord_id: int, quest_id: int) -> bool:
        """Checks if a player already has a specific quest."""
        return (
            self._col("player_quests").find_one(
                {"discord_id": discord_id, "quest_id": quest_id},
                {"_id": 1},
            )
            is not None
        )

    def get_quest_objectives(self, quest_id: int) -> str | None:
        """Fetches raw objectives JSON string for a quest."""
        doc = self._col("quests").find_one({"id": quest_id}, {"_id": 0, "objectives": 1})
        return doc["objectives"] if doc else None

    def insert_player_quest(self, discord_id: int, quest_id: int, status: str, progress: str):
        """Inserts a new player quest record."""
        self._col("player_quests").insert_one(
            {
                "discord_id": discord_id,
                "quest_id": quest_id,
                "status": status,
                "progress": progress,
            }
        )

    def get_player_quest_progress(self, discord_id: int, quest_id: int) -> str | None:
        """Fetches progress JSON string for a player's quest."""
        doc = self._col("player_quests").find_one(
            {"discord_id": discord_id, "quest_id": quest_id},
            {"_id": 0, "progress": 1},
        )
        return doc["progress"] if doc else None

    def set_player_quest_progress(self, discord_id: int, quest_id: int, progress: str):
        """Updates quest progress."""
        self._col("player_quests").update_one(
            {"discord_id": discord_id, "quest_id": quest_id},
            {"$set": {"progress": progress}},
        )

    def get_player_quest_with_objectives(self, discord_id: int, quest_id: int) -> dict | None:
        """Fetches a player quest with quest objectives (for completion check)."""
        pq = self._col("player_quests").find_one(
            {"discord_id": discord_id, "quest_id": quest_id, "status": "in_progress"},
            {"_id": 0},
        )
        if not pq:
            return None
        quest = self._col("quests").find_one({"id": quest_id}, {"_id": 0, "objectives": 1})
        if not quest:
            return None
        return {"progress": pq["progress"], "objectives": quest["objectives"]}

    def complete_player_quest(self, discord_id: int, quest_id: int):
        """Marks a quest as completed."""
        self._col("player_quests").update_one(
            {"discord_id": discord_id, "quest_id": quest_id},
            {"$set": {"status": "completed"}},
        )

    # ============================================================
    # GUILD (New methods for external call sites)
    # ============================================================

    def get_guild_rank(self, discord_id: int) -> str | None:
        """Fetches the player's current guild rank."""
        doc = self._col("guild_members").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "rank": 1},
        )
        return doc["rank"] if doc else None

    def update_guild_rank(self, discord_id: int, new_rank: str):
        """Updates the player's guild rank."""
        self._col("guild_members").update_one(
            {"discord_id": discord_id},
            {"$set": {"rank": new_rank}},
        )

    def insert_guild_member(self, discord_id: int, rank: str = "F"):
        """Registers a new guild member."""
        self._col("guild_members").insert_one(
            {
                "discord_id": discord_id,
                "rank": rank,
                "join_date": WorldTime.now().isoformat(),
                "merit_points": 0,
                "quests_completed": 0,
                "normal_kills": 0,
                "elite_kills": 0,
                "boss_kills": 0,
            }
        )

    def increment_guild_stat(self, discord_id: int, field: str, amount: int = 1):
        """Increments a guild member stat field (merit_points, quests_completed, kills)."""
        valid_fields = {
            "merit_points",
            "quests_completed",
            "normal_kills",
            "elite_kills",
            "boss_kills",
        }
        if field not in valid_fields:
            return
        self._col("guild_members").update_one(
            {"discord_id": discord_id},
            {"$inc": {field: amount}},
        )

    # ============================================================
    # PLAYER SKILLS (New methods for external call sites)
    # ============================================================

    def get_player_skill_levels(self, discord_id: int) -> dict[str, int]:
        """Returns {skill_key: skill_level} for a player."""
        docs = self._col("player_skills").find({"discord_id": discord_id}, {"_id": 0})
        return {d["skill_key"]: d["skill_level"] for d in docs}

    def get_default_skills(self, class_id: int) -> list[str]:
        """Fetches skill key_ids with learn_cost=0 for a class."""
        docs = self._col("skills").find(
            {"class_id": class_id, "learn_cost": 0},
            {"_id": 0, "key_id": 1},
        )
        return [d["key_id"] for d in docs]

    def insert_player_skill(self, discord_id: int, skill_key: str, skill_level: int = 1):
        """Inserts a new player skill."""
        self._col("player_skills").insert_one(
            {
                "discord_id": discord_id,
                "skill_key": skill_key,
                "skill_level": skill_level,
                "skill_exp": 0.0,
            }
        )

    def player_has_skill(self, discord_id: int, skill_key: str) -> bool:
        """Checks if a player has learned a specific skill."""
        return (
            self._col("player_skills").find_one(
                {"discord_id": discord_id, "skill_key": skill_key},
                {"_id": 1},
            )
            is not None
        )

    def get_player_skill_row(self, discord_id: int, skill_key: str) -> dict | None:
        """Fetches a single player skill row."""
        return self._col("player_skills").find_one(
            {"discord_id": discord_id, "skill_key": skill_key},
            {"_id": 0},
        )

    def update_player_skill(
        self,
        discord_id: int,
        skill_key: str,
        skill_level: int | None = None,
        skill_exp: float | None = None,
    ):
        """Updates skill level and/or exp."""
        update: dict[str, Any] = {}
        if skill_level is not None:
            update["skill_level"] = skill_level
        if skill_exp is not None:
            update["skill_exp"] = skill_exp
        if update:
            self._col("player_skills").update_one(
                {"discord_id": discord_id, "skill_key": skill_key},
                {"$set": update},
            )

    def get_skill_with_definition(self, discord_id: int, skill_key: str) -> dict | None:
        """Fetches a player skill joined with its definition."""
        ps = self._col("player_skills").find_one(
            {"discord_id": discord_id, "skill_key": skill_key},
            {"_id": 0},
        )
        if not ps:
            return None

        self._ensure_skill_cache()
        skill_def = self._skill_cache.get(skill_key)

        if not skill_def:
            return None
        return {
            "skill_level": ps["skill_level"],
            "skill_exp": ps.get("skill_exp", 0),
            "name": skill_def["name"],
        }

    # ============================================================
    # STAT EXP / PRACTICE (New methods for external call sites)
    # ============================================================

    def get_stat_exp_row(self, discord_id: int) -> dict | None:
        """Fetches stats_json and all exp columns."""
        return self._col("stats").find_one({"discord_id": discord_id}, {"_id": 0})

    def update_stat_exp(
        self,
        discord_id: int,
        old_stats_json_str: str,
        old_exps: dict[str, float],
        stats_json_str: str,
        str_exp: float,
        end_exp: float,
        dex_exp: float,
        agi_exp: float,
        mag_exp: float,
        lck_exp: float,
    ) -> bool:
        """
        Updates stats JSON and all practice EXP columns with optimistic locking.
        Returns True if successful, False if stats_json OR exp values changed concurrently.
        """
        query = {
            "discord_id": discord_id,
            "stats_json": old_stats_json_str,
        }
        query.update(old_exps)  # Add expected previous exp values to filter

        result = self._col("stats").update_one(
            query,
            {
                "$set": {
                    "stats_json": stats_json_str,
                    "str_exp": str_exp,
                    "end_exp": end_exp,
                    "dex_exp": dex_exp,
                    "agi_exp": agi_exp,
                    "mag_exp": mag_exp,
                    "lck_exp": lck_exp,
                }
            },
        )
        return result.modified_count > 0

    # ============================================================
    # PLAYER UPDATES (New methods for external call sites)
    # ============================================================

    def update_player_fields(self, discord_id: int, **fields):
        """Generic player field update."""
        if fields:
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$set": fields},
            )

    def update_player_mixed(
        self,
        discord_id: int,
        set_fields: dict[str, Any] | None = None,
        inc_fields: dict[str, Any] | None = None,
    ):
        """Updates player fields with both $set and $inc in a single operation."""
        update: dict[str, Any] = {}
        if set_fields:
            update["$set"] = set_fields
        if inc_fields:
            update["$inc"] = inc_fields

        if update:
            self._col("players").update_one(
                {"discord_id": discord_id},
                update,
            )

    def increment_player_fields(self, discord_id: int, **fields):
        """Generic player field increment (e.g., aurum, experience, vestige_pool)."""
        if fields:
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": fields},
            )

    def get_player_field(self, discord_id: int, field: str) -> Any:
        """Fetches a single player field."""
        doc = self._col("players").find_one(
            {"discord_id": discord_id},
            {"_id": 0, field: 1},
        )
        return doc.get(field) if doc else None

    def set_player_field(self, discord_id: int, field: str, value: Any):
        """Sets a single player field."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$set": {field: value}},
        )

    def update_player_vestige_and_vitals(self, discord_id: int, vestige: int, hp: int, mp: int):
        """Atomically updates vestige_pool, current_hp, and current_mp."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$set": {"vestige_pool": vestige, "current_hp": hp, "current_mp": mp}},
        )

    def get_equipped_items(self, discord_id: int) -> list[dict]:
        """Fetches all currently equipped items for a player."""
        return list(
            self._col("inventory").find(
                {"discord_id": discord_id, "equipped": 1},
                {"_id": 0},
            )
        )

    def get_all_player_skills(self, discord_id: int) -> list[dict]:
        """Fetches all player skill rows (raw, without joining definitions)."""
        return list(
            self._col("player_skills").find(
                {"discord_id": discord_id},
                {"_id": 0},
            )
        )

    def get_guild_member(self, discord_id: int) -> dict | None:
        """Alias for get_guild_member_data."""
        return self.get_guild_member_data(discord_id)

    def get_guild_member_field(self, discord_id: int, field: str) -> Any:
        """Fetches a single guild member field."""
        doc = self._col("guild_members").find_one(
            {"discord_id": discord_id},
            {"_id": 0, field: 1},
        )
        return doc.get(field) if doc else None

    def update_guild_member_rank(self, discord_id: int, new_rank: str):
        """Alias for update_guild_rank."""
        self.update_guild_rank(discord_id, new_rank)

    def get_inventory_item(self, discord_id: int, inv_id: int) -> dict | None:
        """Alias for get_inventory_item_by_id with swapped arg order."""
        return self.get_inventory_item_by_id(inv_id, discord_id)

    def get_default_skill_keys(self, class_id: int) -> list[str]:
        """Alias for get_default_skills."""
        return self.get_default_skills(class_id)

    def increment_kill_counter(self, discord_id: int, kill_type: str, amount: int = 1):
        """Increments kill counters on guild_members (normal_kills, elite_kills, boss_kills)."""
        valid = {"normal_kills", "elite_kills", "boss_kills"}
        if kill_type in valid:
            self.increment_guild_stat(discord_id, kill_type, amount)

    def increment_specific_monster_kill(self, discord_id: int, monster_name: str, amount: int = 1):
        """Increments a specific monster kill count in the stats record."""
        # Sanitize name for MongoDB field key (remove dots and $)
        safe_name = monster_name.replace(".", "").replace("$", "")
        self._col("stats").update_one(
            {"discord_id": discord_id},
            {"$inc": {f"monster_kills.{safe_name}": amount}},
            upsert=True,
        )

    def get_specific_monster_kills(self, discord_id: int) -> dict[str, int]:
        """Fetches the dictionary of specific monster kills."""
        doc = self._col("stats").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "monster_kills": 1},
        )
        return doc.get("monster_kills", {}) if doc else {}

    # ============================================================
    # REWARD SYSTEM (New methods for external call sites)
    # ============================================================

    def grant_quest_rewards(
        self,
        discord_id: int,
        level: int,
        exp: int,
        exp_to_next: int,
        aurum_add: int,
        vestige_add: int,
        merit_add: int,
        stats_json_str: str,
    ):
        """Atomically grants all quest completion rewards."""
        # Update player
        self._col("players").update_one(
            {"discord_id": discord_id},
            {
                "$set": {"level": level, "experience": exp, "exp_to_next": exp_to_next},
                "$inc": {"aurum": aurum_add, "vestige_pool": vestige_add},
            },
        )
        # Update guild
        self._col("guild_members").update_one(
            {"discord_id": discord_id},
            {"$inc": {"merit_points": merit_add, "quests_completed": 1}},
        )
        # Update stats
        self._col("stats").update_one(
            {"discord_id": discord_id},
            {"$set": {"stats_json": stats_json_str}},
        )

    def deduct_vestige(self, discord_id: int, amount: int) -> bool:
        """
        Safely deducts vestige with a balance check.
        Returns True if successful, False if insufficient funds.
        """
        result = self._col("players").update_one(
            {"discord_id": discord_id, "vestige_pool": {"$gte": amount}},
            {"$inc": {"vestige_pool": -amount}},
        )
        return result.modified_count > 0

    def deduct_aurum(self, discord_id: int, amount: int) -> int | None:
        """
        Safely deducts aurum with a balance check.
        Returns the new balance if successful, None if insufficient funds.
        """
        result = self._col("players").find_one_and_update(
            {"discord_id": discord_id, "aurum": {"$gte": amount}},
            {"$inc": {"aurum": -amount}},
            return_document=True,
        )
        return result["aurum"] if result else None

    def refund_vestige(self, discord_id: int, amount: int):
        """Refunds vestige (e.g., after a failed optimistic update)."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$inc": {"vestige_pool": amount}},
        )

    def update_player_stats_optimistic(self, discord_id: int, old_json_str: str, new_stats_data: dict) -> bool:
        """
        Updates player stats only if the current stats_json matches old_json_str.
        Prevents Lost Updates due to race conditions.
        """
        result = self._col("stats").update_one(
            {"discord_id": discord_id, "stats_json": old_json_str},
            {"$set": {"stats_json": json.dumps(new_stats_data)}},
        )
        return result.modified_count > 0

    def update_player_vitals(self, discord_id: int, hp: int, mp: int):
        """Updates just HP and MP."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {"$set": {"current_hp": hp, "current_mp": mp}},
        )

    def add_reward_item_internal(self, discord_id: int, item_key: str, item_data: dict):
        """Adds a reward item (consumable) within reward processing."""
        existing = self._col("inventory").find_one(
            {
                "discord_id": discord_id,
                "item_key": item_key,
                "rarity": item_data["rarity"],
                "equipped": 0,
            }
        )
        if existing:
            self._col("inventory").update_one(
                {"id": existing["id"]},
                {"$inc": {"count": 1}},
            )
        else:
            new_id = self._next_inventory_id()
            self._col("inventory").insert_one(
                {
                    "id": new_id,
                    "discord_id": discord_id,
                    "item_key": item_key,
                    "item_name": item_data["name"],
                    "item_type": "consumable",
                    "rarity": item_data["rarity"],
                    "slot": None,
                    "item_source_table": None,
                    "count": 1,
                    "equipped": 0,
                }
            )

    # ============================================================
    # SHOP (New methods for external call sites)
    # ============================================================

    def purchase_item(self, discord_id: int, item_key: str, item_data: dict, price: int) -> tuple[bool, Any, int]:
        """Atomic purchase: deducts gold and adds item. Includes refund on failure."""
        # 1. Atomic Deduction
        new_aurum = self.deduct_aurum(discord_id, price)
        if new_aurum is None:
            return (False, "Insufficient Aurum.", 0)

        # 2. Add item to inventory with Refund Logic
        try:
            success = self.add_inventory_item(
                discord_id,
                item_key,
                item_data["name"],
                "consumable",
                item_data["rarity"],
                1,
            )

            if success:
                return (True, item_data, new_aurum)
            else:
                # Inventory Full -> Refund
                self._col("players").update_one(
                    {"discord_id": discord_id},
                    {"$inc": {"aurum": price}},
                )
                refunded_balance = new_aurum + price
                return (False, "Inventory Full.", refunded_balance)

        except Exception as e:
            logger.error(f"Purchase failed for {discord_id}, refunding {price}: {e}")

            # REFUND
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": {"aurum": price}},
            )
            # Re-calculate balance manually since we refunded
            refunded_balance = new_aurum + price

            return (False, "System error (refunded).", refunded_balance)

    # ============================================================
    # INFIRMARY (New methods for external call sites)
    # ============================================================

    @staticmethod
    def calculate_heal_cost(current_hp: int, current_mp: int, max_hp: int, max_mp: int) -> int:
        """
        Calculates the Aurum cost to restore HP and MP.
        Formula: 2.0 Aurum per missing HP, 3.0 Aurum per missing MP.
        Magic is biologically taxing to restore.
        """
        missing_hp = max(0, max_hp - current_hp)
        missing_mp = max(0, max_mp - current_mp)

        if missing_hp <= 0 and missing_mp <= 0:
            return 0

        return max(1, math.ceil(missing_hp * 2.0 + missing_mp * 3.0))

    def execute_heal(self, discord_id: int, max_hp: int, max_mp: int) -> tuple[bool, str]:
        """Atomically heals a player and deducts gold."""
        player = self._col("players").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "current_hp": 1, "current_mp": 1, "aurum": 1},
        )
        if not player:
            return False, "Player not found."

        current_hp = player["current_hp"]
        current_mp = player["current_mp"]

        if current_hp >= max_hp and current_mp >= max_mp:
            return False, "You are already healthy."

        # Recalculate cost from fresh data using centralized formula
        actual_cost = self.calculate_heal_cost(current_hp, current_mp, max_hp, max_mp)

        if player["aurum"] < actual_cost:
            return False, "Insufficient funds."

        # OPTIMISTIC LOCKING: Ensure HP hasn't changed since read
        # ATOMIC UPDATE: Use $inc for aurum to prevent lost updates
        result = self._col("players").update_one(
            {
                "discord_id": discord_id,
                "current_hp": player["current_hp"],
                "aurum": {"$gte": actual_cost},  # Double-check balance
            },
            {
                "$set": {
                    "current_hp": max_hp,
                    "current_mp": max_mp,
                },
                "$inc": {"aurum": -actual_cost},
            },
        )

        if result.modified_count == 0:
            return False, "Healing failed due to state change. Please try again."

        return True, f"Restored HP/MP for {actual_cost} Aurum."

    # ============================================================
    # STAT UPGRADE (New methods for external call sites)
    # ============================================================

    def execute_stat_upgrade(
        self,
        discord_id: int,
        new_vestige: int,
        new_hp: int,
        new_mp: int,
        stats_json_str: str,
    ):
        """Atomically applies a stat upgrade."""
        self._col("players").update_one(
            {"discord_id": discord_id},
            {
                "$set": {
                    "vestige_pool": new_vestige,
                    "current_hp": new_hp,
                    "current_mp": new_mp,
                }
            },
        )
        self._col("stats").update_one(
            {"discord_id": discord_id},
            {"$set": {"stats_json": stats_json_str}},
        )

    # ============================================================
    # SKILL TRAINER (New methods for external call sites)
    # ============================================================

    def learn_skill(self, discord_id: int, skill_key: str, cost: int) -> tuple[bool, str]:
        """Atomically learns a new skill (deducts vestige, inserts skill)."""
        if self.player_has_skill(discord_id, skill_key):
            return False, "Skill already learned."

        # 1. Optimistic Deduction (Atomic Check & Update)
        result = self._col("players").update_one(
            {"discord_id": discord_id, "vestige_pool": {"$gte": cost}},
            {"$inc": {"vestige_pool": -cost}},
        )

        if result.modified_count == 0:
            return False, "Insufficient Vestige."

        # 2. Insert Skill
        try:
            self.insert_player_skill(discord_id, skill_key)
            return True, "Skill Learned!"
        except DuplicateKeyError:
            # Race condition: Skill was learned concurrently or check failed
            # REFUND VESTIGE
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": {"vestige_pool": cost}},
            )
            return False, "Skill already learned (refunded)."
        except Exception as e:
            # Catch-all for other errors to ensure refund
            logger.error(f"Error learning skill: {e}")
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": {"vestige_pool": cost}},
            )
            return False, "System error (refunded)."

    def upgrade_skill(self, discord_id: int, skill_key: str, cost: int) -> tuple[bool, str, int]:
        """Atomically upgrades a skill (deducts vestige, increments level)."""
        ps = self.get_player_skill_row(discord_id, skill_key)
        if not ps:
            return False, "Skill not learned.", 0

        current_level = ps["skill_level"]

        # 1. Optimistic Deduction (Atomic Check & Update)
        result = self._col("players").update_one(
            {"discord_id": discord_id, "vestige_pool": {"$gte": cost}},
            {"$inc": {"vestige_pool": -cost}},
        )

        if result.modified_count == 0:
            return False, "Insufficient Vestige.", current_level

        # 2. Update Skill Level (Atomic Check on Level)
        # Verify that the level hasn't changed since we calculated the cost
        skill_res = self._col("player_skills").update_one(
            {
                "discord_id": discord_id,
                "skill_key": skill_key,
                "skill_level": current_level,
            },
            {"$inc": {"skill_level": 1}},
        )

        if skill_res.modified_count == 0:
            # Race condition: Level changed concurrently
            # REFUND VESTIGE
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": {"vestige_pool": cost}},
            )
            return (
                False,
                "Skill level changed during transaction. Please try again.",
                current_level,
            )

        return True, "Skill Upgraded!", current_level + 1

    # ============================================================
    # ADMIN (New methods for external call sites)
    # ============================================================

    def admin_grant(self, discord_id: int, exp: int = 0, aurum: int = 0, vestige: int = 0):
        """Admin resource grant."""
        increments = {}
        if exp:
            increments["experience"] = exp
        if aurum:
            increments["aurum"] = aurum
        if vestige:
            increments["vestige_pool"] = vestige
        if increments:
            self._col("players").update_one(
                {"discord_id": discord_id},
                {"$inc": increments},
            )

    # ============================================================
    # PLAYER CREATOR (New methods for external call sites)
    # ============================================================

    def delete_player_full(self, discord_id: int):
        """
        Hard delete of all player data.
        Removes records from: players, stats, inventory, player_skills, player_quests,
        guild_members, active_buffs, adventure_sessions, tournament_scores, player_factions.
        """
        logger.warning(f"Executing FULL DELETE for player {discord_id}")

        self._col("players").delete_one({"discord_id": discord_id})
        self._col("stats").delete_one({"discord_id": discord_id})
        self._col("inventory").delete_many({"discord_id": discord_id})
        self._col("player_skills").delete_many({"discord_id": discord_id})
        self._col("player_quests").delete_many({"discord_id": discord_id})
        self._col("guild_members").delete_one({"discord_id": discord_id})
        self._col("active_buffs").delete_many({"discord_id": discord_id})
        self._col("adventure_sessions").delete_many({"discord_id": discord_id})
        self._col("tournament_scores").delete_many({"discord_id": discord_id})
        self._col("player_factions").delete_one({"discord_id": discord_id})

    def create_player_full(
        self,
        discord_id: int,
        username: str,
        class_id: int,
        stats_json_str: str,
        max_hp: int,
        max_mp: int,
        race: str | None,
        gender: str | None,
        default_skill_keys: list[str],
    ):
        """Atomically creates a full player profile with stats, skills, and guild membership."""
        # Player
        self._col("players").insert_one(
            {
                "discord_id": discord_id,
                "name": username,
                "class_id": class_id,
                "race": race,
                "gender": gender,
                "level": 1,
                "experience": 0,
                "exp_to_next": 1000,
                "current_hp": max_hp,
                "current_mp": max_mp,
                "vestige_pool": 0,
                "aurum": 0,
                "titles": [],
                "active_title": None,
                "crafting_level": 1,
                "crafting_xp": 0,
            }
        )

        # Stats
        self._col("stats").insert_one(
            {
                "discord_id": discord_id,
                "stats_json": stats_json_str,
                "str_exp": 0.0,
                "end_exp": 0.0,
                "dex_exp": 0.0,
                "agi_exp": 0.0,
                "mag_exp": 0.0,
                "lck_exp": 0.0,
            }
        )

        # Default Skills
        skill_docs = [
            {
                "discord_id": discord_id,
                "skill_key": sk,
                "skill_level": 1,
                "skill_exp": 0.0,
            }
            for sk in default_skill_keys
        ]
        if skill_docs:
            # OPTIMIZATION: Use insert_many to perform a single DB round-trip instead of a loop.
            self._col("player_skills").insert_many(skill_docs)

        # Guild Membership
        self.insert_guild_member(discord_id)

    # ============================================================
    # TITLES (New methods for external call sites)
    # ============================================================

    def add_title(self, discord_id: int, title: str) -> bool:
        """
        Adds a title to the player's collection.
        Returns True if the title was newly added, False if already present.
        """
        result = self._col("players").update_one(
            {"discord_id": discord_id},
            {"$addToSet": {"titles": title}},
        )
        return result.modified_count > 0

    def get_titles(self, discord_id: int) -> list[str]:
        """Fetches all titles earned by the player."""
        doc = self._col("players").find_one({"discord_id": discord_id}, {"_id": 0, "titles": 1})
        return doc.get("titles", []) if doc else []

    def set_active_title(self, discord_id: int, title: str | None) -> bool:
        """
        Sets the active title. Verifies the player owns the title.
        Returns True if successful, False if title not owned.
        """
        if title is None:
            self._col("players").update_one({"discord_id": discord_id}, {"$set": {"active_title": None}})
            return True

        # Check ownership
        titles = self.get_titles(discord_id)
        if title not in titles:
            return False

        self._col("players").update_one({"discord_id": discord_id}, {"$set": {"active_title": title}})
        return True

    def get_active_title(self, discord_id: int) -> str | None:
        """Fetches the currently active title."""
        doc = self._col("players").find_one({"discord_id": discord_id}, {"_id": 0, "active_title": 1})
        return doc.get("active_title") if doc else None

    # ============================================================
    # EXPLORATION STATS (New methods for external call sites)
    # ============================================================

    def update_exploration_stats(self, discord_id: int, location_id: str, duration_minutes: int = 0):
        """
        Updates exploration stats: unique locations visited, total expeditions, and duration records.
        """
        self._col("stats").update_one(
            {"discord_id": discord_id},
            {
                "$addToSet": {"unique_locations": location_id},
                "$inc": {
                    "total_expeditions": 1,
                    "total_adventure_minutes": duration_minutes,
                },
                "$max": {"longest_adventure_minutes": duration_minutes},
            },
            upsert=True,
        )

    def get_exploration_stats(self, discord_id: int) -> dict:
        """
        Fetches exploration stats (unique_locations, total_expeditions).
        Returns defaults if not present.
        """
        doc = self._col("stats").find_one(
            {"discord_id": discord_id},
            {"_id": 0, "unique_locations": 1, "total_expeditions": 1},
        )
        if not doc:
            return {"unique_locations": [], "total_expeditions": 0}

        return {
            "unique_locations": doc.get("unique_locations", []),
            "total_expeditions": doc.get("total_expeditions", 0),
        }

    # ============================================================
    # TOURNAMENTS (New methods for external call sites)
    # ============================================================

    def _next_tournament_id(self) -> int:
        """Generates the next auto-increment ID for tournaments."""
        counter = self._col("counters").find_one_and_update(
            {"_id": "tournament_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        return counter["seq"]

    def create_tournament(self, type: str, start_time: str, end_time: str) -> int:
        """Creates a new active tournament."""
        new_id = self._next_tournament_id()
        self._col("tournaments").insert_one(
            {
                "id": new_id,
                "type": type,
                "start_time": start_time,
                "end_time": end_time,
                "active": 1,
            }
        )
        self._tournament_cache_time = 0.0  # Invalidate cache
        return new_id

    def get_active_tournament(self) -> dict | None:
        """Fetches the current active tournament (Cached for 60s)."""
        now_ts = time.time()
        if now_ts - self._tournament_cache_time < 60:
            return self._tournament_cache.copy() if self._tournament_cache else None

        self._tournament_cache = self._col("tournaments").find_one(
            {"active": 1},
            {"_id": 0},
        )
        self._tournament_cache_time = now_ts
        return self._tournament_cache.copy() if self._tournament_cache else None

    def end_active_tournament(self):
        """Marks all active tournaments as inactive."""
        self._col("tournaments").update_many(
            {"active": 1},
            {"$set": {"active": 0}},
        )
        self._tournament_cache_time = 0.0  # Invalidate cache

    def update_tournament_score(self, discord_id: int, tournament_id: int, score_increment: int):
        """Updates (increments) a player's score for a tournament."""
        self._col("tournament_scores").update_one(
            {"discord_id": discord_id, "tournament_id": tournament_id},
            {"$inc": {"score": score_increment}},
            upsert=True,
        )

    def get_tournament_leaderboard(self, tournament_id: int, limit: int = 10) -> list[dict]:
        """Fetches the top players for a tournament."""
        pipeline = [
            {"$match": {"tournament_id": tournament_id}},
            {"$sort": {"score": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "players",
                    "localField": "discord_id",
                    "foreignField": "discord_id",
                    "as": "player_info",
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "discord_id": 1,
                    "score": 1,
                    "name": {"$arrayElemAt": ["$player_info.name", 0]},
                }
            },
        ]
        return list(self._col("tournament_scores").aggregate(pipeline))

    def get_player_tournament_score(self, discord_id: int, tournament_id: int) -> int:
        """Fetches a player's score for a specific tournament."""
        doc = self._col("tournament_scores").find_one(
            {"discord_id": discord_id, "tournament_id": tournament_id},
            {"_id": 0, "score": 1},
        )
        return doc["score"] if doc else 0

    # ============================================================
    # WORLD EVENTS
    # ============================================================

    def get_active_world_event(self) -> dict | None:
        """Fetches the current active world event (Cached for 60s)."""
        now_ts = time.time()
        if now_ts - self._world_event_cache_time < 60:
            return self._world_event_cache.copy() if self._world_event_cache else None

        try:
            self._world_event_cache = self._col("world_events").find_one(
                {"active": 1},
                {"_id": 0},
            )
            self._world_event_cache_time = now_ts
            return self._world_event_cache.copy() if self._world_event_cache else None
        except Exception as e:
            logger.error(f"Error fetching active world event: {e}")
            return None

    def set_active_world_event(self, event_type: str, start_time: str, end_time: str, data: dict | None = None):
        """
        Sets the active world event.
        Ensures only one event is active by deactivating others first.
        """
        self.end_active_world_event()

        self._col("world_events").insert_one(
            {
                "type": event_type,
                "start_time": start_time,
                "end_time": end_time,
                "data": data or {},
                "active": 1,
            }
        )
        self._world_event_cache_time = 0.0  # Invalidate cache

    def end_active_world_event(self):
        """Marks all active world events as inactive."""
        self._col("world_events").update_many(
            {"active": 1},
            {"$set": {"active": 0}},
        )
        self._world_event_cache_time = 0.0  # Invalidate cache

    # ============================================================
    # EQUIPMENT SETS
    # ============================================================

    def save_equipment_set(self, discord_id: int, name: str, items: dict[str, dict]):
        """
        Saves a named equipment set.
        Items dict structure: {slot: {"item_key": key, "rarity": rarity, "name": name}}
        """
        self._col("equipment_sets").update_one(
            {"discord_id": discord_id, "name": name},
            {
                "$set": {
                    "discord_id": discord_id,
                    "name": name,
                    "items": items,
                    "updated_at": WorldTime.now().isoformat(),
                }
            },
            upsert=True,
        )

    def get_equipment_sets(self, discord_id: int) -> list[dict]:
        """Fetches all saved equipment sets for a player."""
        return list(
            self._col("equipment_sets").find(
                {"discord_id": discord_id},
                {"_id": 0},
            )
        )

    def get_equipment_set(self, discord_id: int, name: str) -> dict | None:
        """Fetches a specific equipment set."""
        return self._col("equipment_sets").find_one(
            {"discord_id": discord_id, "name": name},
            {"_id": 0},
        )

    def delete_equipment_set(self, discord_id: int, name: str):
        """Deletes a specific equipment set."""
        self._col("equipment_sets").delete_one({"discord_id": discord_id, "name": name})
