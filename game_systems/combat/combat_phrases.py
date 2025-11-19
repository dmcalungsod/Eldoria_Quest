"""
combat_phrases.py

Provides atmospheric narration for combat.
Hardened: Safe string formatting and robust key handling.
"""

import random
import game_systems.data.emojis as E


class CombatPhrases:
    """
    Houses all static methods for generating thematic combat narration.
    """

    @staticmethod
    def opening(monster_data: dict) -> str:
        """Generates opening line."""
        name = str(monster_data.get("name", "Unknown Entity"))

        if "Goblin" in name:
            phrases = [
                f"A chittering {name} scrambles from the rocks, its crude blade trembling.",
                f"A {name} leaps into your path, eyes gleaming with malice.",
                f"A raspy snarl rings out— a {name} emerges, grinning.",
                f"A {name} darts from the shadows, clutching its jagged weapon.",
                f"A {name} clambers over broken stone, shrieking a challenge.",
            ]
        elif "Slime" in name:
            phrases = [
                f"A {name} gurgles from the damp soil, its form quivering.",
                f"The ground shivers as a {name} slides into view.",
                f"A {name} bubbles grotesquely, advancing slowly.",
                f"Moist air thickens as a {name} rises, dripping sludge.",
            ]
        elif "Wolf" in name or "Hound" in name:
            phrases = [
                f"A {name} emerges, fangs bared and low growl rumbling.",
                f"You are being hunted— a {name} circles you.",
                f"Leaves scatter as a {name} lunges from cover.",
                f"A {name} prowls into the clearing, breath steaming.",
            ]
        elif "Spider" in name:
            phrases = [
                f"Eight legs skitter as a {name} descends from above.",
                f"A hulking {name} blocks your path, mandibles clacking.",
                f"Silk trembles overhead as a {name} lowers itself.",
                f"A {name} crawls forth, venom glistening on its fangs.",
            ]
        else:
            phrases = [
                f"The air chills as a {name} emerges from the shadows.",
                f"A rustle in the undergrowth reveals a {name}, intent on violence.",
                f"From the gloom, a {name} steps forward.",
                f"A {name} materializes, eyes cold and unfeeling.",
            ]

        return f"**{random.choice(phrases)}**"

    @staticmethod
    def player_attack(player, monster: dict, damage: int, is_crit: bool, player_class_id: int) -> str:
        m_name = str(monster.get("name", "the enemy"))
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        # MAGE
        if player_class_id == 2:
            pool = [
                f"Arcane energy hammers the {m_name} for `{damage}` damage!{crit_text}",
                f"A raw bolt of mana sears the {m_name}, dealing `{damage}` damage!{crit_text}",
                f"You conjure a burst of power against the {m_name} for `{damage}` damage.{crit_text}",
            ]
        # WARRIOR
        elif player_class_id == 1:
            pool = [
                f"You cleave into the {m_name} for `{damage}` damage!{crit_text}",
                f"A crushing blow breaks the {m_name}'s guard: `{damage}` damage.{crit_text}",
                f"Your blade bites deep into the {m_name} for `{damage}` damage!{crit_text}",
            ]
        # ROGUE
        elif player_class_id == 3:
            pool = [
                f"You slip through an opening, striking the {m_name} for `{damage}` damage!{crit_text}",
                f"A silent, surgical strike lands true— `{damage}` damage.{crit_text}",
                f"A rapid feint and thrust hits the {m_name} for `{damage}` damage.{crit_text}",
            ]
        # RANGER
        elif player_class_id == 5:
            pool = [
                f"Your arrow pierces the {m_name} for `{damage}` damage!{crit_text}",
                f"A well-placed shot strikes the {m_name} for `{damage}` damage.{crit_text}",
                f"Your bow sings— the {m_name} recoils from `{damage}` damage!{crit_text}",
            ]
        # DEFAULT
        else:
            pool = [
                f"You strike cleanly, dealing `{damage}` damage to the {m_name}.{crit_text}",
                f"A decisive blow lands on the {m_name} for `{damage}` damage.{crit_text}",
                f"Steel meets flesh— `{damage}` damage dealt to the {m_name}.{crit_text}",
            ]

        return random.choice(pool)

    @staticmethod
    def player_skill(player, monster, skill, damage, is_crit) -> str:
        m_name = str(monster.get("name", "the enemy"))
        skill_name = str(skill.get("name", "a skill"))
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        phrases = [
            f"You unleash **{skill_name}**! It crashes into the {m_name} for `{damage}` damage!{crit_text}",
            f"Focusing your strength, you invoke **{skill_name}**, striking the {m_name} for `{damage}` damage.{crit_text}",
            f"Power erupts as **{skill_name}** lands— `{damage}` damage dealt!{crit_text}",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_heal(player, skill, heal_amount) -> str:
        skill_name = str(skill.get("name", "a healing spell"))

        phrases = [
            f"You invoke **{skill_name}**. Warmth floods your body, restoring `{heal_amount}` HP.",
            f"A whispered prayer— **{skill_name}** mends your wounds for `{heal_amount}` HP.",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_buff(player, skill) -> str:
        skill_name = str(skill.get("name", "a buff"))
        
        phrases = [
            f"You channel power into **{skill_name}**, altering your state.",
            f"A moment of focus— **{skill_name}** takes hold.",
            f"Energy surrounds you as **{skill_name}** activates.",
        ]
        return f"{E.BUFF} {random.choice(phrases)}"

    @staticmethod
    def monster_attack(monster, player, damage, is_crit) -> str:
        m_name = str(monster.get("name", "the creature"))
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        if "Goblin" in m_name:
            pool = [
                f"The {m_name} stabs wildly, catching you for `{damage}` damage!{crit_text}",
                f"The {m_name} lunges, slashing for `{damage}` damage!{crit_text}",
            ]
        elif "Slime" in m_name:
            pool = [
                f"The {m_name} slams into you for `{damage}` damage.{crit_text}",
                f"Acid splashes you— `{damage}` damage!{crit_text}",
            ]
        elif "Wolf" in m_name:
            pool = [
                f"The {m_name} bites down savagely for `{damage}` damage!{crit_text}",
                f"Claws rake your side— `{damage}` damage.{crit_text}",
            ]
        else:
            pool = [
                f"The {m_name} strikes you for `{damage}` damage!{crit_text}",
                f"You brace too late— `{damage}` damage from the {m_name}.{crit_text}",
                f"Pain flares as the {m_name} hits you for `{damage}` damage.{crit_text}",
            ]
        
        return random.choice(pool)

    @staticmethod
    def monster_skill(monster, player, skill_data, damage, is_crit) -> str:
        m_name = str(monster.get("name", "the creature"))
        skill_name = str(skill_data.get("name", "Special Attack"))

        phrases = [
            f"The {m_name} unleashes **{skill_name}**! It hits for `{damage}` damage!",
            f"Dark energy gathers— **{skill_name}** strikes you for `{damage}` damage!",
        ]
        return random.choice(phrases)

    @staticmethod
    def monster_buff(monster, buff_data) -> str:
        m_name = str(monster.get("name", "the creature"))
        phrases = [
            f"The {m_name} roars, its power swelling.",
            f"The {m_name} glows as it strengthens.",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_victory(monster, exp, gold, leveled_up, new_level) -> str:
        m_name = str(monster.get("name", "the enemy"))
        phrase = f"The {m_name} collapses, the threat fading."
        
        msg = f"{phrase}\nGained `{exp} EXP`"

        if leveled_up:
            msg += (
                f"\n\n{E.LEVEL_UP} **A NEW THRESHOLD REACHED**\n"
                f"You have reached **Level {new_level}**."
            )
        return msg

    @staticmethod
    def player_defeated(monster) -> str:
        m_name = str(monster.get("name", "the creature"))
        return f"{E.DEFEAT} Your vision blurs. The {m_name}'s final blow sends you collapsing into darkness."