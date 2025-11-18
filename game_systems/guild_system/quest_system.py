"""
quest_system.py

Handles all logic related to quests issued by the Adventurer's Guild.

This system manages:
- Retrieving quests appropriate for a player's Guild Rank
- Accepting official Guild-issued assignments
- Tracking objective progress during expeditions
- Completing quests and triggering reward distribution
"""

import json
from typing import Dict, List, Optional, Tuple

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.guild_system.reward_system import RewardSystem


class QuestSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.reward_system = RewardSystem(db_manager)

    # -----------------------------------------------------------
    #  Fetching Quests
    # -----------------------------------------------------------

    def get_available_quests(self, discord_id: int) -> List[Dict]:
        """
        Fetches quests suited to the Adventurer's Guild Rank.
        Returns a list of quest dictionaries.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Retrieve the adventurer's Guild Rank
        cur.execute(
            "SELECT rank FROM guild_members WHERE discord_id = ?", (discord_id,)
        )
        player_rank_data = cur.fetchone()

        if not player_rank_data:
            conn.close()
            return []

        player_rank = player_rank_data["rank"]

        # Get all quests already taken or completed to avoid duplication
        cur.execute(
            "SELECT quest_id FROM player_quests WHERE discord_id = ?", (discord_id,)
        )
        taken_quest_ids = {row["quest_id"] for row in cur.fetchall()}

        # Fetch quests locked to the adventurer's current Guild Rank
        cur.execute(
            "SELECT id, title, tier, summary FROM quests WHERE tier = ?", (player_rank,)
        )
        all_quests = cur.fetchall()
        conn.close()

        # Filter out previously taken quests
        available_quests = [
            dict(q) for q in all_quests if q["id"] not in taken_quest_ids
        ]
        return available_quests

    # -----------------------------------------------------------
    #  Detailed Quest Data
    # -----------------------------------------------------------

    def get_quest_details(self, quest_id: int) -> Optional[Dict]:
        """
        Retrieves full quest details from the Guild Registry:
        - Lore summary
        - Objective list
        - Reward package (EXP, Gold, Guild Merit, items)
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
        quest_data = cur.fetchone()
        conn.close()

        if quest_data:
            details = dict(quest_data)
            # Parse JSON fields
            try:
                details["objectives"] = json.loads(details["objectives"])
                details["rewards"] = json.loads(details["rewards"])
            except json.JSONDecodeError:
                # Fallback for empty or malformed JSON
                details["objectives"] = {}
                details["rewards"] = {}
            return details

        return None

    # -----------------------------------------------------------
    #  Accepting a Quest
    # -----------------------------------------------------------

    def accept_quest(self, discord_id: int, quest_id: int) -> bool:
        """
        Registers the adventurer for an official quest.
        - Prevents registering for the same quest twice
        - Initializes objective progress based on the quest data
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Check if the quest is already in progress or finished
        cur.execute(
            "SELECT id FROM player_quests WHERE discord_id = ? AND quest_id = ?",
            (discord_id, quest_id),
        )
        if cur.fetchone():
            conn.close()
            return False

        quest_details = self.get_quest_details(quest_id)
        if not quest_details:
            conn.close()
            return False

        # Initialize objective tracker structure (start at 0)
        initial_progress = {}
        for obj_type, tasks in quest_details["objectives"].items():
            if isinstance(tasks, dict):
                initial_progress[obj_type] = {task: 0 for task in tasks}
            else:
                # For string objectives like "Locate Lina", treat as count 0
                initial_progress[obj_type] = {tasks: 0}

        cur.execute(
            "INSERT INTO player_quests (discord_id, quest_id, status, progress) VALUES (?, ?, ?, ?)",
            (discord_id, quest_id, "in_progress", json.dumps(initial_progress)),
        )

        conn.commit()
        conn.close()
        return True

    # -----------------------------------------------------------
    #  Retrieving Active Quests
    # -----------------------------------------------------------

    def get_player_quests(self, discord_id: int) -> List[Dict]:
        """
        Retrieves every active assignment the adventurer is currently undertaking.
        Equivalent to the Guild “Adventurer Task Ledger”.
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT q.id, q.title, q.summary, pq.status, pq.progress, q.objectives
            FROM player_quests pq
            JOIN quests q ON pq.quest_id = q.id
            WHERE pq.discord_id = ? AND pq.status = 'in_progress'
        """,
            (discord_id,),
        )

        player_quests = [dict(row) for row in cur.fetchall()]
        conn.close()

        for quest in player_quests:
            # Safe parsing of progress and objectives
            try:
                quest["progress"] = json.loads(quest["progress"])
                quest["objectives"] = json.loads(quest["objectives"])
            except json.JSONDecodeError:
                quest["progress"] = {}
                quest["objectives"] = {}

        return player_quests

    # -----------------------------------------------------------
    #  Updating Quest Progress
    # -----------------------------------------------------------

    def update_progress(
        self,
        discord_id: int,
        quest_id: int,
        obj_type: str,
        target: str,
        amount: int = 1,
    ) -> bool:
        """
        Updates the adventurer’s progress during an expedition.

        Parameters:
        - obj_type: The category (e.g., "defeat", "collect")
        - target: The specific item/monster name (e.g., "Forest Slime")
        - amount: How much to increment progress by
        """
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT progress FROM player_quests WHERE discord_id = ? AND quest_id = ?",
            (discord_id, quest_id),
        )
        row = cur.fetchone()

        if not row:
            conn.close()
            return False

        try:
            progress = json.loads(row["progress"])
        except json.JSONDecodeError:
            conn.close()
            return False

        # Check if this objective exists in the player's tracking data
        if obj_type in progress and target in progress[obj_type]:
            progress[obj_type][target] += amount

            cur.execute(
                "UPDATE player_quests SET progress = ? WHERE discord_id = ? AND quest_id = ?",
                (json.dumps(progress), discord_id, quest_id),
            )
            conn.commit()
            conn.close()
            return True

        conn.close()
        return False

    # -----------------------------------------------------------
    #  Objective Completion Check
    # -----------------------------------------------------------

    def check_completion(self, progress: Dict, objectives: Dict) -> bool:
        """
        Compares actual progress vs. required objectives.
        Returns True only if ALL tasks meet or exceed the quota.
        """
        for obj_type, tasks in objectives.items():
            if isinstance(tasks, dict):
                for target, required_amt in tasks.items():
                    current_amt = progress.get(obj_type, {}).get(target, 0)
                    if current_amt < required_amt:
                        return False
            else:
                # Handle single string objectives (treated as boolean/count of 1)
                target = tasks
                current_amt = progress.get(obj_type, {}).get(target, 0)
                if current_amt < 1:
                    return False

        return True

    # -----------------------------------------------------------
    #  Completing a Quest
    # -----------------------------------------------------------

    def complete_quest(self, discord_id: int, quest_id: int) -> Tuple[bool, str]:
        """
        Governs official quest completion:
        1. Validates if the quest is active
        2. Validates if objectives are met
        3. Calls RewardSystem to distribute loot/XP
        4. Marks quest as 'completed' in DB
        """
        conn = self.db.connect()
        cur = conn.cursor()

        # Fetch progress and requirements
        cur.execute(
            """
            SELECT pq.progress, q.objectives
            FROM player_quests pq
            JOIN quests q ON pq.quest_id = q.id
            WHERE pq.discord_id = ? AND pq.quest_id = ? AND pq.status = 'in_progress'
        """,
            (discord_id, quest_id),
        )

        row = cur.fetchone()
        conn.close()

        if not row:
            return (
                False,
                f"{E.ERROR} This quest is not active or has already been resolved.",
            )

        progress = json.loads(row["progress"])
        objectives = json.loads(row["objectives"])

        # Validation
        if not self.check_completion(progress, objectives):
            return False, f"{E.WARNING} The required objectives have not yet been met."

        # Distribute Rewards via RewardSystem
        reward_msg = self.reward_system.grant_rewards(discord_id, quest_id)

        # Mark as Completed
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE player_quests SET status = 'completed' WHERE discord_id = ? AND quest_id = ?",
            (discord_id, quest_id),
        )
        conn.commit()
        conn.close()

        # --- THIS IS THE FIX ---
        # Return only the reward message, not extra text
        return True, reward_msg
        # --- END OF FIX ---
