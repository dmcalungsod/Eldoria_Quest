"""
game_systems/guild_system/tournament_system.py

Manages the weekly Guild Tournaments.
Handles starting events, tracking scores, and distributing rewards.
"""

import datetime
import logging
import random

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.core.world_time import WorldTime

logger = logging.getLogger("eldoria.tournament")


class TournamentSystem:
    # Available tournament types
    TOURNAMENT_TYPES = [
        "monster_kills",
        "quests_completed",
        "boss_kills",
        "spectral_tide",
        "elemental_harvest",
    ]

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def start_weekly_tournament(self) -> int:
        """
        Starts a new weekly tournament if one isn't already active.
        Returns the tournament ID.
        """
        # Check if one is already running
        active = self.db.get_active_tournament()
        if active:
            # Check if it should have ended
            end_time = datetime.datetime.fromisoformat(active["end_time"])
            if WorldTime.now() > end_time:
                self.end_current_tournament()
            else:
                return active["id"]

        # Pick a random event type
        event_type = random.choice(self.TOURNAMENT_TYPES)

        # Schedule for 7 days
        start_time = WorldTime.now()
        end_time = start_time + datetime.timedelta(days=7)

        # Create in DB
        t_id = self.db.create_tournament(
            tournament_type=event_type,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

        logger.info(f"Started Tournament #{t_id}: {event_type}")
        return t_id

    def end_current_tournament(self) -> str:
        """
        Ends the current tournament, calculates winners, and distributes rewards.
        Returns a summary string of the results.
        """
        active = self.db.get_active_tournament()
        if not active:
            return "No active tournament to end."

        t_id = active["id"]
        event_type = active["type"]

        # Fetch Top 3
        winners = self.db.get_tournament_leaderboard(t_id, limit=3)

        results_msg = [f"{E.VICTORY} **Tournament Ended: {event_type.replace('_', ' ').title()}**\n"]

        if not winners:
            results_msg.append("No participants qualified for rewards.")
        else:
            for rank, winner in enumerate(winners, 1):
                discord_id = winner["discord_id"]
                score = winner["score"]
                name = winner.get("name", "Unknown Hero")

                # Calculate Reward
                # 1st: 1000 Aurum + Title
                # 2nd: 500 Aurum
                # 3rd: 250 Aurum
                if rank == 1:
                    reward = 1000
                    title = "Grand Champion"
                    self.db.add_title(discord_id, title)
                    self.db.increment_player_fields(discord_id, aurum=reward)
                    results_msg.append(f"🥇 **{name}**: {score} pts — {reward} Aurum & Title: *{title}*")
                elif rank == 2:
                    reward = 500
                    self.db.increment_player_fields(discord_id, aurum=reward)
                    results_msg.append(f"🥈 **{name}**: {score} pts — {reward} Aurum")
                elif rank == 3:
                    reward = 250
                    self.db.increment_player_fields(discord_id, aurum=reward)
                    results_msg.append(f"🥉 **{name}**: {score} pts — {reward} Aurum")

        # Mark as inactive
        self.db.end_active_tournament()
        logger.info(f"Ended Tournament #{t_id}")

        return "\n".join(results_msg)

    def record_action(self, discord_id: int, action_type: str, value: int = 1):
        """
        Records a player action (kill, quest completion) if it matches the active tournament.
        """
        active = self.db.get_active_tournament()
        if not active:
            return

        # Check type match
        if active["type"] != action_type:
            return

        # Check if expired
        end_time = datetime.datetime.fromisoformat(active["end_time"])
        if WorldTime.now() > end_time:
            return

        # Update Score
        self.db.update_tournament_score(discord_id, active["id"], value)

    def get_leaderboard(self) -> tuple[dict | None, list]:
        """
        Returns (active_tournament_info, leaderboard_list).
        Leaderboard list contains dicts with {name, score, rank}.
        """
        active = self.db.get_active_tournament()
        if not active:
            return None, []

        raw_leaders = self.db.get_tournament_leaderboard(active["id"], limit=10)

        # Add rank explicitly
        leaders = []
        for i, entry in enumerate(raw_leaders, 1):
            entry["rank"] = i
            leaders.append(entry)

        return active, leaders
