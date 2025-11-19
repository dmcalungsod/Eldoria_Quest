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
        # Basic logic:
        # 70% Attack
        # 30% Skill (if MP allows - Placeholder logic)

        try:
            roll = random.randint(1, 100)

            # Placeholder for future skill logic
            # For now, mostly normal attacks unless specific boss AI added
            if roll > 80:
                # Example skill structure
                return {
                    "type": "skill",
                    "skill": {"name": "Heavy Blow", "power": 1.5, "mp_cost": 5, "desc_key": "special_hit"},
                }

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
