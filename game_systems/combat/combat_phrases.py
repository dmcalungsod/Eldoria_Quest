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
        Provides monster-specific opening lines.
        """
        name = monster_data.get("name", "creature")
        phrases = []

        if "Goblin" in name:
            phrases = [
                f"A chittering {name} scrambles from the rocks, its crude blade thirsty.",
                f"You hear a harsh cry as a {name} leaps into your path, its eyes wide with malice.",
                f"A raspy snarl echoes— a {name} emerges, grinning through rotten teeth.",
                f"A {name} darts from the shadows, clutching its jagged weapon with manic glee.",
                f"The stench of filth precedes a lurking {name}, eager for plunder and blood.",
                f"A {name} clambers over broken stones, shrieking a challenge only it understands.",
            ]
        elif "Slime" in name:
            phrases = [
                f"A {name} gurgles and oozes from the damp earth, its form quivering.",
                f"The ground trembles slightly as a {name} slides into view, sensing your warmth.",
                f"A sickening squelch announces a {name} dragging itself toward you.",
                f"A {name} bubbles grotesquely, stretching its formless body as it advances.",
                f"Moist air thickens around you as a {name} rises, dripping acidic slime.",
                f"A {name} pulses unnaturally, its gelatinous mass wobbling with hunger.",
            ]
        elif "Wolf" in name or "Hound" in name:
            phrases = [
                f"A low growl echoes from the thicket. A {name} emerges, its fangs bared.",
                f"You are being hunted. A {name} circles you, its eyes locked on yours.",
                f"Leaves scatter as a {name} lunges from cover, fur bristling.",
                f"A {name} prowls into the clearing, breath steaming with animal fury.",
                f"The forest falls silent before a {name} steps forth, announcing its hunt.",
                f"A {name} stalks low, muscles coiled, ready to pounce the moment you falter.",
            ]
        elif "Spider" in name:
            phrases = [
                f"Eight legs skitter on dry leaves as a {name} descends from the canopy.",
                f"A large {name} bars your path, its mandibles clicking.",
                f"Silk trembles overhead as a {name} lowers itself toward you.",
                f"A {name} crawls forth, each step tapping like a drum of dread.",
                f"The underbrush shifts— a {name} emerges, venom glistening on its fangs.",
                f"A {name} rears back, preparing to strike with unnatural speed.",
            ]
        else:
            # Fallback for other monsters
            phrases = [
                f"The air chills as a {name} emerges from the shadows, its eyes fixed upon you.",
                f"A rustle in the undergrowth reveals a {name}, barring your path with ill intent.",
                f"From the gloom, a {name} appears, sensing the warmth of the living.",
                f"An eerie hush settles as a {name} approaches with predatory calm.",
                f"A {name} materializes from drifting mist, gaze cold and unfeeling.",
                f"The world seems to darken as a {name} steps into your fate-bound path.",
            ]

        return f"**{random.choice(phrases)}**"

    @staticmethod
    def player_attack(
        player: LevelUpSystem, monster: dict, damage: int, is_crit: bool
    ) -> str:
        """
        Called when the player hits the monster.
        Uses stat-based inference for class-specific phrases.
        """
        m_name = monster.get("name", "the enemy")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        stats = player.stats
        s = stats.strength
        d_a = stats.dexterity + stats.agility
        m = stats.magic

        # MAGE
        mage = [
            f"Arcane energy crackles and slams into the {m_name} for `{damage}` damage!{crit_text}",
            f"A bolt of raw magic sears the {m_name}, dealing `{damage}` damage!{crit_text}",
            f"You conjure a blast of power, striking the {m_name} for `{damage}` damage.{crit_text}",
            f"Mystic sigils flare as your spell detonates against the {m_name} for `{damage}` damage!{crit_text}",
            f"Your hands surge with mana, unleashing a burst that scorches the {m_name} for `{damage}` damage.{crit_text}",
            f"A ripple of arcane force warps the air, smashing the {m_name} for `{damage}` damage!{crit_text}",
        ]

        # WARRIOR
        warrior = [
            f"You cleave into the {m_name} with brutal force, dealing `{damage}` damage!{crit_text}",
            f"A heavy blow shatters the {m_name}'s guard, inflicting `{damage}` damage.{crit_text}",
            f"Your blade finds purchase, a powerful strike for `{damage}` damage!{crit_text}",
            f"You drive your weight behind the swing, crushing the {m_name} for `{damage}` damage!{crit_text}",
            f"Steel sings as your strike tears through the {m_name}, dealing `{damage}` damage.{crit_text}",
            f"A brutal overhead attack slams into the {m_name}, delivering `{damage}` damage!{crit_text}",
        ]

        # ROGUE / RANGER
        rogue = [
            f"You find an opening, striking the {m_name} with precision for `{damage}` damage!{crit_text}",
            f"A swift, silent strike hits a vital point on the {m_name} for `{damage}` damage.{crit_text}",
            f"Your arrow finds its mark, piercing the {m_name} for `{damage}` damage!{crit_text}",
            f"You slip past its guard and deliver `{damage}` damage in a clean, effortless motion.{crit_text}",
            f"A flicker of movement— your attack lands before the {m_name} even reacts, `{damage}` damage dealt.{crit_text}",
            f"Your blades dance, carving `{damage}` damage from the {m_name} with practiced grace.{crit_text}",
        ]

        # HYBRID (Cleric, etc.)
        hybrid = [
            f"You drive your weapon into the {m_name}, dealing `{damage}` damage!{crit_text}",
            f"Your assault lands true, carving `{damage}` damage from the {m_name}.{crit_text}",
            f"A well-aimed strike connects with the {m_name} for `{damage}` damage.{crit_text}",
            f"You channel instinct and training, striking the {m_name} for `{damage}` damage.{crit_text}",
            f"Your attack flows naturally, landing `{damage}` damage on the {m_name}.{crit_text}",
            f"A decisive blow hits the {m_name}, dealing `{damage}` damage!{crit_text}",
        ]

        if m >= s and m >= d_a:
            pool = mage
        elif s > m and s > d_a:
            pool = warrior
        elif d_a > s and d_a > m:
            pool = rogue
        else:
            pool = hybrid

        return random.choice(pool)

    # --- NEW METHOD ---
    @staticmethod
    def player_skill(
        player: LevelUpSystem, monster: dict, skill: dict, damage: int, is_crit: bool
    ) -> str:
        """
        Called when the player uses an offensive skill.
        """
        m_name = monster.get("name", "the enemy")
        skill_name = skill.get("name", "a skill")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        phrases = [
            f"You unleash **{skill_name}**! It slams into the {m_name} for `{damage}` damage!{crit_text}",
            f"Focusing your power, you cast **{skill_name}**, dealing `{damage}` damage to the {m_name}.{crit_text}",
            f"A brilliant flash erupts as **{skill_name}** strikes the {m_name} for `{damage}` damage!{crit_text}",
        ]
        return f"{random.choice(phrases)}"

    # --- NEW METHOD ---
    @staticmethod
    def player_heal(player: LevelUpSystem, skill: dict, heal_amount: int) -> str:
        """
        Called when the player uses a healing skill.
        """
        skill_name = skill.get("name", "a healing spell")

        phrases = [
            f"You invoke **{skill_name}**! A warm light washes over you, restoring `{heal_amount}` HP.",
            f"A gentle prayer... **{skill_name}** mends your wounds for `{heal_amount}` HP.",
            f"Calling upon **{skill_name}**, you feel vitality return, healing `{heal_amount}` HP.",
        ]
        return f"{random.choice(phrases)}"

    @staticmethod
    def monster_attack(
        monster: dict, player: LevelUpSystem, damage: int, is_crit: bool
    ) -> str:
        """
        Called when the monster hits the player.
        Provides monster-specific attack lines.
        """
        m_name = monster.get("name", "The creature")
        crit_text = " **(CRITICAL!)**" if is_crit else ""
        pool = []

        goblin = [
            f"The {m_name} stabs wildly with its crude weapon, catching you for `{damage}` damage!{crit_text}",
            f"A savage, clumsy blow from the {m_name} lands, dealing `{damage}` damage.{crit_text}",
            f"The {m_name} lunges with reckless glee, cutting you for `{damage}` damage!{crit_text}",
            f"A shrill cry accompanies the {m_name}'s strike— `{damage}` damage dealt.{crit_text}",
            f"The {m_name} slashes in desperation, still landing `{damage}` damage.{crit_text}",
            f"Cackling, the {m_name} digs its jagged blade into you for `{damage}` damage!{crit_text}",
        ]

        slime = [
            f"The {m_name} slams its gelatinous body into you, inflicting `{damage}` damage.{crit_text}",
            f"A caustic glob from the {m_name} strikes you for `{damage}` damage!{crit_text}",
            f"The {m_name} envelops your leg briefly, dissolving flesh for `{damage}` damage!{crit_text}",
            f"A splash of acidic slime burns you for `{damage}` damage.{crit_text}",
            f"The {m_name} lashes out in a rippling wave, dealing `{damage}` damage.{crit_text}",
            f"A corrosive tendril whips from the {m_name}, inflicting `{damage}` damage!{crit_text}",
        ]

        wolf = [
            f"The {m_name} lunges, its fangs tearing at you for `{damage}` damage!{crit_text}",
            f"A swift pounce from the {m_name} connects, dealing `{damage}` damage.{crit_text}",
            f"The {m_name} bites down hard, ripping `{damage}` damage from you!{crit_text}",
            f"A vicious rake of claws from the {m_name} deals `{damage}` damage.{crit_text}",
            f"The {m_name} circles before striking your flank— `{damage}` damage taken.{crit_text}",
            f"A thunderous tackle from the {m_name} knocks breath from your lungs for `{damage}` damage!{crit_text}",
        ]

        spider = [
            f"The {m_name} sinks its fangs into you, inflicting `{damage}` damage!{crit_text}",
            f"A venomous spit from the {m_name} hits you for `{damage}` damage.{crit_text}",
            f"The {m_name} scuttles forward, its bite dealing `{damage}` damage!{crit_text}",
            f"Eight legs blur as the {m_name} strikes, landing `{damage}` damage.{crit_text}",
            f"A sticky web from the {m_name} hits you, followed by a quick bite for `{damage}` damage.",
            f"The {m_name}'s attack is unnervingly fast, dealing `{damage}` damage!{crit_text}",
        ]

        generic = [
            f"The {m_name} lunges, its attack striking you for `{damage}` damage!{crit_text}",
            f"You brace as the {m_name} retaliates, inflicting `{damage}` damage.{crit_text}",
            f"The creature's blow connects, and pain flares as you take `{damage}` damage!{crit_text}",
            f"A savage strike from the {m_name} lands, dealing `{damage}` damage!{crit_text}",
            f"The {m_name}'s assault is relentless, landing a blow for `{damage}` damage.",
            f"Pain lances through you as the {m_name} finds a gap in your defense for `{damage}` damage!{crit_text}",
        ]

        if "Goblin" in m_name:
            pool = goblin
        elif "Slime" in m_name:
            pool = slime
        elif "Wolf" in m_name or "Hound" in m_name:
            pool = wolf
        elif "Spider" in m_name:
            pool = spider
        else:
            pool = generic

        return random.choice(pool)

    @staticmethod
    def monster_skill(
        monster: dict,
        player: LevelUpSystem,
        skill_data: dict,
        damage: int,
        is_crit: bool,
    ) -> str:
        """
        Called when the monster uses a special ability.
        """
        m_name = monster.get("name", "The creature")
        skill_name = skill_data.get("name", "Special Attack")

        phrases = [
            f"The {m_name} unleashes **{skill_name}**! The power slams into you for `{damage}` damage!",
            f"A dark energy gathers... The {m_name}'s **{skill_name}** hits you for `{damage}` damage!",
            f"**{skill_name}**! The {m_name} catches you off guard, inflicting `{damage}` damage!",
        ]
        return f"{random.choice(phrases)}"

    @staticmethod
    def monster_buff(monster: dict, buff_data: dict) -> str:
        """
        Called when the monster buffs itself.
        """
        m_name = monster.get("name", "The creature")
        phrases = [
            f"The {m_name} lets out a primal roar, its power swelling!",
            f"An unnatural light surrounds the {m_name} as it grows stronger!",
            f"The {m_name} focuses, its presence becoming more menacing!",
        ]
        return f"{random.choice(phrases)}"

    @staticmethod
    def player_victory(monster: dict, exp: int, gold: int, leveled_up: bool) -> str:
        """
        Called when the player wins.
        """
        m_name = monster.get("name", "the enemy")
        phrase = ""

        if "Goblin" in m_name:
            phrase = f"The {m_name} falls, its crude blade clattering on the stones. It will threaten no one else."
        elif "Slime" in m_name:
            phrase = f"The {m_name} dissolves into a foul-smelling puddle, its core now still."
        elif "Wolf" in m_name or "Hound" in m_name:
            phrase = f"With a final whimper, the {m_name} collapses. The forest grows quiet once more."
        elif "Spider" in m_name:
            phrase = f"The {m_name} curls its legs in, defeated. The web stills."
        else:
            phrase = (
                f"With a final, pained cry, the {m_name} collapses. The threat is over."
            )

        msg = f"{phrase}\n" f"Gained `{exp} EXP`"

        if leveled_up:
            msg += (
                f"\n{E.LEVEL_UP} **LEVEL UP!** A new strength settles into your limbs."
            )
        return msg

    @staticmethod
    def player_defeated(monster: dict) -> str:
        """
        Called when the player is defeated.
        """
        m_name = monster.get("name", "The creature")
        phrase = ""

        if "Goblin" in m_name:
            phrase = f"The {m_name}'s cackling fills your ears as your vision fades... You have been defeated."
        elif "Wolf" in m_name:
            phrase = f"The {m_name}'s howl echoes as you fall. The hunt is over... and you were the prey."
        elif "Slime" in m_name:
            phrase = f"You are overwhelmed by the {m_name}, its form covering you. You have been defeated."
        elif "Spider" in m_name:
            phrase = f"Venom courses through your veins... the {m_name} watches as your strength fails. You have been defeated."
        else:
            phrase = f"Your vision blurs... the forest tilts. The {m_name}'s blow was too much. Darkness claims you."

        return f"{E.DEFEAT} {phrase}"
