"""
combat_phrases.py

Provides narrative, book-like text for combat events, matching the
dark high-fantasy theme of Eldoria.

Exposes 'CombatPhrases' class for CombatEngine.
"""

import random
from game_systems.player.level_up import LevelUpSystem
import game_systems.data.emojis as E


class CombatPhrases:
    """
    Houses all static methods for generating thematic combat narration.
    """

    @staticmethod
    def opening(monster_data: dict) -> str:
        """
        Called at the start of combat.
        """
        name = monster_data.get("name", "creature")
        phrases = [
            f"The air chills as a {name} emerges from the shadows, its eyes fixed upon you.",
            f"A rustle in the undergrowth reveals a {name}, barring your path with ill intent.",
            f"From the gloom, a {name} appears, sensing the warmth of the living.",
            f"The wind stills; something hunts you. A {name} steps into view."
        ]
        return f"{E.COMBAT} **{random.choice(phrases)}**"

    @staticmethod
    def player_attack(player: LevelUpSystem, monster: dict, damage: int, is_crit: bool) -> str:
        """
        Called when the player hits the monster.
        """
        m_name = monster.get("name", "the enemy")
        crit_text = " **(CRITICAL!)**" if is_crit else ""
        
        phrases = [
            f"You drive your blade into the {m_name}, dealing `{damage}` damage!{crit_text}",
            f"A swift strike finds purchase on the {m_name}. It recoils from `{damage}` damage.{crit_text}",
            f"Your assault lands true, carving `{damage}` damage from the {m_name}.{crit_text}",
            f"Arcane energy or steel bites deep into the {m_name} for `{damage}` damage!{crit_text}"
        ]
        return f"{E.PLAYER_ATTACK} {random.choice(phrases)}"

    @staticmethod
    def monster_attack(monster: dict, player: LevelUpSystem, damage: int, is_crit: bool) -> str:
        """
        Called when the monster hits the player.
        """
        m_name = monster.get("name", "The creature")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        phrases = [
            f"The {m_name} lunges, its attack striking you for `{damage}` damage!{crit_text}",
            f"You brace as the {m_name} retaliates, inflicting `{damage}` damage.{crit_text}",
            f"The creature's blow connects, and pain flares as you take `{damage}` damage!{crit_text}",
            f"A savage strike from the {m_name} lands, dealing `{damage}` damage!{crit_text}"
        ]
        return f"{E.MONSTER_ATTACK} {random.choice(phrases)}"

    @staticmethod
    def monster_skill(monster: dict, player: LevelUpSystem, skill_data: dict, damage: int, is_crit: bool) -> str:
        """
        Called when the monster uses a special ability.
        """
        m_name = monster.get("name", "The creature")
        skill_name = skill_data.get("name", "Special Attack")
        
        phrases = [
            f"The {m_name} unleashes **{skill_name}**! The power slams into you for `{damage}` damage!",
            f"A dark energy gathers... The {m_name}'s **{skill_name}** hits you for `{damage}` damage!",
            f"**{skill_name}**! The {m_name} catches you off guard, inflicting `{damage}` damage!"
        ]
        return f"{E.MONSTER_SKILL} {random.choice(phrases)}"

    @staticmethod
    def monster_buff(monster: dict, buff_data: dict) -> str:
        """
        Called when the monster buffs itself.
        """
        m_name = monster.get("name", "The creature")
        phrases = [
            f"The {m_name} lets out a primal roar, its power swelling!",
            f"An unnatural light surrounds the {m_name} as it grows stronger!",
            f"The {m_name} focuses, its presence becoming more menacing!"
        ]
        return f"{E.BUFF} {random.choice(phrases)}"

    @staticmethod
    def player_victory(monster: dict, exp: int, gold: int, leveled_up: bool) -> str:
        """
        Called when the player wins.
        """
        m_name = monster.get("name", "the enemy")
        
        phrases = [
            f"The {m_name} falls still. Silence returns to the grove. You have prevailed.",
            f"Your final strike cleaves the creature. It is defeated.",
            f"With a final, pained cry, the {m_name} collapses. The threat is over."
        ]
        
        msg = f"{E.VICTORY} {random.choice(phrases)}\n" \
              f"{E.EXP} Gained `{exp} EXP`\n" \
              f"{E.GOLD} Found `{gold} Gold`"
              
        if leveled_up:
            msg += f"\n{E.LEVEL_UP} **LEVEL UP!** A new strength settles into your limbs."
        return msg

    @staticmethod
    def player_defeated(monster: dict) -> str:
        """
        Called when the player is defeated.
        """
        m_name = monster.get("name", "The creature")
        phrases = [
            f"Your vision blurs... the forest tilts. The {m_name}'s blow was too much. Darkness claims you.",
            f"Strength fails you. As you fall to your knees, the {m_name} looms... You have been defeated.",
            f"You cannot withstand the assault. Your consciousness fades as the {m_name} stands victorious."
        ]
        return f"{E.DEFEAT} {random.choice(phrases)}"