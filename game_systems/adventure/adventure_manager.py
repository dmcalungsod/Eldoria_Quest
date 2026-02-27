"""
game_systems/adventure/adventure_manager.py

Coordinates adventure lifecycles.
Hardened: Safe state transitions and secure reward handling.
"""

import datetime
import json
import logging
import random

from database.database_manager import DatabaseManager
from game_systems.core.world_time import WorldTime
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.emojis import AURUM, COMBAT, SKULL
from game_systems.data.materials import MATERIALS
from game_systems.guild_system.faction_system import FactionSystem
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.achievement_system import AchievementSystem
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
        self.faction_system = FactionSystem(self.db)

    def start_adventure(
        self,
        discord_id: int,
        location_id: str,
        duration_minutes: int,
        supplies: dict[str, int] | None = None,
    ) -> bool:
        # --- SECURITY FIX: Input Validation ---
        if location_id not in LOCATIONS:
            logger.warning(f"Invalid location_id attempted: {location_id} by {discord_id}")
            return False

        # Max duration: 1 year (approx 525,600 minutes) to prevent overflow
        if duration_minutes != -1 and not (0 < duration_minutes <= 525600):
            logger.warning(f"Invalid adventure duration: {duration_minutes} by {discord_id}")
            return False

        # Verify and Deduct Supplies
        if supplies:
            # 1. Verification Phase
            # Fetch inventory once to check counts AND capture item metadata for potential rollback
            inventory_items = self.inventory_manager.get_inventory(discord_id)
            item_totals = {}
            item_meta = {}

            for item in inventory_items:
                k = item["item_key"]
                item_totals[k] = item_totals.get(k, 0) + item["count"]
                # Store metadata (name, type, rarity) for the first occurrence of this item key
                if k not in item_meta:
                    item_meta[k] = {
                        "name": item["item_name"],
                        "type": item["item_type"],
                        "rarity": item["rarity"],
                    }

            for item_key, count in supplies.items():
                total = item_totals.get(item_key, 0)
                if total < count:
                    logger.warning(f"User {discord_id} lacks supply {item_key} (Has {total}, Needs {count})")
                    return False

            # 2. Deduction Phase with Rollback
            deducted_items = []
            rollback_needed = False

            for item_key, count in supplies.items():
                if self.db.remove_inventory_item(discord_id, item_key, count):
                    deducted_items.append((item_key, count))
                else:
                    logger.error(f"Failed to deduct supply {item_key} for {discord_id} (Race Condition?)")
                    rollback_needed = True
                    break

            if rollback_needed:
                logger.warning(f"Rolling back supply deduction for {discord_id}...")
                for key, amount in deducted_items:
                    meta = item_meta.get(key)
                    if meta:
                        self.inventory_manager.add_item(
                            discord_id,
                            key,
                            meta["name"],
                            meta["type"],
                            meta["rarity"],
                            amount,
                        )
                    else:
                        logger.error(
                            f"Critical: Failed to rollback {key} x{amount} for {discord_id} (Metadata missing)"
                        )
                return False

        start_time = WorldTime.now()
        end_time = (
            start_time + datetime.timedelta(days=90)
            if duration_minutes == -1
            else start_time + datetime.timedelta(minutes=duration_minutes)
        )

        try:
            # Perform buff cleanup before starting new session
            self.db.clear_expired_buffs(discord_id)

            # Apply Passive Regeneration (heal before adventure starts)
            self.db.apply_passive_regen(discord_id)

            # Cleanup old sessions and create new one
            self.db.delete_adventure_session(discord_id, active=0)
            self.db.insert_adventure_session(
                discord_id,
                location_id,
                start_time.isoformat(),
                end_time.isoformat(),
                duration_minutes,
                supplies=supplies or {},
                status="in_progress",
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

    def simulate_adventure_step(self, discord_id: int, action: str = None) -> dict:
        # OPTIMIZATION: Fetch session and context in a single DB round-trip
        bundle = self.db.get_combat_context_bundle(discord_id)
        session_row = bundle.get("active_session") if bundle else None

        if not session_row:
            return {
                "sequence": [["Error: No active session found."]],
                "dead": True,
                "vitals": {"current_hp": 0, "current_mp": 0},
                "player_stats": None,
                "active_monster": None,
            }

        session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, session_row)

        result = session.simulate_step(context_bundle=bundle, action=action)

        if result.get("dead", False):
            loss_msg = self._handle_death_rewards(discord_id, session)
            if loss_msg:
                # Append to the last frame of the sequence
                if result["sequence"]:
                    last_frame = result["sequence"][-1]
                    last_frame.append(loss_msg)

        return result

    def _handle_death_rewards(self, discord_id, session) -> str | None:
        """Extracts partial rewards on death and returns a loss report."""
        loss_report = []
        try:
            # 1. Clean Session Loot (Prevent EXP/Aurum items)
            session.loot.pop("exp", None)
            session.loot.pop("aurum", None)

            # 2. Aurum Penalty (10%)
            current_aurum = self.db.get_player_field(discord_id, "aurum") or 0
            aurum_loss = int(current_aurum * 0.10)
            if aurum_loss > 0:
                self.db.deduct_aurum(discord_id, aurum_loss)
                loss_report.append(f"• -{aurum_loss} {AURUM} (Lost)")

            # 3. Material Penalty (50% of gathered loot)
            material_losses = []
            keys_to_remove = []

            for item_key, count in session.loot.items():
                # Handle Equipment (Serialization)
                if item_key.startswith("__EQUIPMENT__:"):
                    # 50% Chance to lose each equipment piece individually?
                    # Or 50% of the count?
                    # Equipment usually has count 1.
                    # Let's roll for each unit.
                    kept = 0
                    lost = 0
                    try:
                        equip_json = item_key.replace("__EQUIPMENT__:", "", 1)
                        equip_data = json.loads(equip_json)
                        name = equip_data.get("name", "Unknown Item")
                    except Exception:
                        name = "Unknown Equipment"

                    for _ in range(count):
                        # 50% chance to lose
                        if random.random() < 0.5:
                            lost += 1
                        else:
                            kept += 1

                    if lost > 0:
                        material_losses.append(f"• -{lost}x {name} (Equipment)")

                    if kept > 0:
                        session.loot[item_key] = kept
                    else:
                        keys_to_remove.append(item_key)
                    continue

                kept_amount = int(count * 0.5)
                lost_amount = count - kept_amount

                if lost_amount > 0:
                    mat = MATERIALS.get(item_key)
                    name = mat["name"] if mat else item_key
                    material_losses.append(f"• -{lost_amount}x {name}")

                if kept_amount > 0:
                    session.loot[item_key] = kept_amount
                else:
                    keys_to_remove.append(item_key)

            for k in keys_to_remove:
                del session.loot[k]

            if material_losses:
                loss_report.extend(material_losses)

            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)

            items = self._grant_rewards_internal(session, 0, p_stats)

            # Separate bulk items (materials) and equipment (single items)
            bulk_items = []
            equipment_items = []

            for item in items:
                if item["type"] == "equipment":
                    equipment_items.append(item)
                else:
                    bulk_items.append(
                        {
                            "item_key": item["key"],
                            "item_name": item["name"],
                            "item_type": item["type"],
                            "rarity": item["rarity"],
                            "amount": item["amount"],
                        }
                    )

            failed_items = self.inventory_manager.add_items_bulk(discord_id, bulk_items) or []

            # Grant Equipment via Helper
            failed_equipment = self._grant_equipment_loot(discord_id, equipment_items)

            # Combine failures
            if failed_items is None:
                failed_items = []
            failed_items.extend(failed_equipment)

            if failed_items:
                failed_names = sorted(list(set(f["item_name"] for f in failed_items)))
                loss_report.append(f"• {SKULL} Lost (Full Pack): {', '.join(failed_names)}")

            self.db.end_adventure_session(discord_id)

            if loss_report:
                return "\n" + SKULL + " **Losses Incurred:**\n" + "\n".join(loss_report)
            return None

        except Exception as e:
            logger.error(f"Error handling death for {discord_id}: {e}")
            return None

    def end_adventure(self, discord_id: int) -> dict | None:
        try:
            # 1. Optimistic Locking
            if not self.db.lock_adventure_for_claiming(discord_id):
                # If locking failed, check if it's because there is no session
                active = self.db.get_active_adventure(discord_id)
                if not active:
                    return None
                # If active session exists but lock failed, it's already being claimed
                logger.warning(f"Adventure duplicate claim prevention for {discord_id}")
                return None

            stats_json = self.db.get_player_stats_json(discord_id)
            p_stats = PlayerStats.from_dict(stats_json)
            items_to_add = []
            summary = None

            # 2. Get Locked Session
            # We fetch again (or use cached if we fetched for check) but status might be 'claiming' now
            # get_active_adventure filters by 'active: 1', status irrelevant for retrieval here
            row = self.db.get_active_adventure(discord_id)
            if not row:
                return None

            session = AdventureSession(self.db, self.quest_system, self.inventory_manager, discord_id, row)

            # --- EXPLOIT FIX: Retreating while in Combat ---
            # If the player manually ends the adventure (Retreat) while an active monster is present,
            # they are fleeing in panic. We apply a 25% material penalty (Emergency Extraction).
            penalty_logs = []
            if session.active_monster:
                monster_name = session.active_monster.get("name", "Unknown Enemy")
                penalty_logs.append(
                    f"⚠️ **Emergency Extraction!** You fled from {monster_name}, losing supplies in the chaos."
                )

                # Apply 25% penalty to gathered materials
                keys_to_remove = []
                for item_key, count in session.loot.items():
                    # Skip exp/aurum (handled separately below)
                    if item_key in ("exp", "aurum"):
                        continue

                    kept_amount = int(count * 0.75)  # Keep 75%, Lose 25%
                    lost_amount = count - kept_amount

                    if lost_amount > 0:
                        mat = MATERIALS.get(item_key)
                        name = mat["name"] if mat else item_key
                        penalty_logs.append(f"• -{lost_amount}x {name} (Panic)")

                    if kept_amount > 0:
                        session.loot[item_key] = kept_amount
                    else:
                        keys_to_remove.append(item_key)

                for k in keys_to_remove:
                    del session.loot[k]

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

            # --- FACTION REPUTATION ---
            duration_min = row.get("duration_minutes", 0)
            # If duration is -1, calculate actual time elapsed
            if duration_min == -1:
                start_dt = datetime.datetime.fromisoformat(row["start_time"])
                duration_min = int((WorldTime.now() - start_dt).total_seconds() / 60)

            # Ensure non-negative duration
            duration_min = max(0, duration_min)

            faction_logs = self.faction_system.grant_reputation_for_adventure(
                discord_id, duration_min, row.get("location_id")
            )
            # --------------------------

            summary = {
                "loot": items_to_add,
                "xp_gained": total_exp,
                "aurum_gained": total_aurum,
                "old_level": old_level,
                "new_level": new_level,
                "leveled_up": new_level > old_level,
                "faction_logs": faction_logs,
                "penalty_logs": penalty_logs,
            }

            bulk_items = []
            equipment_items = []

            for item in items_to_add:
                if item["type"] == "equipment":
                    equipment_items.append(item)
                else:
                    bulk_items.append(
                        {
                            "item_key": item["key"],
                            "item_name": item["name"],
                            "item_type": item["type"],
                            "rarity": item["rarity"],
                            "amount": item["amount"],
                        }
                    )

            failed_items = self.inventory_manager.add_items_bulk(discord_id, bulk_items) or []

            # Grant Equipment via Helper
            failed_equipment = self._grant_equipment_loot(discord_id, equipment_items)
            failed_items.extend(failed_equipment)

            if failed_items:
                summary["failed_items"] = failed_items

            # --- EXPLORATION ACHIEVEMENTS ---
            try:
                # 1. Update Stats
                self.db.update_exploration_stats(discord_id, row.get("location_id", "unknown"), duration_min)

                # 2. Check Achievements
                ach_system = AchievementSystem(self.db)
                new_title_msg = ach_system.check_exploration_achievements(discord_id)
                new_duration_msg = ach_system.check_duration_achievements(discord_id, duration_min)

                msgs = []
                if new_title_msg:
                    msgs.append(new_title_msg)
                if new_duration_msg:
                    msgs.append(new_duration_msg)

                if msgs:
                    summary["new_titles"] = "\n".join(msgs)
            except Exception as e:
                logger.error(
                    f"Error checking exploration achievements for {discord_id}: {e}",
                    exc_info=True,
                )

            # End session ONLY after items are safely added
            self.db.end_adventure_session(discord_id)

            return summary

        except Exception as e:
            logger.error(f"Error ending adventure for {discord_id}: {e}", exc_info=True)
            return None

    def _grant_rewards_internal(self, session, total_exp, player_stats):
        """Helper to calculate and apply rewards."""
        p_row = self.db.get_player(session.discord_id)

        level_sys = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )

        leveled_up = False
        if total_exp > 0:
            leveled_up = level_sys.add_exp(total_exp)

        # Save Vitals & Level
        current_hp = p_row["current_hp"]
        saved_hp = 1 if current_hp <= 0 else current_hp

        # FIX: Restore HP/MP on level up, otherwise preserve current values
        # Prevents "free healing" exploit by ending adventure without leveling
        target_mp = level_sys.stats.max_mp if leveled_up else p_row["current_mp"]
        target_hp = level_sys.stats.max_hp if leveled_up else saved_hp

        self.db.update_player_mixed(
            session.discord_id,
            set_fields={
                "level": level_sys.level,
                "experience": level_sys.exp,
                "exp_to_next": level_sys.exp_to_next,
                "current_hp": target_hp,
                "current_mp": target_mp,
                "last_regen_time": WorldTime.now().isoformat(),  # Reset regen timer
            },
            inc_fields={"vestige_pool": total_exp},
        )

        items_awarded = []
        for item_key, count in session.loot.items():
            # EQUIPMENT HANDLING
            if item_key.startswith("__EQUIPMENT__:"):
                try:
                    equip_json = item_key.replace("__EQUIPMENT__:", "", 1)
                    equip_data = json.loads(equip_json)
                    items_awarded.append(
                        {
                            "key": item_key,  # Keep full key so we can access json later if needed
                            "name": equip_data["name"],
                            "type": "equipment",
                            "rarity": equip_data["rarity"],
                            "amount": count,
                            "data": equip_data,  # Pass full data
                        }
                    )
                except Exception as e:
                    logger.error(f"Error parsing equipment key {item_key}: {e}")
                continue

            mat = MATERIALS.get(item_key)
            name = mat["name"] if mat else item_key
            rarity = mat.get("rarity", "Common") if mat else "Common"
            items_awarded.append(
                {
                    "key": item_key,
                    "name": name,
                    "type": "material",
                    "rarity": rarity,
                    "amount": count,
                }
            )

        return items_awarded

    def _grant_equipment_loot(self, discord_id: int, equipment_items: list) -> list[dict]:
        """
        Helper to grant equipment items individually.
        Returns a list of failed items (dict with item_name).
        """
        failed = []
        for equip in equipment_items:
            item_data = equip.get("data")
            if not item_data:
                logger.error(f"Missing data for equipment reward: {equip.get('name', 'Unknown')}")
                continue

            for _ in range(equip["amount"]):
                success = self.inventory_manager.add_item(
                    discord_id,
                    str(item_data["id"]),
                    item_data["name"],
                    "equipment",
                    item_data["rarity"],
                    1,
                    item_data["slot"],
                    item_data["source"],
                )
                if not success:
                    failed.append({"item_name": item_data["name"], "reason": "Inventory Full"})
        return failed

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

            start = WorldTime.now()
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
                    "version": 1,
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to start trial for {discord_id}: {e}")
            return False
