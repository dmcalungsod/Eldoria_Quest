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
        Returns a dict: {"type": "attack"|"skill"|"buff", "skill": {...}, "buff": {...}}
        """
        try:
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
            offensive_skills = [s for s in usable_skills if s.get("heal_power", 0) == 0]

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
                    return {"type": "skill", "skill": chosen}

            # 3. Default Attack
            return {"type": "attack"}

        except Exception:
            # Fallback to attack on any error
            return {"type": "attack"}

    @staticmethod
    def apply_buff(monster_data: dict, buff_data: dict):
        """
        Applies a buff to the monster state (Placeholder).
        """
        # Logic to modify monster stats temporarily would go here
        pass
