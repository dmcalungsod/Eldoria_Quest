"""
combat_phrases.py

Provides atmospheric, book-like narration for combat events,
aligned with the dark high-fantasy tone of Eldoria.

Exposes the 'CombatPhrases' class for use within CombatEngine.
"""

import random

import game_systems.data.emojis as E
from game_systems.player.level_up import LevelUpSystem


class CombatPhrases:
    """
    Houses all static methods for generating thematic combat narration.
    """

    # ---------------------------------------------------------
    # OPENING LINES
    # ---------------------------------------------------------
    @staticmethod
    def opening(monster_data: dict) -> str:
        """
        Called at the start of combat.
        Provides monster-specific atmospheric introductions.
        """
        name = monster_data.get("name", "creature")

        if "Goblin" in name:
            phrases = [
                f"A chittering {name} scrambles from the rocks, its crude blade trembling with bloodlust.",
                f"A harsh cry echoes as a {name} leaps into your path, eyes gleaming with malice.",
                f"A raspy snarl rings out— a {name} emerges, grinning through rotten teeth.",
                f"A {name} darts from the shadows, clutching its jagged weapon with manic zeal.",
                f"A foul stench precedes a lurking {name}, eager for plunder and bloodshed.",
                f"A {name} clambers over broken stone, shrieking a challenge only it understands.",
            ]

        elif "Slime" in name:
            phrases = [
                f"A {name} gurgles and oozes from the damp soil, its form quivering hungrily.",
                f"The ground shivers as a {name} slides into view, drawn to your warmth.",
                f"A sickening squelch announces a {name} dragging itself toward you.",
                f"A {name} bubbles grotesquely, stretching its formless body as it advances.",
                f"Moist air thickens as a {name} rises, dripping acidic sludge.",
                f"A {name} pulses unnaturally, its gelatinous mass wobbling with hunger.",
            ]

        elif "Wolf" in name or "Hound" in name:
            phrases = [
                f"A low growl seeps from the thicket. A {name} emerges, fangs bared.",
                f"You are being hunted— a {name} circles you, eyes locked on your movements.",
                f"Leaves scatter as a {name} lunges from cover, fur bristling.",
                f"A {name} prowls into the clearing, breath steaming with animal fury.",
                f"The forest falls silent as a {name} steps forth, announcing its hunt.",
                f"A {name} stalks low, muscles coiled, ready to pounce the moment you falter.",
            ]

        elif "Spider" in name:
            phrases = [
                f"Eight legs skitter across dry leaves as a {name} descends from the canopy.",
                f"A hulking {name} blocks your path, mandibles clacking rhythmically.",
                f"Silk trembles overhead as a {name} lowers itself toward you.",
                f"A {name} crawls forth, each tap of its legs a drumbeat of dread.",
                f"The underbrush stirs— a {name} emerges, venom glistening on its fangs.",
                f"A {name} rears back, preparing to strike with unnatural speed.",
            ]

        else:
            phrases = [
                f"The air chills as a {name} emerges from the shadows, its gaze fixed upon you.",
                f"A rustle in the undergrowth reveals a {name}, intent on violence.",
                f"From the gloom, a {name} steps forward, sensing the warmth of the living.",
                f"An eerie hush settles as a {name} approaches with predatory calm.",
                f"A {name} materializes from drifting mist, eyes cold and unfeeling.",
                f"The world seems to darken as a {name} enters your fate-bound path.",
            ]

        return f"**{random.choice(phrases)}**"

    # ---------------------------------------------------------
    # PLAYER ATTACK
    # ---------------------------------------------------------
    @staticmethod
    def player_attack(
        player: LevelUpSystem,
        monster: dict,
        damage: int,
        is_crit: bool,
        player_class_id: int,
    ) -> str:
        """
        Called when the player strikes the monster.
        Class-specific narration based on CLASS ID.
        """
        m_name = monster.get("name", "the enemy")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        # MAGE — Class 2
        mage = [
            f"Arcane energy crackles forth, hammering the {m_name} for `{damage}` damage!{crit_text}",
            f"A raw bolt of mana sears the {m_name}, dealing `{damage}` damage!{crit_text}",
            f"You conjure a burst of power, striking the {m_name} for `{damage}` damage.{crit_text}",
            f"Mystic sigils flare as your spell detonates, dealing `{damage}` damage!{crit_text}",
            f"Mana surges through your hands, unleashing a scorching blast for `{damage}` damage.{crit_text}",
            f"The air warps as arcane force smashes into the {m_name} for `{damage}` damage!{crit_text}",
        ]

        # WARRIOR — Class 1
        warrior = [
            f"You cleave into the {m_name} with brutal force, dealing `{damage}` damage!{crit_text}",
            f"A crushing blow breaks the {m_name}'s guard, inflicting `{damage}` damage.{crit_text}",
            f"Your blade bites deep, a powerful strike for `{damage}` damage!{crit_text}",
            f"You drive your weight into the swing, smashing the {m_name} for `{damage}` damage!{crit_text}",
            f"Steel sings as your strike tears through the {m_name}, dealing `{damage}` damage.{crit_text}",
            f"A brutal overhead chop crashes down for `{damage}` damage!{crit_text}",
        ]

        # ROGUE — Class 3
        rogue = [
            f"You slip through an opening, striking the {m_name} with precision for `{damage}` damage!{crit_text}",
            f"A silent, surgical strike lands true— `{damage}` damage dealt.{crit_text}",
            f"You weave past its guard, delivering `{damage}` damage in a swift motion.{crit_text}",
            f"A flicker of movement— your blades hit before the {m_name} can react. `{damage}` damage.{crit_text}",
            f"Your daggers dance, carving `{damage}` damage with practiced grace.{crit_text}",
            f"A rapid feint and thrust lands `{damage}` damage!{crit_text}",
        ]

        # RANGER — Class 5
        ranger = [
            f"Your arrow finds its mark, piercing the {m_name} for `{damage}` damage!{crit_text}",
            f"A well-placed shot whistles from the shadows, striking for `{damage}` damage.{crit_text}",
            f"You loose an arrow that flies true, dealing `{damage}` damage.{crit_text}",
            f"Your bow sings— the {m_name} recoils from `{damage}` damage!{crit_text}",
        ]

        # Default — Cleric / Hybrids
        hybrid = [
            f"You strike cleanly, dealing `{damage}` damage to the {m_name}.{crit_text}",
            f"A decisive blow lands for `{damage}` damage.{crit_text}",
            f"You channel instinct and training, carving `{damage}` damage from the {m_name}.{crit_text}",
            f"A firm strike connects, delivering `{damage}` damage.{crit_text}",
            f"Steel meets flesh— `{damage}` damage dealt.{crit_text}",
        ]

        # Class selection
        if player_class_id == 1:
            pool = warrior
        elif player_class_id == 2:
            pool = mage
        elif player_class_id == 3:
            pool = rogue
        elif player_class_id == 5:
            pool = ranger
        else:
            pool = hybrid

        return random.choice(pool)

    # ---------------------------------------------------------
    # PLAYER SKILL
    # ---------------------------------------------------------
    @staticmethod
    def player_skill(player, monster, skill, damage, is_crit) -> str:
        m_name = monster.get("name", "the enemy")
        skill_name = skill.get("name", "a skill")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        phrases = [
            f"You unleash **{skill_name}**! It crashes into the {m_name} for `{damage}` damage!{crit_text}",
            f"Focusing your strength, you invoke **{skill_name}**, striking for `{damage}` damage.{crit_text}",
            f"Power erupts as **{skill_name}** lands— `{damage}` damage dealt!{crit_text}",
        ]
        return random.choice(phrases)

    # ---------------------------------------------------------
    # PLAYER HEAL
    # ---------------------------------------------------------
    @staticmethod
    def player_heal(player, skill, heal_amount) -> str:
        skill_name = skill.get("name", "a healing spell")

        phrases = [
            f"You invoke **{skill_name}**. Warmth floods your body, restoring `{heal_amount}` HP.",
            f"A whispered prayer— **{skill_name}** mends your wounds for `{heal_amount}` HP.",
            f"Vitality surges through you as **{skill_name}** restores `{heal_amount}` HP.",
        ]
        return random.choice(phrases)

    # ---------------------------------------------------------
    # PLAYER BUFF
    # ---------------------------------------------------------
    @staticmethod
    def player_buff(player, skill) -> str:
        skill_name = skill.get("name", "a buff spell")

        if skill.get("key_id") == "mana_shield":
            phrases = [
                "You focus, forming the **Mana Shield**— damage will drain MP instead of flesh.",
                "Arcane will surrounds you, crystallizing into the **Mana Shield**.",
                "Mystic energy swirls outward— **Mana Shield** activated.",
            ]
        elif skill.get("key_id") == "endure":
            phrases = [
                "You brace yourself— **Endure** hardens your resolve.",
                "Your stance settles; **Endure** transforms you into an unmoving bulwark.",
            ]
        elif skill.get("key_id") == "blessing":
            phrases = [
                "A divine radiance settles upon you— **Blessing** granted.",
                "An ancient whisper answers your call; **Blessing** strengthens your spirit.",
            ]
        else:
            phrases = [
                f"You channel power into **{skill_name}**, altering your state.",
                f"A moment of focus— **{skill_name}** takes hold.",
            ]

        return f"{E.BUFF} {random.choice(phrases)}"

    # ---------------------------------------------------------
    # MONSTER ATTACK
    # ---------------------------------------------------------
    @staticmethod
    def monster_attack(monster, player, damage, is_crit) -> str:
        m_name = monster.get("name", "the creature")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        if "Goblin" in m_name:
            pool = [
                f"The {m_name} stabs wildly, catching you for `{damage}` damage!{crit_text}",
                f"A clumsy yet vicious blow lands— `{damage}` damage dealt.{crit_text}",
                f"The {m_name} lunges with manic glee, slashing for `{damage}` damage!{crit_text}",
                f"A shrill cry accompanies its strike— `{damage}` damage.{crit_text}",
                f"The {m_name} hacks desperately, still managing `{damage}` damage.{crit_text}",
                f"Cackling, it digs its jagged blade into you— `{damage}` damage!{crit_text}",
            ]

        elif "Slime" in m_name:
            pool = [
                f"The {m_name} slams into you, inflicting `{damage}` damage.{crit_text}",
                f"A caustic glob splashes against you— `{damage}` damage!{crit_text}",
                f"The {m_name} envelops your leg briefly, dissolving skin for `{damage}` damage!{crit_text}",
                f"Acid burns your flesh— `{damage}` damage.{crit_text}",
                f"A rippling tendril lashes out, striking for `{damage}` damage.{crit_text}",
                f"A corrosive whip of slime hits you— `{damage}` damage!{crit_text}",
            ]

        elif "Wolf" in m_name or "Hound" in m_name:
            pool = [
                f"The {m_name} lunges, fangs tearing into you for `{damage}` damage!{crit_text}",
                f"A swift pounce collides with your chest— `{damage}` damage.{crit_text}",
                f"The {m_name} bites down savagely, ripping `{damage}` damage!{crit_text}",
                f"Claws rake your side— `{damage}` damage dealt.{crit_text}",
                f"The {m_name} circles, then strikes your flank for `{damage}` damage.{crit_text}",
                f"A crushing tackle sends you staggering— `{damage}` damage!{crit_text}",
            ]

        elif "Spider" in m_name:
            pool = [
                f"The {m_name} sinks its fangs into you— `{damage}` damage!{crit_text}",
                f"A jet of venom spatters your skin for `{damage}` damage.{crit_text}",
                f"The {m_name} darts forward, striking for `{damage}` damage!{crit_text}",
                f"Eight legs blur as it lashes out— `{damage}` damage.{crit_text}",
                f"A sticky web ensnares you before a bite lands— `{damage}` damage.",
                f"The {m_name} strikes with eerie speed, dealing `{damage}` damage!{crit_text}",
            ]

        else:
            pool = [
                f"The {m_name} lunges, striking you for `{damage}` damage!{crit_text}",
                f"You brace too late— `{damage}` damage crashes into you.{crit_text}",
                f"Pain flares as the {m_name}'s attack lands— `{damage}` damage!{crit_text}",
                f"A savage blow connects, dealing `{damage}` damage.{crit_text}",
                f"The assault is relentless— `{damage}` damage taken.",
                f"A well-timed strike pierces your defense— `{damage}` damage!{crit_text}",
            ]

        return random.choice(pool)

    # ---------------------------------------------------------
    # MONSTER SKILL
    # ---------------------------------------------------------
    @staticmethod
    def monster_skill(monster, player, skill_data, damage, is_crit) -> str:
        m_name = monster.get("name", "the creature")
        skill_name = skill_data.get("name", "Special Attack")

        phrases = [
            f"The {m_name} unleashes **{skill_name}**! It crashes into you for `{damage}` damage!",
            f"Dark energy gathers— **{skill_name}** strikes for `{damage}` damage!",
            f"The {m_name} releases **{skill_name}**, catching you off-guard for `{damage}` damage!",
        ]
        return random.choice(phrases)

    # ---------------------------------------------------------
    # MONSTER BUFF
    # ---------------------------------------------------------
    @staticmethod
    def monster_buff(monster, buff_data) -> str:
        m_name = monster.get("name", "the creature")

        phrases = [
            f"The {m_name} releases a primal roar— its power swells.",
            f"An unnatural glow envelops the {m_name} as it strengthens.",
            f"The {m_name} focuses, its presence growing increasingly menacing.",
        ]
        return random.choice(phrases)

    # ---------------------------------------------------------
    # PLAYER VICTORY
    # ---------------------------------------------------------
    @staticmethod
    def player_victory(monster, exp, gold, leveled_up, new_level) -> str:
        m_name = monster.get("name", "the enemy")

        if "Goblin" in m_name:
            phrase = f"The {m_name} collapses, its crude weapon clattering lifelessly to the stone."
        elif "Slime" in m_name:
            phrase = f"The {m_name} dissolves into a foul, motionless puddle."
        elif "Wolf" in m_name or "Hound" in m_name:
            phrase = f"With a final whimper, the {m_name} falls. The forest exhales a quiet hush."
        elif "Spider" in m_name:
            phrase = f"The {m_name} curls inward, its legs folding as the web stills."
        else:
            phrase = f"With a final, strangled cry, the {m_name} collapses. The threat fades."

        msg = f"{phrase}\nGained `{exp} EXP`"

        if leveled_up:
            msg += (
                f"\n\n{E.LEVEL_UP} **A NEW THRESHOLD REACHED**"
                f"\nThrough struggle and blood, your spirit carves a new truth."
                f"\nYou have reached **Level {new_level}**."
            )

        return msg

    # ---------------------------------------------------------
    # PLAYER DEFEATED
    # ---------------------------------------------------------
    @staticmethod
    def player_defeated(monster) -> str:
        m_name = monster.get("name", "the creature")

        if "Goblin" in m_name:
            phrase = f"Cackling echoes in your fading vision… The {m_name} stands triumphant."
        elif "Wolf" in m_name:
            phrase = "A chilling howl rises as you fall— the hunt ends, and you were the prey."
        elif "Slime" in m_name:
            phrase = f"The {m_name} engulfs you, its acidic form smothering the last of your strength."
        elif "Spider" in m_name:
            phrase = f"Venom floods your veins… The {m_name} watches as darkness overtakes you."
        else:
            phrase = f"Your vision blurs. The {m_name}'s final blow sends you collapsing into darkness."

        return f"{E.DEFEAT} {phrase}"
