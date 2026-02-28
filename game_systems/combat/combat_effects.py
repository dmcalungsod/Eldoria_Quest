"""
Combat Effects utility for Eldoria Quest

Handles calculating and processing buffs and debuffs within combat.
Extracted from combat_engine.py to reduce complexity.
"""

from typing import Any

from ..player.player_stats import calculate_tiered_bonus


class CombatEffects:
    @staticmethod
    def get_effective_monster_stats(monster: dict) -> dict:
        """
        Calculates monster stats with active debuffs applied.
        Returns a copy of the monster dict with modified stats.
        """
        eff_monster = monster.copy()

        if "debuffs" in monster:
            for debuff in monster["debuffs"]:
                if debuff.get("type") == "stat_mod":
                    # Apply percentage modifiers
                    for stat in ["ATK", "DEF", "AGI", "DEX"]:
                        key = f"{stat}_percent"
                        if key in debuff:
                            mod = float(debuff[key])
                            base_val = eff_monster.get(stat, 0)
                            new_val = max(0, int(base_val * (1.0 + mod)))
                            eff_monster[stat] = new_val

                    # Special Rogue Debuff: Accuracy
                    if "accuracy_percent" in debuff:
                        acc_mod = float(debuff["accuracy_percent"])
                        eff_monster["accuracy_percent"] = eff_monster.get("accuracy_percent", 0.0) + acc_mod

        return eff_monster

    @staticmethod
    def process_monster_debuffs(monster: dict, monster_hp: int) -> tuple[int, list]:
        """
        Handles damage over time from debuffs on the monster.
        Returns (new_hp, list of log messages)
        """
        if "debuffs" not in monster or not monster["debuffs"]:
            return monster_hp, []

        msgs = []
        active_debuffs = []

        for debuff in monster["debuffs"]:
            debuff_type = debuff.get("type")

            # Legacy Support: If type is missing but damage exists, treat as poison
            if not debuff_type and "damage" in debuff:
                debuff_type = "poison"

            name = debuff.get("name", "Debuff")

            if debuff_type in ["poison", "bleed"]:
                dmg = debuff.get("damage", 0)
                monster_hp -= dmg
                if debuff_type == "poison":
                    msgs.append(f"☠️ **{monster.get('name', 'Enemy')}** takes {dmg} {name.lower()} damage!")
                else:
                    msgs.append(f"🩸 **{monster.get('name', 'Enemy')}** bleeds for {dmg} damage!")

            # Decrement Duration
            debuff["duration"] -= 1
            if debuff["duration"] > 0:
                active_debuffs.append(debuff)
            else:
                msgs.append(f"✅ {name} on **{monster.get('name', 'Enemy')}** has worn off.")

        monster["debuffs"] = active_debuffs
        return monster_hp, msgs

    @staticmethod
    def apply_monster_debuff(monster: dict, skill: dict, stats_dict: dict) -> str | None:
        """
        Applies a debuff to the monster (e.g., Poison, Stat Down).
        Scales damage based on player stats.
        Returns a log string describing the effect, or None.
        """
        debuff_data = skill.get("debuff", {})
        if not debuff_data:
            return None

        # Initialize debuffs list if missing
        if "debuffs" not in monster:
            monster["debuffs"] = []

        # Check for Poison
        if "poison" in debuff_data:
            base_dmg = float(debuff_data["poison"])
            duration = int(debuff_data.get("duration", 3))

            scaling_stat = skill.get("scaling_stat", "DEX").upper()
            stat_val = stats_dict.get(scaling_stat, 10)
            stat_bonus = calculate_tiered_bonus(stat_val, 0.3)
            scaled_dmg = int(base_dmg + stat_bonus)

            existing = next((d for d in monster["debuffs"] if d["type"] == "poison"), None)
            if existing:
                existing["duration"] = duration
                existing["damage"] = max(existing["damage"], scaled_dmg)
                return f"☠️ **{monster.get('name', 'Enemy')}**'s poison is refreshed!"
            else:
                monster["debuffs"].append(
                    {
                        "type": "poison",
                        "damage": scaled_dmg,
                        "duration": duration,
                        "name": "Poison",
                    }
                )
                return f"☠️ **{monster.get('name', 'Enemy')}** is poisoned for {scaled_dmg} dmg/turn!"

        # Check for Stat Modifiers
        stat_mods = {}
        for key in ["ATK_percent", "DEF_percent", "AGI_percent", "DEX_percent", "accuracy_percent"]:
            if key in debuff_data:
                stat_mods[key] = debuff_data[key]

        if stat_mods:
            duration = int(debuff_data.get("duration", 3))
            name = skill.get("name", "Debuff")

            existing = next(
                (d for d in monster["debuffs"] if d.get("name") == name and d.get("type") == "stat_mod"), None
            )

            if existing:
                existing["duration"] = duration
                return f"💢 **{monster.get('name', 'Enemy')}**'s {name} is refreshed!"
            else:
                new_debuff = {
                    "type": "stat_mod",
                    "duration": duration,
                    "name": name,
                }
                new_debuff.update(stat_mods)
                monster["debuffs"].append(new_debuff)
                return f"💢 **{monster.get('name', 'Enemy')}** is weakened by {name}!"

        # Check for Bleed
        if debuff_data.get("type") == "bleed":
            damage = int(debuff_data.get("damage", 5))
            duration = int(debuff_data.get("duration", 3))
            existing = next((d for d in monster["debuffs"] if d.get("type") == "bleed"), None)
            if existing:
                existing["duration"] = duration
                existing["damage"] = max(existing["damage"], damage)
                return f"🩸 **{monster.get('name', 'Enemy')}**'s bleed is refreshed!"
            else:
                monster["debuffs"].append({"type": "bleed", "damage": damage, "duration": duration})
                return f"🩸 **{monster.get('name', 'Enemy')}** is bleeding for {damage} dmg/turn!"

        return None

    @staticmethod
    def apply_skill_buffs(skill: dict, base_stats_dict: dict) -> list[dict[str, Any]]:
        """
        Calculates buffs from a skill and converts % bonuses to flat values.
        Returns a list of calculated new buffs.
        """
        new_buffs: list[dict[str, Any]] = []
        buff_data = skill.get("buff_data", skill.get("buff", {}))
        if not buff_data:
            return new_buffs

        duration = int(buff_data.get("duration", 3))

        def add_buff(stat, amount):
            new_buffs.append(
                {
                    "name": skill.get("name", "Unknown Buff"),
                    "stat": stat,
                    "amount": int(amount),
                    "duration": duration,
                }
            )

        for key, val in buff_data.items():
            if key == "duration":
                continue

            if key == "all_stats_percent":
                for stat_code in ["STR", "END", "DEX", "AGI", "MAG", "LCK"]:
                    current_val = base_stats_dict.get(stat_code, 10)
                    bonus = current_val * float(val)
                    if bonus > 0:
                        add_buff(stat_code, bonus)

            elif key == "next_hit_crit":
                if val:
                    add_buff("next_hit_crit", 1)

            elif key.endswith("_percent"):
                stat_code = key.replace("_percent", "").upper()
                current_val = base_stats_dict.get(stat_code, 10)
                bonus = current_val * float(val)
                if bonus > 0:
                    add_buff(stat_code, bonus)

            elif key == "status_immunity":
                for status in val:
                    add_buff(f"immunity_{status}", 1)

            else:
                add_buff(key, val)

        return new_buffs
