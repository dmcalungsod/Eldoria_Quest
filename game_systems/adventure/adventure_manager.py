"""
game_systems/adventure/adventure_manager.py

Coordinates adventure lifecycles.
Hardened: Safe state transitions and secure reward handling.
"""

import datetime
import json
import logging

from database.database_manager import DatabaseManager
from game_systems.data.emojis import COMBAT
from game_systems.data.materials import MATERIALS
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

from .adventure_session import AdventureSession

logger = logging.getLogger("eldoria.adventure_mgr")


class AdventureManager:
    def __init__(self, db_manager: DatabaseManager, bot):
        self.db = db_manager
        self.bot = bot
        self.inventory_manager = InventoryManager(self.db)
        self.quest_system = QuestSystem(self.db)

    def start_adventure(self, discord_id: int, location_id: str, duration_minutes: int) -> bool:
        start_time = datetime.datetime.now()
        end_time = (
            start_time + datetime.timedelta(days=90)
            if duration_minutes == -1
            else start_time + datetime.timedelta(minutes=duration_minutes)
        )

        try:
            # Perform buff cleanup before starting new session
            self.db.clear_expired_buffs(discord_id)

            # Cleanup old sessions and create new one
            self.db.delete_adventure_session(discord_id, active=0)
            self.db.insert_adventure_session(
                discord_id,
                location_id,
                start_time.isoformat(),
                end_time.isoformat(),
                duration_minutes,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start adventure for {discord_id}: {e}")
            return False

    def get_active_session(self, discord_id: int):
        try:
            return self.db.get_active_adventure(discord_id)
        except Exception as e:
            logger.error(f"Error fetching session for {discord_id}: {e}")
            return None

    def simulate_adventure_step(self, discord_id: int) -> dict:
        session_row = self.get_active_session(discord_id)
        if not session_row:
            return {"sequence": [["Error: No active session found."]], "dead": True}

        session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, session_row)

        result = session.simulate_step()

        if result.get("dead", False):
            self._handle_death_rewards(discord_id, session)

        return result

    def _handle_death_rewards(self, discord_id, session):
        """Extracts partial rewards on death."""
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)

            items = self._grant_rewards_internal(session, 0, p_stats)

            bulk_items = [
                {
                    "item_key": item["key"],
                    "item_name": item["name"],
                    "item_type": item["type"],
                    "rarity": item["rarity"],
                    "amount": item["amount"],
                }
                for item in items
            ]
            self.inventory_manager.add_items_bulk(discord_id, bulk_items)

            self.db.end_adventure_session(discord_id)

        except Exception as e:
            logger.error(f"Error handling death for {discord_id}: {e}")

    def end_adventure(self, discord_id: int) -> dict | None:
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)
            items_to_add = []
            summary = None

            row = self.db.get_active_adventure(discord_id)
            if not row:
                return None

            session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, row)
            total_exp = session.loot.pop("exp", 0)
            total_aurum = session.loot.pop("aurum", 0)

            # Apply Aurum
            if total_aurum > 0:
                self.db.increment_player_fields(discord_id, aurum=total_aurum)

            # Capture state before rewards
            old_level = self.db.get_player_field(discord_id, "level")

            items_to_add = self._grant_rewards_internal(session, total_exp, p_stats)

            # Capture state after rewards
            new_level = self.db.get_player_field(discord_id, "level")

            self.db.end_adventure_session(discord_id)

            summary = {
                "loot": items_to_add,
                "xp_gained": total_exp,
                "aurum_gained": total_aurum,
                "old_level": old_level,
                "new_level": new_level,
                "leveled_up": new_level > old_level,
            }

            bulk_items = [
                {
                    "item_key": item["key"],
                    "item_name": item["name"],
                    "item_type": item["type"],
                    "rarity": item["rarity"],
                    "amount": item["amount"],
                }
                for item in items_to_add
            ]
            self.inventory_manager.add_items_bulk(discord_id, bulk_items)

            return summary

        except Exception as e:
            logger.error(f"Error ending adventure for {discord_id}: {e}", exc_info=True)
            return None

    def _grant_rewards_internal(self, session, total_exp, player_stats):
        """Helper to calculate and apply rewards."""
        p_row = self.db.get_player(session.discord_id)

        level_sys = LevelUpSystem(
            stats=player_stats, level=p_row["level"], exp=p_row["experience"], exp_to_next=p_row["exp_to_next"]
        )

        if total_exp > 0:
            level_sys.add_exp(total_exp)

        # Save Vitals & Level
        current_hp = p_row["current_hp"]
        saved_hp = 1 if current_hp <= 0 else current_hp

        self.db.update_player_fields(
            session.discord_id,
            level=level_sys.level,
            experience=level_sys.exp,
            exp_to_next=level_sys.exp_to_next,
            current_hp=saved_hp,
            current_mp=level_sys.stats.max_mp,
        )
        self.db.increment_player_fields(session.discord_id, vestige_pool=total_exp)

        items_awarded = []
        for item_key, count in session.loot.items():
            mat = MATERIALS.get(item_key)
            name = mat["name"] if mat else item_key
            rarity = mat.get("rarity", "Common") if mat else "Common"
            items_awarded.append({"key": item_key, "name": name, "type": "material", "rarity": rarity, "amount": count})

        return items_awarded

    def start_promotion_trial(self, discord_id: int, next_rank: str):
        try:
            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)

            boss_hp = int(p_stats.max_hp * 2.5)
            active_monster = {
                "name": f"Rank {next_rank} Examiner",
                "tier": "Boss",
                "HP": boss_hp,
                "max_hp": boss_hp,
                "MP": 100,
                "ATK": int(p_stats.endurance * 1.5 + 20),
                "DEF": int(p_stats.strength * 0.8),
                "xp": 500,
                "drops": [],
                "promotion_target": next_rank,
            }

            start = datetime.datetime.now()
            end = start + datetime.timedelta(hours=1)

            # Perform buff cleanup
            self.db.clear_expired_buffs(discord_id)

            # Cleanup old sessions
            self.db.delete_adventure_session(discord_id, active=0)

            # Create promotion trial session
            self.db._col("adventure_sessions").delete_many({"discord_id": discord_id})
            self.db._col("adventure_sessions").insert_one(
                {
                    "discord_id": discord_id,
                    "location_id": "guild_arena",
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                    "duration_minutes": -1,
                    "active": 1,
                    "logs": json.dumps([f"{COMBAT} **PROMOTION TRIAL**\nThe Examiner awaits."]),
                    "loot_collected": "{}",
                    "active_monster_json": json.dumps(active_monster),
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start trial for {discord_id}: {e}")
            return False
