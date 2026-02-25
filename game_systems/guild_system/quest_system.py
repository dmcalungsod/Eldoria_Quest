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
from game_systems.guild_system.tournament_system import TournamentSystem

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

            # Allow quests from current rank and all lower ranks to prevent progression lock
            rank_order = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"]
            if rank in rank_order:
                allowed_tiers = rank_order[: rank_order.index(rank) + 1]
            else:
                allowed_tiers = [rank]

            quests = list(
                self.db._col("quests").find(
                    {"tier": {"$in": allowed_tiers}},
                    {
                        "_id": 0,
                        "id": 1,
                        "title": 1,
                        "tier": 1,
                        "summary": 1,
                        "prerequisites": 1,
                        "exclusive_group": 1,
                    },
                )
            )

            # Fetch all player quest IDs (active + completed) to determine locked groups
            all_pq_docs = self.db._col("player_quests").find(
                {"discord_id": discord_id},
                {"_id": 0, "quest_id": 1, "status": 1},
            )

            all_player_quests = list(all_pq_docs)
            completed_ids = {d["quest_id"] for d in all_player_quests if d.get("status") == "completed"}
            all_ids = [d["quest_id"] for d in all_player_quests]

            # Find groups the player is already locked into
            locked_groups = set()
            if all_ids:
                group_docs = self.db._col("quests").find(
                    {"id": {"$in": all_ids}, "exclusive_group": {"$ne": None}},
                    {"exclusive_group": 1},
                )
                locked_groups = {d["exclusive_group"] for d in group_docs if d.get("exclusive_group")}

            available = []
            for q in quests:
                if q["id"] in taken_ids:
                    continue

                # Check exclusive group
                grp = q.get("exclusive_group")
                if grp and grp in locked_groups:
                    continue

                # Check prerequisites
                prereqs = q.get("prerequisites")
                if prereqs:
                    # Support single ID or list
                    if isinstance(prereqs, int):
                        prereqs = [prereqs]

                    if not all(pid in completed_ids for pid in prereqs):
                        continue

                available.append(q)

            return available
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
                details["objectives"] = (
                    json.loads(details["objectives"])
                    if isinstance(details["objectives"], str)
                    else details["objectives"]
                )
                details["rewards"] = (
                    json.loads(details["rewards"]) if isinstance(details["rewards"], str) else details["rewards"]
                )
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
                    {
                        "_id": 0,
                        "id": 1,
                        "title": 1,
                        "summary": 1,
                        "location": 1,
                        "objectives": 1,
                        "flavor_text": 1,
                    },
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
                    "flavor_text": quest.get("flavor_text", {}),
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

            quest = self.db._col("quests").find_one(
                {"id": quest_id}, {"_id": 0, "objectives": 1, "tier": 1, "exclusive_group": 1}
            )
            if not quest:
                return False

            # --- EXCLUSIVE GROUP CHECK ---
            exclusive_group = quest.get("exclusive_group")
            if exclusive_group:
                # Find all quest IDs in this group
                group_docs = self.db._col("quests").find({"exclusive_group": exclusive_group}, {"id": 1})
                group_ids = [d["id"] for d in group_docs]

                # Check if player has accepted or completed any
                existing_group_quest = self.db._col("player_quests").find_one(
                    {"discord_id": discord_id, "quest_id": {"$in": group_ids}}, {"_id": 1}
                )
                if existing_group_quest:
                    logger.warning(
                        f"Rejecting Quest {quest_id} for User {discord_id}: Exclusive group conflict ({exclusive_group})"
                    )
                    return False
            # -----------------------------

            # --- SECURITY CHECK ---
            player_rank = self.db.get_guild_member_field(discord_id, "rank")
            rank_order = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"]

            allowed = False
            if player_rank in rank_order:
                allowed_tiers = rank_order[: rank_order.index(player_rank) + 1]
                if quest.get("tier") in allowed_tiers:
                    allowed = True
            elif quest.get("tier") == player_rank:
                allowed = True

            if not allowed:
                logger.warning(
                    f"Security: User {discord_id} (Rank {player_rank}) tried to accept Quest {quest_id} (Rank {quest.get('tier')})"
                )
                return False
            # ----------------------

            try:
                objectives = (
                    json.loads(quest["objectives"]) if isinstance(quest["objectives"], str) else quest["objectives"]
                )
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

    def update_progress(
        self,
        discord_id: int,
        quest_id: int,
        obj_type: str,
        target: str,
        amount: int = 1,
    ) -> bool:
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
                {
                    "discord_id": discord_id,
                    "quest_id": quest_id,
                    "status": "in_progress",
                },
                {"_id": 0, "progress": 1},
            )
            if not pq:
                return False, f"{ERROR} Quest inactive or already completed."

            quest = self.db._col("quests").find_one({"id": quest_id}, {"_id": 0, "objectives": 1, "rewards": 1})
            if not quest:
                return False, f"{ERROR} Quest definition not found."

            # --- PRE-VALIDATION: Ensure Rewards are Valid ---
            try:
                if isinstance(quest.get("rewards"), str):
                    json.loads(quest["rewards"])
            except json.JSONDecodeError:
                logger.error(f"Critical: Corrupt reward JSON for quest {quest_id}")
                return (
                    False,
                    f"{ERROR} System error: Reward data corrupted. Please report this.",
                )
            # ------------------------------------------------

            progress = json.loads(pq["progress"]) if isinstance(pq["progress"], str) else pq["progress"]
            objectives = (
                json.loads(quest["objectives"]) if isinstance(quest["objectives"], str) else quest["objectives"]
            )

            if not self.check_completion(progress, objectives):
                return False, f"{WARNING} Objectives not met."

            result = self.db._col("player_quests").update_one(
                {
                    "discord_id": discord_id,
                    "quest_id": quest_id,
                    "status": "in_progress",
                },
                {"$set": {"status": "completed"}},
            )

            if result.modified_count == 0:
                # Race Condition Detected: Status changed between find_one and update_one
                logger.warning(f"Quest completion race condition prevented for {discord_id}, quest {quest_id}")
                return False, f"{ERROR} Quest already completed or inactive."

            # Grant rewards
            reward_msg = self.reward_system.grant_rewards(discord_id, quest_id)

            # --- TOURNAMENT HOOK ---
            try:
                tournament = TournamentSystem(self.db)
                tournament.record_action(discord_id, "quests_completed", 1)
            except Exception as e:
                logger.error(f"Tournament hook error: {e}")
            # -----------------------

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
