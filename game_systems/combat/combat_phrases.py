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
        elif "Undead" in name or "Skeleton" in name or "Zombie" in name:
            phrases = [
                f"A {name} shambles forward, bones rattling with ancient hatred.",
                f"The grave soil shifts, revealing a {name}.",
                f"A hollow groan echoes as a {name} lurches toward you.",
                f"Death itself seems to cling to the {name} approaching you.",
            ]
        else:
            phrases = [
                f"The air chills as a {name} emerges from the shadows.",
                f"A rustle in the undergrowth reveals a {name}, intent on violence.",
                f"From the gloom, a {name} steps forward.",
                f"A {name} materializes, eyes cold and unfeeling.",
                f"Something stirs in the dark—a {name} reveals itself.",
                f"The silence is broken by the approach of a {name}.",
            ]

        return f"**{random.choice(phrases)}**"

    @staticmethod
    def player_attack(
        player, monster: dict, damage: int, is_crit: bool, player_class_id: int
    ) -> str:
        m_name = str(monster.get("name", "the enemy"))

        # Helper to format damage
        def fmt(dmg, crit):
            base = f"`{dmg}` damage"
            return f"{base} **(CRITICAL!)**" if crit else base

        d_str = fmt(damage, is_crit)

        # --- WARRIOR (ID 1) ---
        if player_class_id == 1:
            if is_crit:
                pool = [
                    f"You put your entire weight behind the swing, shattering the {m_name}'s defense! {d_str}",
                    f"A thunderous impact! Your weapon crushes into the {m_name}. {d_str}",
                    f"You roar with effort, cleaving deep into the {m_name}'s flesh! {d_str}",
                ]
            else:
                pool = [
                    f"You cleave into the {m_name}, steel ringing against bone. {d_str}",
                    f"A heavy blow forces the {m_name} back. {d_str}",
                    f"Your blade bites into the {m_name}'s hide. {d_str}",
                    f"You drive your shoulder into the strike, hitting the {m_name}. {d_str}",
                ]

        # --- MAGE (ID 2) ---
        elif player_class_id == 2:
            if is_crit:
                pool = [
                    f"The air screams as concentrated mana obliterates the {m_name}'s guard! {d_str}",
                    f"A blinding flash! Your spell consumes the {m_name} in raw power. {d_str}",
                    f"You unravel the {m_name}'s very essence with a surge of arcane force! {d_str}",
                ]
            else:
                pool = [
                    f"Arcane energy hammers the {m_name}. {d_str}",
                    f"A raw bolt of mana sears the {m_name}'s skin. {d_str}",
                    f"You conjure a burst of power, scorching the {m_name}. {d_str}",
                    f"The weave responds to your call, striking the {m_name}. {d_str}",
                ]

        # --- ROGUE (ID 3) ---
        elif player_class_id == 3:
            if is_crit:
                pool = [
                    f"Perfect execution! Your blade finds a vital artery on the {m_name}. {d_str}",
                    f"You vanish for a heartbeat, reappearing as your dagger sinks deep. {d_str}",
                    f"A spray of blood marks your precision strike on the {m_name}! {d_str}",
                ]
            else:
                pool = [
                    f"You slip through an opening, cutting the {m_name}. {d_str}",
                    f"A silent, surgical strike lands true on the {m_name}. {d_str}",
                    f"A rapid feint leaves the {m_name} exposed to your blade. {d_str}",
                    f"You find a gap in the {m_name}'s armor. {d_str}",
                ]

        # --- CLERIC (ID 4) ---
        elif player_class_id == 4:
            if is_crit:
                pool = [
                    f"Divine judgment descends! The {m_name} reels from the holy impact. {d_str}",
                    f"Your weapon glows with blinding light, smiting the {m_name} where it stands! {d_str}",
                    f"Faith guides your hand into a devastating blow against the {m_name}! {d_str}",
                ]
            else:
                pool = [
                    f"You strike the {m_name} with righteous fury. {d_str}",
                    f"Your weapon descends like judgment upon the {m_name}. {d_str}",
                    f"A flash of holy light accompanies your blow against the {m_name}. {d_str}",
                    f"You batter the {m_name} with the weight of your conviction. {d_str}",
                ]

        # --- RANGER (ID 5) ---
        elif player_class_id == 5:
            if is_crit:
                pool = [
                    f"A perfect shot! Your arrow pierces the {m_name}'s eye! {d_str}",
                    f"You loose the shaft before the {m_name} can blink—dead center! {d_str}",
                    f"The wind guides your aim into a lethal strike on the {m_name}! {d_str}",
                ]
            else:
                pool = [
                    f"Your arrow thuds into the {m_name}. {d_str}",
                    f"A well-placed shot strikes the {m_name}. {d_str}",
                    f"Your bow sings—the {m_name} recoils from the hit. {d_str}",
                    f"You loose an arrow, catching the {m_name} in the flank. {d_str}",
                ]

        # --- DEFAULT ---
        else:
            if is_crit:
                pool = [
                    f"An incredible blow! The {m_name} staggers violently. {d_str}",
                    f"You find a weakness and exploit it with brutal force! {d_str}",
                ]
            else:
                pool = [
                    f"You strike cleanly, hitting the {m_name}. {d_str}",
                    f"A decisive blow lands on the {m_name}. {d_str}",
                    f"Steel meets flesh as you hit the {m_name}. {d_str}",
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
            f"Light gathers around you as **{skill_name}** takes effect (+`{heal_amount}` HP).",
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

        # Specific Monster Types
        if "Goblin" in m_name:
            pool = [
                f"The {m_name} stabs wildly, catching you for `{damage}` damage!{crit_text}",
                f"The {m_name} lunges with a shriek, slashing for `{damage}` damage!{crit_text}",
                f"A dirty blade finds a gap in your armor— `{damage}` damage.{crit_text}",
            ]
        elif "Slime" in m_name:
            pool = [
                f"The {m_name} slams into you with heavy force for `{damage}` damage.{crit_text}",
                f"Acid splashes against your skin— `{damage}` damage!{crit_text}",
                f"The {m_name} engulfs your limb momentarily, burning for `{damage}` damage.{crit_text}",
            ]
        elif "Wolf" in m_name or "Hound" in m_name:
            pool = [
                f"The {m_name} bites down savagely for `{damage}` damage!{crit_text}",
                f"Claws rake your side, drawing blood— `{damage}` damage.{crit_text}",
                f"Hot breath precedes a tearing snap of jaws— `{damage}` damage.{crit_text}",
            ]
        elif "Spider" in m_name:
            pool = [
                f"The {m_name} sinks its fangs into you for `{damage}` damage!{crit_text}",
                f"A sharp leg pierces your defense— `{damage}` damage.{crit_text}",
                f"Venom burns as the {m_name} strikes for `{damage}` damage.{crit_text}",
            ]
        elif "Bear" in m_name:
            pool = [
                f"The {m_name} swipes with massive force, dealing `{damage}` damage!{crit_text}",
                f"You are thrown back by the {m_name}'s charge— `{damage}` damage.{crit_text}",
                f"Bone-crushing weight slams into you for `{damage}` damage.{crit_text}",
            ]
        else:
            pool = [
                f"The {m_name} strikes you for `{damage}` damage!{crit_text}",
                f"You brace too late— `{damage}` damage from the {m_name}.{crit_text}",
                f"Pain flares as the {m_name} hits you for `{damage}` damage.{crit_text}",
                f"The {m_name}'s attack connects with a sickening thud— `{damage}` damage.{crit_text}",
                f"You reel from the {m_name}'s blow— `{damage}` damage.{crit_text}",
            ]

        return random.choice(pool)

    @staticmethod
    def monster_skill(monster, player, skill_data, damage, is_crit) -> str:
        m_name = str(monster.get("name", "the creature"))
        skill_name = str(skill_data.get("name", "Special Attack"))

        phrases = [
            f"The {m_name} unleashes **{skill_name}**! It hits for `{damage}` damage!",
            f"Dark energy gathers— **{skill_name}** strikes you for `{damage}` damage!",
            f"The {m_name} channels a deadly art: **{skill_name}** deals `{damage}` damage!",
        ]
        return random.choice(phrases)

    @staticmethod
    def monster_buff(monster, buff_data) -> str:
        m_name = str(monster.get("name", "the creature"))
        phrases = [
            f"The {m_name} roars, its power swelling.",
            f"The {m_name} glows as it strengthens.",
            f"A dark aura surrounds the {m_name}.",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_victory(monster, exp, gold, leveled_up, new_level) -> str:
        m_name = str(monster.get("name", "the enemy"))

        victory_phrases = [
            f"The {m_name} collapses, the threat fading.",
            f"With a final gasp, the {m_name} falls silent.",
            f"You stand victorious over the fallen {m_name}.",
            f"The {m_name} lies defeated at your feet.",
        ]
        phrase = random.choice(victory_phrases)

        msg = f"{phrase}\nGained `{exp} EXP`"

        if leveled_up:
            msg += f"\n\n{E.LEVEL_UP} **A NEW THRESHOLD REACHED**\nYou have reached **Level {new_level}**."
        return msg

    @staticmethod
    def player_defeated(monster) -> str:
        m_name = str(monster.get("name", "the creature"))
        return f"{E.DEFEAT} Your vision blurs. The {m_name}'s final blow sends you collapsing into darkness."

    @staticmethod
    def monster_heal(monster, skill, amount) -> str:
        m_name = str(monster.get("name", "the creature"))
        skill_name = str(skill.get("name", "healing"))

        phrases = [
            f"The {m_name} uses **{skill_name}** and recovers `{amount}` HP.",
            f"A green light surrounds the {m_name} as it uses **{skill_name}** (+`{amount}` HP).",
        ]
        return random.choice(phrases)
