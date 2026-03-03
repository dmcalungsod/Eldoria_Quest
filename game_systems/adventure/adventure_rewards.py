"""
adventure_rewards.py

Handles post-combat rewards: Loot, XP, Stat growth, Skill growth.
Hardened to ensure atomic reward distribution.
"""

import json
import logging
import random
from collections import Counter, defaultdict

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.emojis import get_rarity_ansi
from game_systems.data.materials import MATERIALS
from game_systems.guild_system.faction_system import FactionSystem
from game_systems.guild_system.rank_system import RankSystem
from game_systems.guild_system.tournament_system import TournamentSystem
from game_systems.items.item_manager import item_manager
from game_systems.player.achievement_system import AchievementSystem
from game_systems.player.player_stats import PlayerStats, calculate_practice_threshold
from game_systems.rewards.loot_calculator import LootCalculator

logger = logging.getLogger("eldoria.rewards")

# Configuration
SKILL_EXP_THRESHOLD = 100
SKILL_EXP_PER_USE = 2.5

STAT_UP_MESSAGES = {
    "STR": f"{E.STR} Your arms feel stronger. (**STR +1**)",
    "END": f"{E.CON} Your skin toughens. (**END +1**)",
    "DEX": f"{E.DEX} Your aim sharpens. (**DEX +1**)",
    "AGI": f"{E.AGI} You move with new grace. (**AGI +1**)",
    "MAG": f"{E.INT} Your mind expands. (**MAG +1**)",
    "LCK": f"{E.LCK} Fate smiles upon you. (**LCK +1**)",
}

STAT_EXP_GAINS = {
    "str_exp": lambda br: br.get("str_hits", 0) * 0.5,
    "dex_exp": lambda br: (br.get("dex_hits", 0) * 0.5)
    + (br.get("player_crit", 0) * 2.0),
    "agi_exp": lambda br: br.get("player_dodge", 0) * 1.5,
    "end_exp": lambda br: (br.get("hits_taken", 0) * 1.0)
    + (br.get("damage_taken", 0) * 0.1),
    "mag_exp": lambda br: br.get("mag_hits", 0) * 1.0,
    "lck_exp": lambda br: 0.5
    + (br.get("player_crit", 0) * 0.5)
    + (br.get("player_dodge", 0) * 0.5),
}


