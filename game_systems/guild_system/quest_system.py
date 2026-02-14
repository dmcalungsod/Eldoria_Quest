"""
game_systems/guild_system/quest_system.py

Manages quest tracking, updates, and completion.
Hardened: Safe state validation with MongoDB methods.
"""

import json
import logging

from database.database_manager import DatabaseManager
from game_systems.data.emojis import ERROR, WARNING
from game_systems.guild_system.reward_system import RewardSystem

logger = logging.getLogger("eldoria.quests")


class QuestSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.reward_system = RewardSystem(db_manager)

    def get_available_quests(self, discord_id: int) -> list[dict]:
        try:
            rank = self.db.get_guild_member_field(discord_id, "rank")
            if not rank:
                return []

            taken = self.db.get_player_quest_ids(discord_id)
            taken_ids = set(taken)

            quests = list(
                self.db._col("quests").find(
                    {"tier": rank},
                    {"_id": 0, "id": 1, "title": 1, "tier": 1, "summary": 1},
                )
            )

            return [q for q in quests if q["id"] not in taken_ids]
        except Exception as e:
            logger.error(f"Error fetching quests for {discord_id}: {e}", exc_info=True)
            return []

    def get_quest_details(self, quest_id: int) -> dict | None:
        try:
            row = self.db._col("quests").find_one({"id": quest_id}, {"_id": 0})
            if not row:
                return None

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

    def get_player_quests(self, discord_id: int) -> list[dict]:
        try:
            pq_rows = list(
                self.db._col("player_quests").find(
                    {"discord_id": discord_id, "status": "in_progress"},
                    {"_id": 0},
                )
            )

            results = []
            for pq in pq_rows:
                quest = self.db._col("quests").find_one(
                    {"id": pq["quest_id"]},
                    {"_id": 0, "id": 1, "title": 1, "summary": 1, "location": 1, "objectives": 1},
                )
                if not quest:
                    continue

                d = {
                    "id": quest["id"],
                    "title": quest["title"],
                    "summary": quest.get("summary"),
                    "location": quest.get("location"),
                    "status": pq["status"],
                    "progress": pq.get("progress", "{}"),
                    "objectives": quest.get("objectives", "{}"),
                }

                try:
                    d["progress"] = json.loads(d["progress"]) if isinstance(d["progress"], str) else d["progress"]
                    d["objectives"] = (
                        json.loads(d["objectives"]) if isinstance(d["objectives"], str) else d["objectives"]
                    )
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
            exists = self.db._col("player_quests").find_one(
                {"discord_id": discord_id, "quest_id": quest_id}, {"_id": 1}
            )
            if exists:
                return False

            quest = self.db._col("quests").find_one({"id": quest_id}, {"_id": 0, "objectives": 1})
            if not quest:
                return False

            try:
                objectives = json.loads(quest["objectives"])
            except json.JSONDecodeError:
                return False

            progress = {}
            for type_, targets in objectives.items():
                if isinstance(targets, dict):
                    progress[type_] = {t: 0 for t in targets}
                else:
                    progress[type_] = {targets: 0}

            self.db._col("player_quests").insert_one(
                {
                    "discord_id": discord_id,
                    "quest_id": quest_id,
                    "status": "in_progress",
                    "progress": json.dumps(progress),
                }
            )
            logger.info(f"User {discord_id} accepted quest {quest_id}")
            return True
        except Exception as e:
            logger.error(f"Accept quest error: {e}", exc_info=True)
            return False

    def update_progress(self, discord_id: int, quest_id: int, obj_type: str, target: str, amount: int = 1) -> bool:
        try:
            row = self.db._col("player_quests").find_one(
                {"discord_id": discord_id, "quest_id": quest_id},
                {"_id": 0, "progress": 1},
            )
            if not row:
                return False

            try:
                progress = json.loads(row["progress"]) if isinstance(row["progress"], str) else row["progress"]
            except json.JSONDecodeError:
                return False

            if obj_type in progress and target in progress[obj_type]:
                progress[obj_type][target] += amount
                self.db._col("player_quests").update_one(
                    {"discord_id": discord_id, "quest_id": quest_id},
                    {"$set": {"progress": json.dumps(progress)}},
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Update progress error: {e}")
            return False

    def complete_quest(self, discord_id: int, quest_id: int) -> tuple[bool, str]:
        try:
            pq = self.db._col("player_quests").find_one(
                {"discord_id": discord_id, "quest_id": quest_id, "status": "in_progress"},
                {"_id": 0, "progress": 1},
            )
            if not pq:
                return False, f"{ERROR} Quest inactive or already completed."

            quest = self.db._col("quests").find_one({"id": quest_id}, {"_id": 0, "objectives": 1})
            if not quest:
                return False, f"{ERROR} Quest definition not found."

            progress = json.loads(pq["progress"]) if isinstance(pq["progress"], str) else pq["progress"]
            objectives = (
                json.loads(quest["objectives"]) if isinstance(quest["objectives"], str) else quest["objectives"]
            )

            if not self.check_completion(progress, objectives):
                return False, f"{WARNING} Objectives not met."

            self.db._col("player_quests").update_one(
                {"discord_id": discord_id, "quest_id": quest_id},
                {"$set": {"status": "completed"}},
            )

            # Grant rewards
            reward_msg = self.reward_system.grant_rewards(discord_id, quest_id)
            return True, reward_msg

        except Exception as e:
            logger.error(f"Quest completion error: {e}", exc_info=True)
            return False, f"{ERROR} System error during completion."

    def check_completion(self, progress: dict, objectives: dict) -> bool:
        for obj_type, tasks in objectives.items():
            if isinstance(tasks, dict):
                for target, req in tasks.items():
                    if progress.get(obj_type, {}).get(target, 0) < req:
                        return False
            else:
                if progress.get(obj_type, {}).get(tasks, 0) < 1:
                    return False
        return True
