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

        # OPTIMIZATION: Fetch context ONCE and persist only at the end
        bundle = self.db.get_combat_context_bundle(discord_id)
        initial_hp = 0
        initial_mp = 0
        max_hp = 100  # Fallback
        max_mp = 100  # Fallback

        if bundle and "player" in bundle:
            initial_hp = bundle["player"].get("current_hp", 0)
            initial_mp = bundle["player"].get("current_mp", 0)

            # Extract Max HP/MP from stats if available for delta calculation
            # Note: AdventureSession extracts this internally, but we need it for final delta
            # We can rely on the last result's context if available, or fetch now.
            # Let's try to extract it from bundle["stats"]
            if bundle.get("stats"):
                # Use simple extraction, exact logic matches PlayerStats defaults
                max_hp = bundle["stats"].get("HP", 100)
                max_mp = bundle["stats"].get("MP", 100)

        final_vitals = None

        # 3. Simulation Loop
        for _ in range(steps_remaining):
            # Pass bundle and persist=False to avoid DB writes per step
            result = session.simulate_step(context_bundle=bundle, background=True, persist=False)

            # Increment step counter
            session.steps_completed += 1
            final_vitals = result.get("vitals")

            # FIX: Update bundle with new vitals so damage persists to next step
            if final_vitals and bundle and "player" in bundle:
                bundle["player"]["current_hp"] = final_vitals.get("current_hp", bundle["player"]["current_hp"])
                bundle["player"]["current_mp"] = final_vitals.get("current_mp", bundle["player"]["current_mp"])

            if result.get("dead", False):
                logger.info(f"Player {discord_id} died during simulation step {session.steps_completed}.")

                # Save state immediately on death
                session.save_state()

                # Apply Vital Updates (Dead)
                if final_vitals:
                    current_hp = final_vitals.get("current_hp", 0)
                    current_mp = final_vitals.get("current_mp", 0)

                    # Update Max HP from player_stats if available
                    if result.get("player_stats"):
                        p_stats = result["player_stats"]
                        max_hp = p_stats.max_hp
                        max_mp = p_stats.max_mp

                    delta_hp = current_hp - initial_hp
                    delta_mp = current_mp - initial_mp
                    if delta_hp != 0 or delta_mp != 0:
                        self.db.update_player_vitals_delta(discord_id, delta_hp, delta_mp, max_hp, max_mp)

                self._handle_death(discord_id, session)
                return True

        # 4. Finalize Success
        # Save state ONCE at the end
        session.save_state()

        # Apply Vital Updates (Final)
        if final_vitals:
            current_hp = final_vitals.get("current_hp", initial_hp)
            current_mp = final_vitals.get("current_mp", initial_mp)

            # Check for PlayerStats in result to get accurate Max HP/MP (handling buffs)
            if result.get("player_stats"):
                p_stats = result["player_stats"]
                max_hp = p_stats.max_hp
                max_mp = p_stats.max_mp

            delta_hp = current_hp - initial_hp
            delta_mp = current_mp - initial_mp
            if delta_hp != 0 or delta_mp != 0:
                self.db.update_player_vitals_delta(discord_id, delta_hp, delta_mp, max_hp, max_mp)

        self._mark_complete(discord_id)
        return True

    def _mark_complete(self, discord_id: int):
        """Marks successful adventure as ready to claim."""
        self.db.update_adventure_status(discord_id, "completed")

    def _handle_death(self, discord_id: int, session: AdventureSession):
        """Resolves death: penalties, inventory update, and marks session failed."""
        loss_msg = self.adventure_manager._handle_death_rewards(discord_id, session)

        # Append loss message to logs if available
        if loss_msg:
            # We need to manually append to logs in DB since _handle_death_rewards ended the session
            # but didn't save the log update (it modified session.loot only usually).
            # Actually _handle_death_rewards calls db.end_adventure_session.
            # We should probably update the log with the loss report.

            # Fetch closed session to append log?
            # Or assume _handle_death_rewards does enough.
            # _handle_death_rewards in AdventureManager returns a string but doesn't save it to session logs explicitly?
            # It seems it expects the caller to display it.

            # Let's save it to the session logs.
            session.logs.append(loss_msg)
            # Use raw update because session is now inactive
            trimmed_logs = session.logs[-30:]
            self.db.update_adventure_session(
                discord_id,
                logs=json.dumps(trimmed_logs),
                loot_collected=json.dumps(session.loot),
                active=0,  # Ensure inactive
                active_monster_json=None,
                previous_version=session.version,  # Hope version matches
                steps_completed=session.steps_completed,
            )

        self.db.update_adventure_status(discord_id, "failed")
