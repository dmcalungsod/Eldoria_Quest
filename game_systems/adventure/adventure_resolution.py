"""
game_systems/adventure/adventure_resolution.py

Engine for resolving time-based background adventures.
"""

import json
import logging
import math
from typing import Any

from database.database_manager import DatabaseManager
from game_systems.adventure.adventure_manager import AdventureManager
from game_systems.adventure.adventure_session import AdventureSession
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager

logger = logging.getLogger("eldoria.resolution")


class AdventureResolutionEngine:
    def __init__(self, bot, db_manager: DatabaseManager):
        self.bot = bot
        self.db = db_manager
        self.quest_system = QuestSystem(self.db)
        self.inventory_manager = InventoryManager(self.db)
        self.adventure_manager = AdventureManager(self.db, self.bot)

    def resolve_session(self, session_doc: dict[str, Any]) -> bool:
        """
        Processes a time-based adventure session to completion (or death).
        Returns True if session was marked completed/processed.
        """
        discord_id = session_doc["discord_id"]
        logger.info(f"Starting resolution for session {discord_id}")

        # 1. Initialize Session Wrapper
        session = AdventureSession(
            self.db,
            self.quest_system,
            self.inventory_manager,
            discord_id,
            row_data=session_doc,
        )

        # 2. Calculate Steps
        duration_mins = session_doc.get("duration_minutes", 60)

        # If unlimited duration (-1), we process steps up to NOW based on start_time?
        # The scheduler queries 'get_adventures_ending_before'.
        # Unlimited adventures don't have an end time, so they shouldn't be picked up by that query
        # unless we explicitly want to 'tick' them.
        # For now, we assume fixed duration adventures are the target.
        if duration_mins <= 0:
            logger.warning(f"Skipping infinite adventure resolution for {discord_id}")
            return False

        # 15 mins per step
        total_steps = math.ceil(duration_mins / 15)
        # Ensure at least 1 step if duration > 0
        total_steps = max(1, total_steps)

        steps_completed = session.steps_completed
        steps_remaining = total_steps - steps_completed

        if steps_remaining <= 0:
            logger.info(f"Session {discord_id} already fully processed.")
            self._mark_complete(discord_id)
            return True

        logger.info(f"Simulating {steps_remaining} steps for {discord_id} (Total: {total_steps})")

        # 3. Simulation Loop
        for _ in range(steps_remaining):
            result = session.simulate_step(background=True)

            # Increment step counter
            session.steps_completed += 1

            # Save intermediate state (logs, loot, vitals, step count)
            session.save_state()

            if result.get("dead", False):
                logger.info(f"Player {discord_id} died during simulation step {session.steps_completed}.")
                self._handle_death(discord_id, session)
                return True

        # 4. Finalize Success
        self._mark_complete(discord_id)
        return True

    def _mark_complete(self, discord_id: int):
        """Marks successful adventure as ready to claim."""
        self.db.update_adventure_status(discord_id, "completed")

    def _handle_death(self, discord_id: int, session: AdventureSession):
        """Resolves death: penalties, inventory update, and marks session failed."""
        # Penalize but KEEP ACTIVE so player can see the report
        loss_msg = self.adventure_manager._handle_death_rewards(discord_id, session, deactivate=False)

        # Append loss message to logs if available
        if loss_msg:
            session.logs.append(loss_msg)

        # Update logs, save loot changes, and MARK FAILED (but keep active=1)
        trimmed_logs = session.logs[-30:]

        # We manually update session fields because save_state() might not be flexible enough
        # to handle the status change we want implicitly, and we want to ensure "failed" status.
        self.db.set_adventure_failed(
            discord_id=discord_id,
            logs=json.dumps(trimmed_logs),
            loot_collected=json.dumps(session.loot),
            steps_completed=session.steps_completed,
            previous_version=session.version
        )
