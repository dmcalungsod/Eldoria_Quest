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

    # --- MONSTER OPENING PHRASES ---
    OPENING_PHRASES = {
        "Goblin": [
            "A chittering {name} scrambles from the rocks, its crude blade trembling.",
            "A {name} leaps into your path, eyes gleaming with malice.",
            "A raspy snarl rings out— a {name} emerges, grinning.",
            "A {name} darts from the shadows, clutching its jagged weapon.",
            "A {name} clambers over broken stone, shrieking a challenge.",
            "The stench of unwashed hides precedes a {name}, stepping into the light.",
            "You hear a manic cackle as a {name} reveals itself.",
        ],
        "Slime": [
            "A {name} gurgles from the damp soil, its form quivering.",
            "The ground shivers as a {name} slides into view.",
            "A {name} bubbles grotesquely, advancing slowly.",
            "Moist air thickens as a {name} rises, dripping sludge.",
            "A wet, slapping sound announces the arrival of a {name}.",
            "The earth seems to dissolve as a {name} pools into a solid form.",
        ],
        "Wolf": [
            "A {name} emerges, fangs bared and low growl rumbling.",
            "You are being hunted— a {name} circles you.",
            "Leaves scatter as a {name} lunges from cover.",
            "A {name} prowls into the clearing, breath steaming.",
            "Yellow eyes flash in the darkness—a {name} is upon you.",
            "A mournful howl cuts the air, followed by the snap of twigs as a {name} appears.",
        ],
        "Hound": [
            "A {name} emerges, fangs bared and low growl rumbling.",
            "You are being hunted— a {name} circles you.",
            "Leaves scatter as a {name} lunges from cover.",
            "A {name} prowls into the clearing, breath steaming.",
            "Yellow eyes flash in the darkness—a {name} is upon you.",
            "A mournful howl cuts the air, followed by the snap of twigs as a {name} appears.",
        ],
        "Spider": [
            "Eight legs skitter as a {name} descends from above.",
            "A hulking {name} blocks your path, mandibles clacking.",
            "Silk trembles overhead as a {name} lowers itself.",
            "A {name} crawls forth, venom glistening on its fangs.",
            "You brush against a sticky thread, and a {name} drops to investigate.",
            "Many eyes watch you from the gloom—a {name} prepares to strike.",
        ],
        "Boar": [
            "The undergrowth explodes as a {name} charges into view!",
            "A massive {name} paws the ground, preparing to trample you.",
            "Heavy hooves thunder against the earth—a {name} is attacking!",
            "Snorting with aggression, a {name} lowers its head to strike.",
            "Trees shake as a {name} crashes through the brush.",
        ],
        "Stag": [
            "The undergrowth explodes as a {name} charges into view!",
            "A massive {name} paws the ground, preparing to trample you.",
            "Heavy hooves thunder against the earth—a {name} is attacking!",
            "Snorting with aggression, a {name} lowers its head to strike.",
            "Trees shake as a {name} crashes through the brush.",
        ],
        "Brute": [
            "The undergrowth explodes as a {name} charges into view!",
            "A massive {name} paws the ground, preparing to trample you.",
            "Heavy hooves thunder against the earth—a {name} is attacking!",
            "Snorting with aggression, a {name} lowers its head to strike.",
            "Trees shake as a {name} crashes through the brush.",
        ],
        "Bear": [
            "A {name} rises on its hind legs, roaring a challenge.",
            "The ground shakes under the weight of a {name}.",
            "A massive {name} lumbers into view, eyes locked on you.",
        ],
        "Treant": [
            "A {name} creaks to life, detaching itself from the forest.",
            "Roots snap and shift as a {name} lumbers toward you.",
            "The trees themselves seem to turn against you—a {name} awakens.",
            "A {name} rises from the earth, moss and bark forming a deadly shape.",
            "Ancient wood groans as a {name} steps from the canopy.",
        ],
        "Ent": [
            "A {name} creaks to life, detaching itself from the forest.",
            "Roots snap and shift as a {name} lumbers toward you.",
            "The trees themselves seem to turn against you—a {name} awakens.",
            "A {name} rises from the earth, moss and bark forming a deadly shape.",
            "Ancient wood groans as a {name} steps from the canopy.",
        ],
        "Vineling": [
            "A {name} creaks to life, detaching itself from the forest.",
            "Roots snap and shift as a {name} lumbers toward you.",
            "The trees themselves seem to turn against you—a {name} awakens.",
            "A {name} rises from the earth, moss and bark forming a deadly shape.",
            "Ancient wood groans as a {name} steps from the canopy.",
        ],
        "Bramble": [
            "A {name} creaks to life, detaching itself from the forest.",
            "Roots snap and shift as a {name} lumbers toward you.",
            "The trees themselves seem to turn against you—a {name} awakens.",
            "A {name} rises from the earth, moss and bark forming a deadly shape.",
            "Ancient wood groans as a {name} steps from the canopy.",
        ],
        "Sporeling": [
            "A {name} creaks to life, detaching itself from the forest.",
            "Roots snap and shift as a {name} lumbers toward you.",
            "The trees themselves seem to turn against you—a {name} awakens.",
            "A {name} rises from the earth, moss and bark forming a deadly shape.",
            "Ancient wood groans as a {name} steps from the canopy.",
        ],
        "Wisp": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Shade": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Revenant": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Wight": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Stormling": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Duskling": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Sprite": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Crawler": [
            "Damp earth churns as a {name} scuttles forth.",
            "A {name} emerges from the muck, clicking its mandibles.",
            "Something wet and many-legged moves in the shadows—a {name} appears.",
            "The stench of rot heralds the arrival of a {name}.",
            "Insects flee as a {name} drags itself into view.",
        ],
        "Urch": [
            "Damp earth churns as a {name} scuttles forth.",
            "A {name} emerges from the muck, clicking its mandibles.",
            "Something wet and many-legged moves in the shadows—a {name} appears.",
            "The stench of rot heralds the arrival of a {name}.",
            "Insects flee as a {name} drags itself into view.",
        ],
        "Lurker": [
            "Damp earth churns as a {name} scuttles forth.",
            "A {name} emerges from the muck, clicking its mandibles.",
            "Something wet and many-legged moves in the shadows—a {name} appears.",
            "The stench of rot heralds the arrival of a {name}.",
            "Insects flee as a {name} drags itself into view.",
        ],
        "Undead": [
            "A {name} shambles forward, bones rattling with ancient hatred.",
            "The grave soil shifts, revealing a {name}.",
            "A hollow groan echoes as a {name} lurches toward you.",
            "Death itself seems to cling to the {name} approaching you.",
            "Empty sockets stare into your soul as a {name} advances.",
        ],
        "Skeleton": [
            "A {name} shambles forward, bones rattling with ancient hatred.",
            "The grave soil shifts, revealing a {name}.",
            "A hollow groan echoes as a {name} lurches toward you.",
            "Death itself seems to cling to the {name} approaching you.",
            "Empty sockets stare into your soul as a {name} advances.",
        ],
        "Zombie": [
            "A {name} shambles forward, bones rattling with ancient hatred.",
            "The grave soil shifts, revealing a {name}.",
            "A hollow groan echoes as a {name} lurches toward you.",
            "Death itself seems to cling to the {name} approaching you.",
            "Empty sockets stare into your soul as a {name} advances.",
        ],
    }

    GENERIC_OPENING = [
        "The air chills as a {name} emerges from the shadows.",
        "A rustle in the undergrowth reveals a {name}, intent on violence.",
        "From the gloom, a {name} steps forward.",
        "A {name} materializes, eyes cold and unfeeling.",
        "Something stirs in the dark—a {name} reveals itself.",
        "The silence is broken by the approach of a {name}.",
        "Your instincts scream danger as a {name} appears.",
        "A {name} stands before you, ready to kill.",
    ]

    # --- MONSTER ATTACK PHRASES ---
    # Structure: (Normal, Critical)
    ATTACK_PHRASES = {
        "Goblin": (
            [
                "The {name} stabs wildly, catching you for `{dmg}` damage!",
                "The {name} lunges with a shriek, slashing for `{dmg}` damage!",
                "A dirty blade finds a gap in your armor— `{dmg}` damage.",
                "The {name} bites and claws, dealing `{dmg}` damage.",
                "A jagged dagger scrapes across your skin— `{dmg}` damage.",
            ],
            [
                "The {name}'s blade sinks deep into your side! `{dmg}` damage! **(CRITICAL!)**",
                "A vicious strike to your ribs leaves you gasping! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} exploits your stumble with a brutal shank! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Slime": (
            [
                "The {name} slams into you with heavy force for `{dmg}` damage.",
                "Acid splashes against your skin— `{dmg}` damage!",
                "The {name} engulfs your limb momentarily, burning for `{dmg}` damage.",
                "A pseudopod whips out, striking you for `{dmg}` damage.",
                "The {name} surges forward, bludgeoning you for `{dmg}` damage.",
            ],
            [
                "The {name} envelops you, its acid dissolving your armor! `{dmg}` damage! **(CRITICAL!)**",
                "A massive surge of sludge crushes the breath from you! `{dmg}` damage! **(CRITICAL!)**",
                "You are trapped in the {name}'s corrosive grip! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Wolf": (
            [
                "The {name} bites down savagely for `{dmg}` damage!",
                "Claws rake your side, drawing blood— `{dmg}` damage.",
                "Hot breath precedes a tearing snap of jaws— `{dmg}` damage.",
                "The {name} leaps, knocking you back for `{dmg}` damage.",
                "Fangs graze your arm— `{dmg}` damage.",
            ],
            [
                "The {name}'s jaws lock onto your limb, tearing flesh! `{dmg}` damage! **(CRITICAL!)**",
                "Claws shred through your defenses, leaving deep gouges! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} goes for the throat—you barely deflect it! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Hound": (
            [
                "The {name} bites down savagely for `{dmg}` damage!",
                "Claws rake your side, drawing blood— `{dmg}` damage.",
                "Hot breath precedes a tearing snap of jaws— `{dmg}` damage.",
                "The {name} leaps, knocking you back for `{dmg}` damage.",
                "Fangs graze your arm— `{dmg}` damage.",
            ],
            [
                "The {name}'s jaws lock onto your limb, tearing flesh! `{dmg}` damage! **(CRITICAL!)**",
                "Claws shred through your defenses, leaving deep gouges! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} goes for the throat—you barely deflect it! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Spider": (
            [
                "The {name} sinks its fangs into you for `{dmg}` damage!",
                "A sharp leg pierces your defense— `{dmg}` damage.",
                "Venom burns as the {name} strikes for `{dmg}` damage.",
                "Webs entangle you as the {name} bites— `{dmg}` damage.",
                "The {name} skitters past, slashing you for `{dmg}` damage.",
            ],
            [
                "Venom floods your veins as the {name} lands a deep bite! `{dmg}` damage! **(CRITICAL!)**",
                "A chitinous leg impales you, pinning you momentarily! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} strikes a nerve cluster—agony blinds you! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Boar": (
            [
                "The {name} swipes with massive force, dealing `{dmg}` damage!",
                "You are thrown back by the {name}'s charge— `{dmg}` damage.",
                "Bone-crushing weight slams into you for `{dmg}` damage.",
                "The {name} gores you with brutal efficiency— `{dmg}` damage.",
                "A tusk grazes your leg— `{dmg}` damage.",
            ],
            [
                "The {name} tramples you, crushing ribs under its weight! `{dmg}` damage! **(CRITICAL!)**",
                "A tusk pierces deep, lifting you off your feet! `{dmg}` damage! **(CRITICAL!)**",
                "The impact of the charge shatters your guard! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Bear": (
            [
                "The {name} swipes with massive force, dealing `{dmg}` damage!",
                "You are thrown back by the {name}'s charge— `{dmg}` damage.",
                "Bone-crushing weight slams into you for `{dmg}` damage.",
                "The {name} mauls you with brutal efficiency— `{dmg}` damage.",
            ],
            [
                "The {name} crushes you in a bear hug, snapping bone! `{dmg}` damage! **(CRITICAL!)**",
                "Massive claws tear through armor and flesh alike! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        "Treant": (
            [
                "A heavy branch bludgeons you for `{dmg}` damage!",
                "Roots whip out, lashing your skin for `{dmg}` damage.",
                "The {name} crushes you with the weight of old wood— `{dmg}` damage.",
                "Thorns tear at your flesh as the {name} strikes for `{dmg}` damage.",
                "The {name} swings a massive limb— `{dmg}` damage.",
            ],
            [
                "A root constricts your chest, cracking ribs! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} brings a massive trunk down, flattening you! `{dmg}` damage! **(CRITICAL!)**",
                "Thorns tear deep into muscle, leaving you bleeding! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        # Mapped types for Treant-like
        "Ent": "Treant", "Vineling": "Treant", "Bramble": "Treant", "Sporeling": "Treant",

        "Wisp": (
            [
                "A cold touch drains your vitality— `{dmg}` damage.",
                "The {name} passes through your guard, chilling you for `{dmg}` damage!",
                "Spectral energy flares, burning you with cold fire for `{dmg}` damage.",
                "The {name} strikes with an otherworldly force— `{dmg}` damage.",
                "Your breath freezes as the {name} touches you— `{dmg}` damage.",
            ],
            [
                "The {name} passes straight through your heart—liquid ice fills your veins! `{dmg}` damage! **(CRITICAL!)**",
                "Soul-flaying cold wracks your body! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} feeds directly on your life force! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        # Mapped types for Wisp-like
        "Shade": "Wisp", "Revenant": "Wisp", "Wight": "Wisp", "Stormling": "Wisp", "Duskling": "Wisp", "Sprite": "Wisp",

        "Crawler": (
            [
                "The {name} pinches you with serrated limbs for `{dmg}` damage!",
                "Acidic slime burns your skin as the {name} strikes— `{dmg}` damage.",
                "Mandibles snap shut on your arm— `{dmg}` damage.",
                "The {name} swarms over your defenses, biting for `{dmg}` damage.",
                "Sharp legs scratch and tear— `{dmg}` damage.",
            ],
            [
                "The {name} burrows its mandibles into your flesh! `{dmg}` damage! **(CRITICAL!)**",
                "Serrated limbs saw through your armor! `{dmg}` damage! **(CRITICAL!)**",
                "Venom and acid overwhelm your senses! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        # Mapped types
        "Urch": "Crawler", "Lurker": "Crawler",

        "Undead": (
            [
                "A rotting fist slams into you for `{dmg}` damage!",
                "Bones rattle as the {name} strikes— `{dmg}` damage.",
                "A rusty weapon swings with unnatural strength, dealing `{dmg}` damage.",
                "The {name} lurches forward, tearing at you for `{dmg}` damage.",
                "Cold, dead fingers claw at your face— `{dmg}` damage.",
            ],
            [
                "The {name}'s rusty blade finds a gap, infecting the wound! `{dmg}` damage! **(CRITICAL!)**",
                "Unnatural strength shatters your block! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} tears a chunk of flesh away! `{dmg}` damage! **(CRITICAL!)**",
            ]
        ),
        # Mapped types
        "Skeleton": "Undead", "Zombie": "Undead",
    }

    GENERIC_ATTACK = (
        [
            "The {name} strikes you for `{dmg}` damage!",
            "You brace too late— `{dmg}` damage from the {name}.",
            "Pain flares as the {name} hits you for `{dmg}` damage.",
            "The {name}'s attack connects with a sickening thud— `{dmg}` damage.",
            "You reel from the {name}'s blow— `{dmg}` damage.",
        ],
        [
            "A devastating blow sends you flying! `{dmg}` damage! **(CRITICAL!)**",
            "The {name} hits you with overwhelming force! `{dmg}` damage! **(CRITICAL!)**",
            "You are crushed under the {name}'s assault! `{dmg}` damage! **(CRITICAL!)**",
        ]
    )

    @staticmethod
    def opening(monster_data: dict) -> str:
        """Generates opening line."""
        name = str(monster_data.get("name", "Unknown Entity"))

        # Check for specific keys in name
        phrase_list = CombatPhrases.GENERIC_OPENING
        for key, phrases in CombatPhrases.OPENING_PHRASES.items():
            if key in name:
                phrase_list = phrases
                break

        return f"**{random.choice(phrase_list).format(name=name)}**"

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
                    f"You bash the {m_name} with your shield before delivering a fatal slash! {d_str}",
                ]
            else:
                pool = [
                    f"You cleave into the {m_name}, steel ringing against bone. {d_str}",
                    f"A heavy blow forces the {m_name} back. {d_str}",
                    f"Your blade bites into the {m_name}'s hide. {d_str}",
                    f"You drive your shoulder into the strike, hitting the {m_name}. {d_str}",
                    f"You deflect an attack and counter with a solid hit. {d_str}",
                ]

        # --- MAGE (ID 2) ---
        elif player_class_id == 2:
            if is_crit:
                pool = [
                    f"The air screams as concentrated mana obliterates the {m_name}'s guard! {d_str}",
                    f"A blinding flash! Your spell consumes the {m_name} in raw power. {d_str}",
                    f"You unravel the {m_name}'s very essence with a surge of arcane force! {d_str}",
                    f"Pure energy arcs from your fingers, turning the {m_name} into a conduit of pain! {d_str}",
                ]
            else:
                pool = [
                    f"Arcane energy hammers the {m_name}. {d_str}",
                    f"A raw bolt of mana sears the {m_name}'s skin. {d_str}",
                    f"You conjure a burst of power, scorching the {m_name}. {d_str}",
                    f"The weave responds to your call, striking the {m_name}. {d_str}",
                    f"You mutter a word of power, and the {m_name} recoils. {d_str}",
                ]

        # --- ROGUE (ID 3) ---
        elif player_class_id == 3:
            if is_crit:
                pool = [
                    f"Perfect execution! Your blade finds a vital artery on the {m_name}. {d_str}",
                    f"You vanish for a heartbeat, reappearing as your dagger sinks deep. {d_str}",
                    f"A spray of blood marks your precision strike on the {m_name}! {d_str}",
                    f"You exploit a micro-second gap, driving your blade into the {m_name}'s weak point! {d_str}",
                ]
            else:
                pool = [
                    f"You slip through an opening, cutting the {m_name}. {d_str}",
                    f"A silent, surgical strike lands true on the {m_name}. {d_str}",
                    f"A rapid feint leaves the {m_name} exposed to your blade. {d_str}",
                    f"You find a gap in the {m_name}'s armor. {d_str}",
                    f"Quick as a viper, you slash the {m_name}. {d_str}",
                ]

        # --- CLERIC (ID 4) ---
        elif player_class_id == 4:
            if is_crit:
                pool = [
                    f"Divine judgment descends! The {m_name} reels from the holy impact. {d_str}",
                    f"Your weapon glows with blinding light, smiting the {m_name} where it stands! {d_str}",
                    f"Faith guides your hand into a devastating blow against the {m_name}! {d_str}",
                    f"A halo of light erupts as you crush the {m_name} with sacred force! {d_str}",
                ]
            else:
                pool = [
                    f"You strike the {m_name} with righteous fury. {d_str}",
                    f"Your weapon descends like judgment upon the {m_name}. {d_str}",
                    f"A flash of holy light accompanies your blow against the {m_name}. {d_str}",
                    f"You batter the {m_name} with the weight of your conviction. {d_str}",
                    f"You chant a hymn of battle, your strike guided by faith. {d_str}",
                ]

        # --- RANGER (ID 5) ---
        elif player_class_id == 5:
            if is_crit:
                pool = [
                    f"A perfect shot! Your arrow pierces the {m_name}'s eye! {d_str}",
                    f"You loose the shaft before the {m_name} can blink—dead center! {d_str}",
                    f"The wind guides your aim into a lethal strike on the {m_name}! {d_str}",
                    f"An impossible shot! You pin the {m_name} with a high-velocity arrow! {d_str}",
                ]
            else:
                pool = [
                    f"Your arrow thuds into the {m_name}. {d_str}",
                    f"A well-placed shot strikes the {m_name}. {d_str}",
                    f"Your bow sings—the {m_name} recoils from the hit. {d_str}",
                    f"You loose an arrow, catching the {m_name} in the flank. {d_str}",
                    f"You snap-fire a shot, hitting the {m_name} in stride. {d_str}",
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

        # 1. Resolve Family
        family = None
        for key in CombatPhrases.ATTACK_PHRASES:
            if key in m_name:
                family = CombatPhrases.ATTACK_PHRASES[key]
                break

        # Check for string mapping (e.g. "Ent" -> "Treant")
        if isinstance(family, str):
            family = CombatPhrases.ATTACK_PHRASES.get(family)

        if not family:
            family = CombatPhrases.GENERIC_ATTACK

        # 2. Select Pool (Normal vs Crit)
        pool = family[1] if is_crit else family[0]

        return random.choice(pool).format(name=m_name, dmg=damage)

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