class AdventureRewards:
    def __init__(self, db: DatabaseManager, discord_id: int):
        self.db = db
        self.discord_id = discord_id
        self.rank_system = RankSystem(db)
        self.achievement_system = AchievementSystem(db)
        self.faction_system = FactionSystem(db)

    def process_victory(
        self,
        battle_report,
        report_list,
        combat_result,
        quest_system,
        inventory_manager,
        session_loot,
        location_id: str | None = None,
    ):
        """
        Master reward processor.
        Coordinates all sub-systems safely.
        """
        logs = []

        try:
            # 1. Promotion Trial
            monster_data = combat_result.get("monster_data", {})
            promo_rank = monster_data.get("promotion_target")

            if promo_rank:
                success, msg = self.rank_system.finalize_promotion(
                    self.discord_id, promo_rank
                )
                if success:
                    logs.append(
                        f"\n{E.MEDAL} **PROMOTION SUCCESSFUL!**\nYou are now **Rank {promo_rank}**."
                    )

            # 2. Loot & Quests
            actual_drops = self._process_loot_and_quests(
                combat_result,
                quest_system,
                inventory_manager,
                session_loot,
                logs,
                location_id,
            )

            # 3. Stat Growth
            self._process_stat_exp(battle_report, logs)

            # 4. Skill Growth
            self._process_skill_exp(report_list, logs)

            # 5. Kill Counters
            tier = monster_data.get("tier")
            self._increment_kill_counter(tier)

            # Record specific monster kill
            monster_name = monster_data.get("name", "Unknown")
            self.db.increment_specific_monster_kill(self.discord_id, monster_name)

            # --- TOURNAMENT HOOK ---
            try:
                tournament = TournamentSystem(self.db)
                tournament.record_action(self.discord_id, "monster_kills", 1)
                if tier == "Boss":
                    tournament.record_action(self.discord_id, "boss_kills", 1)

                # Event: Spectral Tide
                ectoplasm_count = actual_drops.count("ectoplasm")
                if ectoplasm_count > 0:
                    tournament.record_action(
                        self.discord_id, "spectral_tide", ectoplasm_count
                    )

                # Event: Elemental Harvest
                mote_count = actual_drops.count("elemental_mote")
                if mote_count > 0:
                    tournament.record_action(
                        self.discord_id, "elemental_harvest", mote_count
                    )

            except Exception as e:
                logger.error(f"Tournament hook error: {e}")
            # -----------------------

            # 6. Achievements
            ach_msg = self.achievement_system.check_kill_achievements(
                self.discord_id, tier
            )
            if ach_msg:
                logs.append(f"\n{ach_msg}")

            # Check Group Achievements
            group_ach_msg = self.achievement_system.check_group_achievements(
                self.discord_id, monster_name
            )
            if group_ach_msg:
                logs.append(f"\n{group_ach_msg}")

            # Check Combat Achievements
            player_doc = self.db.get_player(self.discord_id)
            if player_doc:
                class_name = player_doc.get("class_name", "Unknown")
                damage_taken = battle_report.get("damage_taken")
                if damage_taken is not None:
                    combat_ach_msg = self.achievement_system.check_combat_achievements(
                        self.discord_id, class_name, damage_taken
                    )
                    if combat_ach_msg:
                        logs.append(f"\n{combat_ach_msg}")

            # 7. Faction Reputation
            faction_logs = self.faction_system.grant_reputation_for_kill(
                self.discord_id, combat_result.get("monster_data", {})
            )
            if faction_logs:
                logs.append("\n" + "\n".join(faction_logs))

        except Exception as e:
            logger.error(
                f"Reward processing failed for {self.discord_id}: {e}", exc_info=True
            )
            logs.append(f"\n{E.ERROR} *An error occurred processing some rewards.*")

        return logs

    def _process_loot_and_quests(
        self,
        combat_result,
        quest_system,
        inventory_manager,
        session_loot,
        logs,
        location_id=None,
    ):
        """Calculates drops and updates quest progress."""
        loot_bundle = defaultdict(int)
        exp_gain = combat_result["exp"]
        aurum_gain = combat_result.get("aurum", 0)
        actual_drops = []  # Track items that actually dropped for quests

        # Apply global aurum boost from active event modifiers
        aurum_boost = combat_result.get("active_boosts", {}).get("aurum_boost", 1.0)
        aurum_gain = int(aurum_gain * aurum_boost)

        # Add XP and Aurum to session loot immediately
        self._add_loot_to_session(session_loot, "exp", exp_gain)
        if aurum_gain > 0:
            self._add_loot_to_session(session_loot, "aurum", aurum_gain)

        # Determine drops
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        loot_boost = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # EVENT HOOK: Frostfall Loot Bonus
        if location_id == "frostfall_expanse":
            frostfall_bonus = combat_result.get("active_boosts", {}).get(
                "frostfall_loot_bonus", 1.0
            )
            loot_boost *= float(frostfall_bonus)

        # EVENT HOOK: Wailing Chasm Loot Bonus
        if location_id == "the_wailing_chasm":
            wailing_chasm_bonus = combat_result.get("active_boosts", {}).get(
                "wailing_chasm_loot_bonus", 1.0
            )
            loot_boost *= float(wailing_chasm_bonus)

        # EVENT HOOK: Ouros Loot Bonus
        if location_id == "silent_city_ouros":
            ouros_bonus = combat_result.get("active_boosts", {}).get(
                "ouros_loot_bonus", 1.0
            )
            loot_boost *= float(ouros_bonus)

        # Check for World Event: Elemental Surge or Spectral Tide
        try:
            active_event = self.db.get_active_world_event()
            if active_event:
                # Elemental Surge
                if active_event.get("type") == "elemental_surge":
                    # 30% chance to drop 1-3 Elemental Motes
                    if random.random() < 0.3:  # nosec B311
                        mote_count = random.randint(1, 3)  # nosec B311
                        self._add_loot_to_session(
                            session_loot, "elemental_mote", mote_count
                        )

                        mote_info = MATERIALS.get("elemental_mote", {})
                        loot_bundle[
                            (
                                mote_info.get("name", "Elemental Mote"),
                                mote_info.get("rarity", "Uncommon"),
                            )
                        ] += mote_count

                        # We add to actual_drops so quests/tournaments can track it
                        for _ in range(mote_count):
                            actual_drops.append("elemental_mote")

                # Spectral Tide
                elif active_event.get("type") == "spectral_tide":
                    # 30% chance to drop 1-2 Ectoplasm
                    if random.random() < 0.3:  # nosec B311
                        ecto_count = random.randint(1, 2)  # nosec B311
                        self._add_loot_to_session(session_loot, "ectoplasm", ecto_count)

                        ecto_info = MATERIALS.get("ectoplasm", {})
                        loot_bundle[
                            (
                                ecto_info.get("name", "Ectoplasm"),
                                ecto_info.get("rarity", "Uncommon"),
                            )
                        ] += ecto_count

                        for _ in range(ecto_count):
                            actual_drops.append("ectoplasm")

        except Exception as e:
            logger.error(f"Event loot error: {e}")

        # Material Drops (via Centralized Calculator)
        rolled_drops = LootCalculator.roll_drops(
            combat_result.get("drops", []), stats.luck, loot_boost
        )

        for drop_key in rolled_drops:
            self._add_loot_to_session(session_loot, drop_key, 1)
            mat = MATERIALS.get(drop_key, {})
            rarity = mat.get("rarity", "Common")
            loot_bundle[(mat.get("name", drop_key), rarity)] += 1
            actual_drops.append(drop_key)

        # Equipment Drops
        eq_list = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in eq_list:
            # Add item to DB immediately to prevent loss
            success = inventory_manager.add_item(
                self.discord_id,
                str(item["id"]),
                item["name"],
                "equipment",
                item["rarity"],
                1,
                item["slot"],
                item["source"],
            )
            if success:
                loot_bundle[(item["name"], item["rarity"])] += 1
            else:
                logs.append(
                    f"\n{E.ERROR} **Inventory Full!** Left **{item['name']}** behind."
                )

            # Assuming equipment doesn't trigger "collect" quests for now, or if it does, it's not handled here.
            # Usually collect quests are for materials.

        # Format Logs
        loot_lines = [get_rarity_ansi("Common", f"• {exp_gain} EXP")]
        if aurum_gain > 0:
            loot_lines.append(get_rarity_ansi("Common", f"• {aurum_gain} {E.AURUM}"))

        # Sort by Rarity
        rarity_order = {
            "Common": 0,
            "Uncommon": 1,
            "Rare": 2,
            "Epic": 3,
            "Legendary": 4,
            "Mythical": 5,
        }
        sorted_loot = sorted(
            loot_bundle.items(), key=lambda x: (rarity_order.get(x[0][1], 0), x[0][1])
        )

        for (name, rarity), count in sorted_loot:
            qty = f" (x{count})" if count > 1 else ""
            loot_lines.append(get_rarity_ansi(rarity, f"• {name}{qty}"))

        if loot_lines:
            block = "\n".join(loot_lines)
            logs.append(f"{E.ITEM_BOX} **Loot Acquired**\n```ansi\n{block}```")

        # Quest Updates
        # FIX: Pass only actual drops, not potential drops
        self._update_quests(
            quest_system, combat_result["monster_data"]["name"], actual_drops, logs
        )

        return actual_drops

    def _update_quests(self, quest_system, monster_name, actual_drops, logs):
        updated = []
        quests = quest_system.get_player_quests(self.discord_id)

        # Aggregate drops for efficiency (one DB update per item type)
        drop_counts = Counter(actual_drops)

        for q in quests:
            progress_made = False
            objs = q.get("objectives", {})
            flavor_text = q.get("flavor_text", {})
            added_flavors = set()

            # Defeat check
            if "defeat" in objs and monster_name in objs["defeat"]:
                quest_system.update_progress(
                    self.discord_id, q["id"], "defeat", monster_name
                )
                progress_made = True

                # Check for flavor text
                key = f"defeat:{monster_name}"
                if key in flavor_text:
                    logs.append(f"\n*{flavor_text[key]}*")

            # Collect check
            if "collect" in objs:
                for dk, count in drop_counts.items():
                    if dk in objs["collect"]:
                        quest_system.update_progress(
                            self.discord_id, q["id"], "collect", dk, amount=count
                        )
                        progress_made = True

                        # Check for flavor text (avoid spamming if multiple drop)
                        key = f"collect:{dk}"
                        if key in flavor_text and key not in added_flavors:
                            logs.append(f"\n*{flavor_text[key]}*")
                            added_flavors.add(key)

            # Examine check (for exploration events)
            if "examine" in objs:
                for dk, count in drop_counts.items():
                    if dk in objs["examine"]:
                        quest_system.update_progress(
                            self.discord_id, q["id"], "examine", dk, amount=count
                        )
                        progress_made = True

                        key = f"examine:{dk}"
                        if key in flavor_text and key not in added_flavors:
                            logs.append(f"\n*{flavor_text[key]}*")
                            added_flavors.add(key)

            if progress_made:
                updated.append(q["title"])

        if updated:
            logs.append(f"\n{E.QUEST_SCROLL} *Quest Updated: {', '.join(updated)}*")

        return actual_drops

    def _calculate_growth(self, current_exp, gain, threshold):
        """Helper to calculate leveling progress."""
        current_exp += gain
        levels_gained = 0
        while current_exp >= threshold:
            current_exp -= threshold
            levels_gained += 1
        return current_exp, levels_gained

    def _process_stat_exp(self, br, logs):
        """
        Updates practice-based stat experience.
        """
        gains = {k: fn(br) for k, fn in STAT_EXP_GAINS.items()}

        try:
            # SECURITY: Retry Loop for Optimistic Locking
            attempts = 0
            while attempts < 3:
                row = self.db.get_stat_exp_row(self.discord_id)

                if not row:
                    return

                original_json_str = row["stats_json"]
                stats_data = json.loads(original_json_str)
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}

                # Capture original values for optimistic lock
                original_exps = {k: row[k] for k in STAT_EXP_GAINS.keys()}

                # Mutable exp dict
                curr_exp = original_exps.copy()
                level_up_msgs = []

                for exp_key, gain in gains.items():
                    if gain <= 0:
                        continue

                    stat_key = exp_key.split("_")[0].upper()
                    current_val = base_stats[stat_key]
                    current_exp_val = curr_exp[exp_key] + gain

                    levels_gained = 0

                    # Dynamic Threshold Check
                    while True:
                        threshold = calculate_practice_threshold(current_val)
                        if current_exp_val >= threshold:
                            current_exp_val -= threshold
                            levels_gained += 1
                            current_val += 1
                        else:
                            break

                    curr_exp[exp_key] = current_exp_val
                    base_stats[stat_key] = current_val

                    if levels_gained > 0:
                        if stat_key in STAT_UP_MESSAGES:
                            # Append message only once per stat type to avoid spam, or repeat?
                            # Original code appended once per level. Let's keep it simple.
                            # Assuming usually 1 level at a time.
                            for _ in range(levels_gained):
                                level_up_msgs.append(STAT_UP_MESSAGES[stat_key])

                # Save updates
                for s, v in base_stats.items():
                    stats_data[s]["base"] = v

                # Optimistic Update
                success = self.db.update_stat_exp(
                    self.discord_id,
                    original_json_str,
                    original_exps,
                    json.dumps(stats_data),
                    curr_exp["str_exp"],
                    curr_exp["end_exp"],
                    curr_exp["dex_exp"],
                    curr_exp["agi_exp"],
                    curr_exp["mag_exp"],
                    curr_exp["lck_exp"],
                )

                if success:
                    if level_up_msgs:
                        logs.append("\n" + "\n".join(level_up_msgs))
                    break

                attempts += 1
                logger.warning(
                    f"Stat XP race condition for {self.discord_id}. Retrying ({attempts}/3)..."
                )

        except Exception as e:
            logger.error(f"Stat XP error: {e}")

    def _process_skill_exp(self, report_list, logs):
        """Updates skill levels."""
        usage = defaultdict(int)
        for entry in report_list:
            if entry.get("skill_key_used"):
                usage[entry["skill_key_used"]] += 1

        if not usage:
            return

        try:
            msgs = []
            for s_key, count in usage.items():
                row = self.db.get_skill_with_definition(self.discord_id, s_key)

                if not row:
                    continue

                lvl, exp, name = row["skill_level"], row["skill_exp"], row["name"]
                gain = count * SKILL_EXP_PER_USE

                new_exp, levels = self._calculate_growth(exp, gain, SKILL_EXP_THRESHOLD)

                if levels > 0:
                    lvl += levels
                    msgs.append(f"{E.LEVEL_UP} **{name}** reached **Level {lvl}**!")

                self.db.update_player_skill(
                    self.discord_id, s_key, skill_level=lvl, skill_exp=new_exp
                )

            if msgs:
                logs.append("\n" + "\n".join(msgs))
        except Exception as e:
            logger.error(f"Skill XP error: {e}")

    def _increment_kill_counter(self, tier):
        field = {
            "Normal": "normal_kills",
            "Elite": "elite_kills",
            "Boss": "boss_kills",
        }.get(tier)
        if field:
            self.db.increment_guild_stat(self.discord_id, field)

    def _add_loot_to_session(self, session_loot, key, amt):
        session_loot[key] = session_loot.get(key, 0) + amt
