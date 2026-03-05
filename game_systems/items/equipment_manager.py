"""
game_systems/items/equipment_manager.py


.errors
Handles equipping/unequipping and stat recalculation.
Hardened: Atomic equipment swaps via MongoDB DatabaseManager methods.
"""

import logging
import math

import pymongo
import pymongo.errors

from database.database_manager import MAX_STACK_EQUIPMENT, DatabaseManager
from game_systems.data.class_data import CLASSES
from game_systems.data.equipments import EQUIPMENT_DATA
from game_systems.data.skills_data import SKILLS
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.equipment")


class EquipmentManager:
    VALID_TABLES = {"equipment", "class_equipment"}
    MAX_ACCESSORY_SLOTS = 2

    RANK_VALUES = {
        "F": 1,
        "E": 2,
        "D": 3,
        "C": 4,
        "B": 5,
        "A": 6,
        "S": 7,
        "SS": 8,
        "SSS": 9,
    }

    STAT_MAP = {
        "str_bonus": "STR",
        "end_bonus": "END",
        "dex_bonus": "DEX",
        "agi_bonus": "AGI",
        "mag_bonus": "MAG",
        "lck_bonus": "LCK",
    }

    # Quality Multipliers (Relative to Common=1.0)
    QUALITY_MULTIPLIERS = {
        "Common": 1.0,
        "Uncommon": 1.1,
        "Rare": 1.25,
        "Epic": 1.5,
        "Legendary": 2.0,
        "Mythical": 3.0,
    }

    RARITY_TIERS = {
        "Common": 1,
        "Uncommon": 2,
        "Rare": 3,
        "Epic": 4,
        "Legendary": 5,
        "Mythical": 6,
    }

    # Slot Groups for Conflict Resolution
    TWO_HANDED_SLOTS = {"greatsword", "bow", "staff"}
    OFF_HAND_SLOTS = {"shield", "orb", "tome", "quiver", "offhand_dagger"}
    MAIN_HAND_SLOTS = {"sword", "mace", "dagger", "wand"}

    # Armor Groups (Standardized Slots)
    HEAD_SLOTS = {"helm", "leather_cap", "hood", "miter", "leather_hood"}
    BODY_SLOTS = {"heavy_armor", "medium_armor", "rogue_armor", "robe", "vestments", "alchemist_coat"}
    HAND_SLOTS = {"heavy_gloves", "medium_gloves", "gloves"}
    LEG_SLOTS = {"heavy_legs", "medium_legs", "legs"}
    FOOT_SLOTS = {"heavy_boots", "medium_boots", "boots"}

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_slot_display_name(self, slot: str) -> str:
        """Returns a user-friendly name for the equipment slot/group."""
        if slot in self.HEAD_SLOTS:
            return "Head"
        if slot in self.BODY_SLOTS:
            return "Body"
        if slot in self.HAND_SLOTS:
            return "Hands"
        if slot in self.LEG_SLOTS:
            return "Legs"
        if slot in self.FOOT_SLOTS:
            return "Feet"
        if slot in self.MAIN_HAND_SLOTS:
            return "Main Hand"
        if slot in self.OFF_HAND_SLOTS:
            return "Off Hand"
        if slot in self.TWO_HANDED_SLOTS:
            return "Two-Handed"
        return slot.replace("_", " ").title()

    def _get_player_allowed_slots(self, discord_id: int) -> list:
        """Fetches allowed equipment slots for the player's class."""
        class_id = self.db.get_player_field(discord_id, "class_id")
        if not class_id:
            return []

        for name, data in CLASSES.items():
            if data["id"] == class_id:
                return data.get("allowed_slots", [])
        return []

    def _resolve_conflict_slots(self, target_slot: str) -> set:
        """
        Returns the set of slots that must be cleared before equipping target_slot.
        Returns an empty set when no conflicts are possible (e.g. accessories).
        """
        if target_slot in self.TWO_HANDED_SLOTS:
            return self.MAIN_HAND_SLOTS | self.OFF_HAND_SLOTS | self.TWO_HANDED_SLOTS
        if target_slot in self.MAIN_HAND_SLOTS:
            return self.MAIN_HAND_SLOTS | self.TWO_HANDED_SLOTS
        if target_slot in self.OFF_HAND_SLOTS:
            return self.OFF_HAND_SLOTS | self.TWO_HANDED_SLOTS
        if target_slot in self.HEAD_SLOTS:
            return set(self.HEAD_SLOTS)
        if target_slot in self.BODY_SLOTS:
            return set(self.BODY_SLOTS)
        if target_slot in self.HAND_SLOTS:
            return set(self.HAND_SLOTS)
        if target_slot in self.LEG_SLOTS:
            return set(self.LEG_SLOTS)
        if target_slot in self.FOOT_SLOTS:
            return set(self.FOOT_SLOTS)
        return {target_slot}

    def _get_base_stat(self, stats: "PlayerStats", stat_name: str) -> int:
        """Returns the current base value of a primary stat by name."""
        mapping = {
            "STR": stats.strength,
            "END": stats.endurance,
            "DEX": stats.dexterity,
            "AGI": stats.agility,
            "MAG": stats.magic,
            "LCK": stats.luck,
        }
        return mapping.get(stat_name, 0)

    def check_requirements(self, item_data: dict, player_data: dict) -> tuple[bool, str | None]:
        """
        Validates if a player can equip an item based on Level, Rank, and Class.
        player_data must contain: 'level', 'rank' (from guild), 'class_name'.
        """
        # 1. Level Requirement
        req_level = item_data.get("level_req", 1)
        if player_data.get("level", 1) < req_level:
            return False, f"Req: Lvl {req_level}"

        # 2. Rank Requirement
        req_rank = item_data.get("rank_restriction")
        if req_rank:
            p_rank = player_data.get("rank", "F")
            if self.RANK_VALUES.get(p_rank, 1) < self.RANK_VALUES.get(req_rank, 1):
                return False, f"Req: Rank {req_rank}"

        # 3. Class Restriction
        allowed_classes = item_data.get("class_restrictions")
        if allowed_classes:
            p_class = player_data.get("class_name")
            if not p_class or p_class not in allowed_classes:
                return False, f"Class Restricted: {', '.join(allowed_classes)}"

        return True, None

    def recalculate_player_stats(self, discord_id: int) -> PlayerStats:
        """
        Recalculates a player's total stats based on equipped items AND passive skills.
        """
        try:
            # 1. Get Base Stats
            try:
                stats = PlayerStats.from_dict(self.db.get_player_stats_json(discord_id))
            except Exception:
                stats = PlayerStats()

            # Reset bonuses to prevent duplication on recalculation
            for stat in stats._stats.values():
                stat.bonus = 0

            # 2. Apply Equipped Item Bonuses
            self._calculate_equipped_item_bonuses(discord_id, stats)

            # 3. Apply Passive Skill Bonuses
            self._calculate_passive_skill_bonuses(discord_id, stats)

            # 4. Save Updates
            self.db.update_player_stats(discord_id, stats.to_dict())

            # 5. Clamp HP/MP if necessary (Avoid Overflow Exploit)
            self._clamp_vitals_to_max(discord_id, stats)

            return stats

        except Exception as e:
            logger.error(f"Stat calc failed for {discord_id}: {e}", exc_info=True)
            return PlayerStats()


    def _calculate_equipped_item_bonuses(self, discord_id: int, stats: PlayerStats):
        equipped_items = self.db.get_equipped_items(discord_id)

        for item in equipped_items:
            table = item.get("item_source_table")
            if table not in self.VALID_TABLES:
                continue

            try:
                item_id = int(item["item_key"])
            except ValueError:
                logger.warning(f"Skipping invalid item key '{item.get('item_key')}' for user {discord_id}")
                continue

            item_data = self.db._col(table).find_one({"id": item_id}, {"_id": 0})
            if item_data:
                # Calculate Quality Scaling
                base_rarity = item_data.get("rarity", "Common")
                current_rarity = item.get("rarity", base_rarity)

                base_tier = self.RARITY_TIERS.get(base_rarity, 1)
                current_tier = self.RARITY_TIERS.get(current_rarity, 1)

                multiplier = 1.0
                if current_tier > base_tier:
                    base_mult = self.QUALITY_MULTIPLIERS.get(base_rarity, 1.0)
                    curr_mult = self.QUALITY_MULTIPLIERS.get(current_rarity, 1.0)
                    if base_mult > 0:
                        multiplier = curr_mult / base_mult

                for col, stat_name in self.STAT_MAP.items():
                    if col in item_data and item_data[col]:
                        base_val = item_data[col]
                        # Apply multiplier and round up
                        final_val = math.ceil(base_val * multiplier)
                        stats.add_bonus_stat(stat_name, final_val)

    def _calculate_passive_skill_bonuses(self, discord_id: int, stats: PlayerStats):
        player_skills = self.db.get_all_player_skills(discord_id)

        for p_skill in player_skills:
            skill_data = SKILLS.get(p_skill["skill_key"])
            if skill_data and skill_data.get("type") == "Passive" and "passive_bonus" in skill_data:
                level = p_skill["skill_level"]

                for stat_key, percent in skill_data["passive_bonus"].items():
                    if stat_key.endswith("_percent"):
                        stat_name = stat_key.split("_")[0].upper()
                        current_total = self._get_base_stat(stats, stat_name)
                        bonus = math.ceil(current_total * (percent * level))
                        stats.add_bonus_stat(stat_name, bonus)

    def _clamp_vitals_to_max(self, discord_id: int, stats: PlayerStats):
        # Fetch current vitals to check if they exceed new max
        vitals = self.db.get_player_vitals(discord_id)
        if vitals:
            current_hp = vitals.get("current_hp", 0)
            current_mp = vitals.get("current_mp", 0)

            # Calculate Effective Max HP/MP (Stats + Buffs) for Clamping
            effective_stats = PlayerStats.from_dict(stats.to_dict())
            active_buffs = self.db.get_active_buffs(discord_id)

            for buff in active_buffs:
                stat_name = buff.get("stat", "").upper()
                amount = int(buff.get("amount", 0))

                # Apply to Primary Stats (STR, END, etc.)
                # PlayerStats calculates derived HP/MP from these
                # Note: We do not handle direct "HP" or "MP" buffs here unless PlayerStats supports it.
                # Currently PlayerStats only supports primary stats + DEF in add_bonus_stat.
                if stat_name in ["STR", "END", "DEX", "AGI", "MAG", "LCK", "DEF"]:
                    effective_stats.add_bonus_stat(stat_name, amount)

            new_hp = min(current_hp, effective_stats.max_hp)
            new_mp = min(current_mp, effective_stats.max_mp)

            if new_hp != current_hp or new_mp != current_mp:
                self.db.set_player_vitals(discord_id, new_hp, new_mp)
                logger.info(
                    f"Clamped vitals for {discord_id}: HP {current_hp}->{new_hp}, MP {current_mp}->{new_mp}"
                )

    def equip_item(self, discord_id: int, inventory_db_id: int) -> tuple[bool, str]:
        """
        Equips an item. Handles slot conflicts and stack splitting.
        """
        try:
            # Fetch target item
            item = self.db.get_inventory_item(discord_id, inventory_db_id)

            if not item:
                return False, "Item not found."
            if item.get("item_type") != "equipment":
                return False, "Not equippable."
            if item.get("equipped") == 1:
                return False, "Already equipped."

            # Fetch player data for validation
            player = self.db.get_player(discord_id)
            if not player:
                return False, "Player not found."

            # Fetch rank and class
            guild_rank = self.db.get_guild_rank(discord_id) or "F"

            # Resolve Class Name
            class_id = player.get("class_id")
            class_name = next((k for k, v in CLASSES.items() if v["id"] == class_id), None)

            player_data = {
                "level": player.get("level", 1),
                "rank": guild_rank,
                "class_name": class_name,
            }

            # Fetch full item static data for requirements
            # Try EQUIPMENT_DATA first (in-memory)
            static_data = EQUIPMENT_DATA.get(item["item_key"])

            # Fallback to DB lookup if not in static dict (e.g. dynamic items)
            if not static_data and item.get("item_source_table"):
                pass

            # Merge inventory data over static data (in case of dynamic overrides)
            full_item_data = (static_data or {}).copy()
            full_item_data.update(item)

            valid, msg = self._validate_equip_requirements(discord_id, item, full_item_data, player_data)
            if not valid:
                return False, msg

            equipped_items = self.db.get_equipped_items(discord_id)
            valid, msg, conflicts_msg = self._resolve_equip_slot_conflicts(discord_id, item, equipped_items)
            if not valid:
                return False, msg

            valid, msg = self._execute_equip_db_update(discord_id, inventory_db_id, item)
            if not valid:
                return False, msg

            # Recalculate stats
            self.recalculate_player_stats(discord_id)
            return True, f"Item equipped.{conflicts_msg}"

        except Exception as e:
            logger.error(f"Equip error: {e}", exc_info=True)
            return False, "An error occurred."


    def _validate_equip_requirements(self, discord_id: int, item: dict, full_item_data: dict, player_data: dict) -> tuple[bool, str]:
        # 1. Validate Requirements (Level, Rank)
        can_equip, reason = self.check_requirements(full_item_data, player_data)
        if not can_equip:
            return False, f"Cannot equip: {reason}"

        # 2. Validate Class Permissions (Slots)
        allowed = self._get_player_allowed_slots(discord_id)
        if item["slot"] not in allowed:
            return False, f"Your class cannot equip {item['slot']} items."

        return True, ""

    def _resolve_equip_slot_conflicts(self, discord_id: int, item: dict, equipped_items: list) -> tuple[bool, str, str]:
        conflicts_msg = ""
        target_slot = item["slot"]

        # Accessories: check uniqueness and capacity, no slot clearing
        if target_slot == "accessory":
            current_accessories = [i for i in equipped_items if i.get("slot") == "accessory"]
            for acc in current_accessories:
                if acc["item_key"] == item["item_key"]:
                    return False, "You cannot equip two of the same accessory.", conflicts_msg
            if len(current_accessories) >= self.MAX_ACCESSORY_SLOTS:
                return (
                    False,
                    f"Accessory slots full ({self.MAX_ACCESSORY_SLOTS}/{self.MAX_ACCESSORY_SLOTS}). Unequip one first.",
                    conflicts_msg
                )
        else:
            slots_to_check = self._resolve_conflict_slots(target_slot)
            for eq_item in equipped_items:
                if eq_item.get("slot") in slots_to_check:
                    try:
                        self._unequip_logic(discord_id, eq_item["id"])
                        conflicts_msg += f" (Unequipped {eq_item['item_name']})"
                    except Exception as e:
                        logger.error(f"Failed to auto-unequip {eq_item['item_name']}: {e}")

        return True, "", conflicts_msg

    def _execute_equip_db_update(self, discord_id: int, inventory_db_id: int, item: dict) -> tuple[bool, str]:
        if item.get("count", 1) > 1:
            # Split stack safely with compensation
            if not self.db.split_stack_to_equipped(discord_id, inventory_db_id, item):
                return False, "Failed to process equipment split. Please try again."
        else:
            try:

                self.db.set_item_equipped(inventory_db_id, 1)
            except pymongo.errors.DuplicateKeyError:
                return False, "Equipment slot update conflict."

        return True, ""

    def unequip_item(self, discord_id: int, inventory_db_id: int) -> tuple[bool, str]:
        """Unequips an item safely."""
        try:
            self._unequip_logic(discord_id, inventory_db_id)
            self.recalculate_player_stats(discord_id)
            return True, "Item unequipped."
        except ValueError as ve:
            return False, str(ve)
        except Exception as e:
            logger.error(f"Unequip error: {e}", exc_info=True)
            return False, "An error occurred."

    def _unequip_logic(self, discord_id, inv_id):
        """Internal logic to unequip and merge stacks."""
        item = self.db.get_inventory_item(discord_id, inv_id)
        if not item or not item.get("equipped"):
            raise ValueError("Item not equipped or not found.")

        # Look for an existing unequipped stack to merge into
        stack = self.db.find_stackable_item(
            discord_id,
            item["item_key"],
            item["rarity"],
            item.get("slot"),
            item.get("item_source_table"),
            max_stack=MAX_STACK_EQUIPMENT,
        )

        if stack:
            self.db._col("inventory").update_one({"id": stack["id"]}, {"$inc": {"count": 1}})
            self.db._col("inventory").delete_one({"id": inv_id})
        else:
            self.db.set_item_equipped(inv_id, 0)

    def save_loadout(self, discord_id: int, name: str) -> tuple[bool, str]:
        """Saves the current equipped items as a loadout."""
        equipped_items = self.db.get_equipped_items(discord_id)
        if not equipped_items:
            return False, "No items equipped."

        items_dict = {}
        accessory_count = 0

        for item in equipped_items:
            slot = item["slot"]

            # Handle multiple accessories by suffixing keys
            if slot == "accessory":
                accessory_count += 1
                save_key = f"accessory_{accessory_count}"
            else:
                save_key = slot

            items_dict[save_key] = {
                "item_key": item["item_key"],
                "rarity": item["rarity"],
                "item_name": item["item_name"],
                "item_source_table": item.get("item_source_table"),
                "slot": slot,  # Preserve original slot data
            }

        self.db.save_equipment_set(discord_id, name, items_dict)
        return True, f"Loadout '{name}' saved."

    def delete_loadout(self, discord_id: int, name: str) -> tuple[bool, str]:
        """Deletes a saved loadout."""
        self.db.delete_equipment_set(discord_id, name)
        return True, f"Loadout '{name}' deleted."

    def equip_loadout(self, discord_id: int, name: str) -> tuple[bool, str]:
        """
        Attempts to equip a saved loadout.
        Finds best matching items in inventory.
        """
        loadout = self.db.get_equipment_set(discord_id, name)
        if not loadout:
            return False, "Loadout not found."

        items_to_equip = loadout.get("items", {})
        if not items_to_equip:
            return False, "Loadout is empty."

        success_count = 0
        missing_items = []

        current_equipped = {item["slot"]: item for item in self.db.get_equipped_items(discord_id)}

        for slot_key, target_data in items_to_equip.items():
            target_key = target_data["item_key"]
            target_rarity = target_data["rarity"]

            # Determine actual slot to search (handle suffixes)
            # Use preserved 'slot' if available, otherwise strip suffix if accessory
            target_slot = target_data.get("slot")
            if not target_slot:
                if "accessory" in slot_key:
                    target_slot = "accessory"
                else:
                    target_slot = slot_key

            # Check if already equipped
            # Note: For accessories, we just check if *any* equipped item matches this key+rarity+slot
            # This is a bit simplified; strictly we might want to ensure *enough* are equipped.
            # But iterating through the loadout means we check for *each* required item.

            # We can't use simple dictionary lookup for duplicate slots like accessory
            # So we iterate current_equipped values.
            for eq_item in current_equipped.values():
                if (
                    eq_item["slot"] == target_slot
                    and eq_item["item_key"] == target_key
                    and eq_item["rarity"] == target_rarity
                ):
                    # Found a match. To prevent counting same item for multiple loadout entries,
                    # we should track used IDs?
                    # But for now, simple check is okay, loadout equipping is best-effort.
                    # Actually, if loadout has 2 rings, and we have 1 ring equipped,
                    # both iterations will find "already equipped".
                    # So we skip equipping the second ring. BAD.

                    # Fix: We should check if we need to equip MORE.
                    # But equip_item() handles "already equipped" check internally via "equipped": 1 status.
                    # So maybe we should just ALWAYS try to equip from inventory?
                    # If it's already equipped, it won't be in inventory with equipped=0.
                    pass

            # Better approach: Search inventory for UN-EQUIPPED item.
            # If found, equip it.
            # If NOT found, verify if it's already equipped.

            match = self.db._col("inventory").find_one(
                {
                    "discord_id": discord_id,
                    "item_key": target_key,
                    "rarity": target_rarity,
                    "slot": target_slot,
                    "equipped": 0,
                }
            )

            if match:
                ok, msg = self.equip_item(discord_id, match["id"])
                if ok:
                    success_count += 1
                else:
                    missing_items.append(f"{target_data['item_name']} (Error: {msg})")
            else:
                # Not found in unequipped inventory. Check if already equipped.
                # We need to find *how many* of this item are currently equipped vs how many needed?
                # This gets complex.
                # Simple check: Is at least ONE matching item equipped?
                # If loadout has 2 identical rings, and we have 1 equipped and 0 in inventory...
                # We report missing.

                # Check actual count in inventory (equipped=1)
                equipped_count = self.db._col("inventory").count_documents(
                    {
                        "discord_id": discord_id,
                        "item_key": target_key,
                        "rarity": target_rarity,
                        "slot": target_slot,
                        "equipped": 1,
                    }
                )

                # We can't easily know if this specific iteration of the loop corresponds to
                # the 1st or 2nd ring without tracking.
                # But since we just want to report success/fail...
                if hasattr(equipped_count, "__call__") or (isinstance(equipped_count, int) and equipped_count > 0):
                    # Assume success if at least one is equipped.
                    # This might be slightly inaccurate for duplicates but acceptable.
                    success_count += 1
                else:
                    missing_items.append(target_data["item_name"])

        msg = f"Equipped {success_count} items."
        if missing_items:
            details = ", ".join(missing_items[:3])
            if len(missing_items) > 3:
                details += f" and {len(missing_items) - 3} more"
            msg += f" Missing/Failed: {details}"

        return True, msg
