"""
monster_actions.py

Simple AI for monster combat turns.
Hardened: Safe random rolls and default fallback actions.
"""

import random


class MonsterAI:
    @staticmethod
    def choose_action(monster_data: dict, current_hp: int, current_mp: int) -> dict:
        """
        Decides the monster's next move.
        Returns a dict: {"type": "attack"|"skill"|"buff"|"telegraph"|"execute_charge", ...}
        """
        try:
            # 0. Check for Charged Skill (Priority 1)
            if "charged_skill" in monster_data:
                return {"type": "execute_charge", "skill": monster_data["charged_skill"]}

            skills = monster_data.get("skills", [])
            max_hp = monster_data.get("max_hp", 100)

            # Filter skills by MP cost
            usable_skills = [s for s in skills if s.get("mp_cost", 0) <= current_mp]

            # 1. Healing Logic (Priority)
            # If HP is below 40%, try to heal
            if current_hp < max_hp * 0.4:
                heal_skills = [s for s in usable_skills if s.get("heal_power", 0) > 0]
                if heal_skills:
                    # 70% chance to heal if critical
                    if random.randint(1, 100) <= 70:
                        chosen = random.choice(heal_skills)
                        return {"type": "skill", "skill": chosen}

            # 2. Offensive Skill Logic
            offensive_skills = [s for s in usable_skills if s.get("heal_power", 0) == 0 and not s.get("buff_data")]

            if offensive_skills:
                # Base chance to use skill over normal attack
                skill_chance = 30

                # Increase chance for stronger monsters
                tier = monster_data.get("tier", "Normal")
                if tier == "Elite":
                    skill_chance = 50
                elif tier == "Boss":
                    skill_chance = 70

                if random.randint(1, 100) <= skill_chance:
                    chosen = random.choice(offensive_skills)

                    # --- TELEGRAPH LOGIC ---
                    # High power skills (>= 1.5) have a chance to be telegraphed.
                    # Ultra-Heavy attacks (>= 2.0) are ALWAYS telegraphed to allow counterplay.
                    power = float(chosen.get("power", 1.0))

                    if power >= 2.0:
                        return {"type": "telegraph", "skill": chosen}

                    if power >= 1.5 and random.randint(1, 100) <= 50:
                        return {"type": "telegraph", "skill": chosen}

                    return {"type": "skill", "skill": chosen}

            # 3. Buff Logic
            buff_skills = [s for s in usable_skills if s.get("buff_data")]
            if buff_skills:
                # 25% chance to use a buff if available
                if random.randint(1, 100) <= 25:
                    chosen = random.choice(buff_skills)
                    return {"type": "buff", "buff": chosen}

            # 4. Default Attack
            return {"type": "attack"}

        except Exception:
            # Fallback to attack on any error
            return {"type": "attack"}

    @staticmethod
    def apply_buff(monster_data: dict, buff_skill: dict):
        """
        Applies a buff to the monster state.
        buff_skill contains "buff_data" with:
        {
            "stat": "ATK"|"DEF",
            "multiplier": float,
            "duration": int
        }
        """
        buff_data = buff_skill.get("buff_data", {})
        if not buff_data:
            return

        if "buffs" not in monster_data:
            monster_data["buffs"] = []

        stat = buff_data.get("stat")
        multiplier = float(buff_data.get("multiplier", 1.0))
        duration = int(buff_data.get("duration", 3))

        # Calculate increase
        current_val = monster_data.get(stat, 0)
        new_val = int(current_val * multiplier)
        increase = new_val - current_val

        # Apply
        monster_data[stat] = new_val

        # Record
        buff_record = {
            "stat": stat,
            "increase": increase,
            "duration": duration,
            "name": buff_skill.get("name", "Unknown Buff"),
        }
        monster_data["buffs"].append(buff_record)

    @staticmethod
    def handle_buffs(monster_data: dict) -> list[str]:
        """
        Decrements buff duration and reverts expired buffs.
        Returns a list of expiration messages.
        """
        expired_msgs = []
        if "buffs" not in monster_data:
            return expired_msgs

        active_buffs = []
        for buff in monster_data["buffs"]:
            buff["duration"] -= 1
            if buff["duration"] <= 0:
                # Revert
                stat = buff["stat"]
                increase = buff["increase"]
                monster_data[stat] = max(0, monster_data.get(stat, 0) - increase)
                expired_msgs.append(f"{monster_data.get('name', 'Monster')}'s {buff['name']} wore off.")
            else:
                active_buffs.append(buff)

        monster_data["buffs"] = active_buffs
        return expired_msgs
