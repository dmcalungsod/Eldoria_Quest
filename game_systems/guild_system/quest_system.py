"""
game_systems/guild_system/quest_system.py

Manages quest tracking, updates, and completion.
Hardened: Atomic transactions and safe state validation.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from database.database_manager import DatabaseManager
from game_systems.guild_system.reward_system import RewardSystem
from game_systems.data.emojis import ERROR, WARNING, CHECK

logger = logging.getLogger("eldoria.quests")

class QuestSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.reward_system = RewardSystem(db_manager)

    def get_available_quests(self, discord_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                rank_row = conn.execute("SELECT rank FROM guild_members WHERE discord_id = ?", (discord_id,)).fetchone()
                if not rank_row: return []
                
                player_rank = rank_row["rank"]

                taken = conn.execute("SELECT quest_id FROM player_quests WHERE discord_id = ?", (discord_id,)).fetchall()
                taken_ids = {row["quest_id"] for row in taken}

                quests = conn.execute(
                    "SELECT id, title, tier, summary FROM quests WHERE tier = ?", (player_rank,)
                ).fetchall()

                return [dict(q) for q in quests if q["id"] not in taken_ids]
        except Exception as e:
            logger.error(f"Error fetching quests for {discord_id}: {e}", exc_info=True)
            return []

    def get_quest_details(self, quest_id: int) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT * FROM quests WHERE id = ?", (quest_id,)).fetchone()
                if not row: return None
                
                details = dict(row)
                try:
                    details["objectives"] = json.loads(details["objectives"])
                    details["rewards"] = json.loads(details["rewards"])
                except json.JSONDecodeError:
                    details["objectives"] = {}
                    details["rewards"] = {}
                return details
        except Exception as e:
            logger.error(f"Details fetch error: {e}")
            return None

    def get_player_quests(self, discord_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT q.id, q.title, q.summary, pq.status, pq.progress, q.objectives
                    FROM player_quests pq
                    JOIN quests q ON pq.quest_id = q.id
                    WHERE pq.discord_id = ? AND pq.status = 'in_progress'
                    """,
                    (discord_id,)
                ).fetchall()

                results = []
                for row in rows:
                    d = dict(row)
                    try:
                        d["progress"] = json.loads(d["progress"])
                        d["objectives"] = json.loads(d["objectives"])
                    except json.JSONDecodeError:
                        d["progress"] = {}
                        d["objectives"] = {}
                    results.append(d)
                return results
        except Exception as e:
            logger.error(f"Player quests error: {e}")
            return []

    def accept_quest(self, discord_id: int, quest_id: int) -> bool:
        try:
            with self.db.get_connection() as conn:
                exists = conn.execute(
                    "SELECT 1 FROM player_quests WHERE discord_id = ? AND quest_id = ?", (discord_id, quest_id)
                ).fetchone()
                if exists: return False

                q_data = conn.execute("SELECT objectives FROM quests WHERE id = ?", (quest_id,)).fetchone()
                if not q_data: return False

                try:
                    objectives = json.loads(q_data["objectives"])
                except json.JSONDecodeError:
                    return False

                progress = {}
                for type_, targets in objectives.items():
                    if isinstance(targets, dict):
                        progress[type_] = {t: 0 for t in targets}
                    else:
                        progress[type_] = {targets: 0}

                conn.execute(
                    "INSERT INTO player_quests (discord_id, quest_id, status, progress) VALUES (?, ?, ?, ?)",
                    (discord_id, quest_id, "in_progress", json.dumps(progress))
                )
                logger.info(f"User {discord_id} accepted quest {quest_id}")
                return True
        except Exception as e:
            logger.error(f"Accept quest error: {e}", exc_info=True)
            return False

    def update_progress(self, discord_id: int, quest_id: int, obj_type: str, target: str, amount: int = 1) -> bool:
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    "SELECT progress FROM player_quests WHERE discord_id = ? AND quest_id = ?",
                    (discord_id, quest_id)
                ).fetchone()
                
                if not row: return False

                try:
                    progress = json.loads(row["progress"])
                except json.JSONDecodeError:
                    return False

                if obj_type in progress and target in progress[obj_type]:
                    progress[obj_type][target] += amount
                    conn.execute(
                        "UPDATE player_quests SET progress = ? WHERE discord_id = ? AND quest_id = ?",
                        (json.dumps(progress), discord_id, quest_id)
                    )
                    return True
            return False
        except Exception as e:
            logger.error(f"Update progress error: {e}")
            return False

    def complete_quest(self, discord_id: int, quest_id: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT pq.progress, q.objectives 
                    FROM player_quests pq
                    JOIN quests q ON pq.quest_id = q.id
                    WHERE pq.discord_id = ? AND pq.quest_id = ? AND pq.status = 'in_progress'
                    """,
                    (discord_id, quest_id)
                ).fetchone()

                if not row:
                    return False, f"{ERROR} Quest inactive or already completed."

                progress = json.loads(row["progress"])
                objectives = json.loads(row["objectives"])

                if not self.check_completion(progress, objectives):
                    return False, f"{WARNING} Objectives not met."

                conn.execute(
                    "UPDATE player_quests SET status = 'completed' WHERE discord_id = ? AND quest_id = ?",
                    (discord_id, quest_id)
                )
                
            # Grant rewards
            reward_msg = self.reward_system.grant_rewards(discord_id, quest_id)
            return True, reward_msg

        except Exception as e:
            logger.error(f"Quest completion error: {e}", exc_info=True)
            return False, f"{ERROR} System error during completion."

    def check_completion(self, progress: Dict, objectives: Dict) -> bool:
        for obj_type, tasks in objectives.items():
            if isinstance(tasks, dict):
                for target, req in tasks.items():
                    if progress.get(obj_type, {}).get(target, 0) < req:
                        return False
            else:
                if progress.get(obj_type, {}).get(tasks, 0) < 1:
                    return False
        return True