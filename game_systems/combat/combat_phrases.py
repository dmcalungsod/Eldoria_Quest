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
                "The {name} throws dirt in your eyes and strikes— `{dmg}` damage.",
                "The {name} leaps from a rock, landing a blow for `{dmg}` damage.",
            ],
            [
                "The {name}'s blade sinks deep into your side! `{dmg}` damage! **(CRITICAL!)**",
                "A vicious strike to your ribs leaves you gasping! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} exploits your stumble with a brutal shank! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Slime": (
            [
                "The {name} slams into you with heavy force for `{dmg}` damage.",
                "Acid splashes against your skin— `{dmg}` damage!",
                "The {name} engulfs your limb momentarily, burning for `{dmg}` damage.",
                "A pseudopod whips out, striking you for `{dmg}` damage.",
                "The {name} surges forward, bludgeoning you for `{dmg}` damage.",
                "A wave of sludge knocks you back— `{dmg}` damage.",
                "The {name} hardens its body and rams you— `{dmg}` damage.",
            ],
            [
                "The {name} envelops you, its acid dissolving your armor! `{dmg}` damage! **(CRITICAL!)**",
                "A massive surge of sludge crushes the breath from you! `{dmg}` damage! **(CRITICAL!)**",
                "You are trapped in the {name}'s corrosive grip! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Wolf": (
            [
                "The {name} bites down savagely for `{dmg}` damage!",
                "Claws rake your side, drawing blood— `{dmg}` damage.",
                "Hot breath precedes a tearing snap of jaws— `{dmg}` damage.",
                "The {name} leaps, knocking you back for `{dmg}` damage.",
                "Fangs graze your arm— `{dmg}` damage.",
                "The {name} circles and snaps at your legs— `{dmg}` damage.",
                "A feral lunge catches you off guard— `{dmg}` damage.",
            ],
            [
                "The {name}'s jaws lock onto your limb, tearing flesh! `{dmg}` damage! **(CRITICAL!)**",
                "Claws shred through your defenses, leaving deep gouges! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} goes for the throat—you barely deflect it! `{dmg}` damage! **(CRITICAL!)**",
            ],
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
            ],
        ),
        "Spider": (
            [
                "The {name} sinks its fangs into you for `{dmg}` damage!",
                "A sharp leg pierces your defense— `{dmg}` damage.",
                "Venom burns as the {name} strikes for `{dmg}` damage.",
                "Webs entangle you as the {name} bites— `{dmg}` damage.",
                "The {name} skitters past, slashing you for `{dmg}` damage.",
                "The {name} drops from above, landing a heavy blow— `{dmg}` damage.",
            ],
            [
                "Venom floods your veins as the {name} lands a deep bite! `{dmg}` damage! **(CRITICAL!)**",
                "A chitinous leg impales you, pinning you momentarily! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} strikes a nerve cluster—agony blinds you! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Boar": (
            [
                "The {name} swipes with massive force, dealing `{dmg}` damage!",
                "You are thrown back by the {name}'s charge— `{dmg}` damage.",
                "Bone-crushing weight slams into you for `{dmg}` damage.",
                "The {name} gores you with brutal efficiency— `{dmg}` damage.",
                "A tusk grazes your leg— `{dmg}` damage.",
                "The {name} thrashes wildly, hitting you— `{dmg}` damage.",
            ],
            [
                "The {name} tramples you, crushing ribs under its weight! `{dmg}` damage! **(CRITICAL!)**",
                "A tusk pierces deep, lifting you off your feet! `{dmg}` damage! **(CRITICAL!)**",
                "The impact of the charge shatters your guard! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Bear": (
            [
                "The {name} swipes with massive force, dealing `{dmg}` damage!",
                "You are thrown back by the {name}'s charge— `{dmg}` damage.",
                "Bone-crushing weight slams into you for `{dmg}` damage.",
                "The {name} mauls you with brutal efficiency— `{dmg}` damage.",
                "A massive paw swats you aside— `{dmg}` damage.",
            ],
            [
                "The {name} crushes you in a bear hug, snapping bone! `{dmg}` damage! **(CRITICAL!)**",
                "Massive claws tear through armor and flesh alike! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Treant": (
            [
                "A heavy branch bludgeons you for `{dmg}` damage!",
                "Roots whip out, lashing your skin for `{dmg}` damage.",
                "The {name} crushes you with the weight of old wood— `{dmg}` damage.",
                "Thorns tear at your flesh as the {name} strikes for `{dmg}` damage.",
                "The {name} swings a massive limb— `{dmg}` damage.",
                "Bark scrapes against steel as the {name} slams you— `{dmg}` damage.",
            ],
            [
                "A root constricts your chest, cracking ribs! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} brings a massive trunk down, flattening you! `{dmg}` damage! **(CRITICAL!)**",
                "Thorns tear deep into muscle, leaving you bleeding! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Ent": "Treant",
        "Vineling": "Treant",
        "Bramble": "Treant",
        "Sporeling": "Treant",
        "Wisp": (
            [
                "A cold touch drains your vitality— `{dmg}` damage.",
                "The {name} passes through your guard, chilling you for `{dmg}` damage!",
                "Spectral energy flares, burning you with cold fire for `{dmg}` damage.",
                "The {name} strikes with an otherworldly force— `{dmg}` damage.",
                "Your breath freezes as the {name} touches you— `{dmg}` damage.",
                "The air warps around the {name} as it hits you— `{dmg}` damage.",
            ],
            [
                "The {name} passes straight through your heart—liquid ice fills your veins! `{dmg}` damage! **(CRITICAL!)**",
                "Soul-flaying cold wracks your body! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} feeds directly on your life force! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Shade": "Wisp",
        "Revenant": "Wisp",
        "Wight": "Wisp",
        "Stormling": "Wisp",
        "Duskling": "Wisp",
        "Sprite": "Wisp",
        "Crawler": (
            [
                "The {name} pinches you with serrated limbs for `{dmg}` damage!",
                "Acidic slime burns your skin as the {name} strikes— `{dmg}` damage.",
                "Mandibles snap shut on your arm— `{dmg}` damage.",
                "The {name} swarms over your defenses, biting for `{dmg}` damage.",
                "Sharp legs scratch and tear— `{dmg}` damage.",
                "The {name} spits a caustic fluid— `{dmg}` damage.",
            ],
            [
                "The {name} burrows its mandibles into your flesh! `{dmg}` damage! **(CRITICAL!)**",
                "Serrated limbs saw through your armor! `{dmg}` damage! **(CRITICAL!)**",
                "Venom and acid overwhelm your senses! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Urch": "Crawler",
        "Lurker": "Crawler",
        "Undead": (
            [
                "A rotting fist slams into you for `{dmg}` damage!",
                "Bones rattle as the {name} strikes— `{dmg}` damage.",
                "A rusty weapon swings with unnatural strength, dealing `{dmg}` damage.",
                "The {name} lurches forward, tearing at you for `{dmg}` damage.",
                "Cold, dead fingers claw at your face— `{dmg}` damage.",
                "The {name} vomits a cloud of decay, choking you— `{dmg}` damage.",
            ],
            [
                "The {name}'s rusty blade finds a gap, infecting the wound! `{dmg}` damage! **(CRITICAL!)**",
                "Unnatural strength shatters your block! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} tears a chunk of flesh away! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Skeleton": "Undead",
        "Zombie": "Undead",
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
        ],
    )

    # --- PLAYER CLASS ATTACK PHRASES ---
    WARRIOR_ATTACKS = (
        [
            "You cleave into the {m_name}, steel ringing against bone. {d_str}",
            "A heavy blow forces the {m_name} back. {d_str}",
            "Your blade bites into the {m_name}'s hide. {d_str}",
            "You drive your shoulder into the strike, hitting the {m_name}. {d_str}",
            "You deflect an attack and counter with a solid hit. {d_str}",
            "You slam your pommel into the {m_name}, following with a slash. {d_str}",
            "You grunt with effort, your weapon carving a path through the {m_name}'s guard. {d_str}",
            "A disciplined strike finds its mark on the {m_name}. {d_str}",
            "You batter the {m_name}'s defenses, chipping away at its resolve. {d_str}",
            "Steel meets flesh in a spray of crimson as you hit the {m_name}. {d_str}",
            "You step into the {m_name}'s range and punish it. {d_str}",
            "Your weapon feels like an extension of your arm as it strikes the {m_name}. {d_str}",
        ],
        [
            "You put your entire weight behind the swing, shattering the {m_name}'s defense! {d_str}",
            "A thunderous impact! Your weapon crushes into the {m_name}. {d_str}",
            "You roar with effort, cleaving deep into the {m_name}'s flesh! {d_str}",
            "You bash the {m_name} with your shield before delivering a fatal slash! {d_str}",
            "Your strike breaks bone and spirit alike! The {m_name} reels! {d_str}",
            "A perfect parry opens the {m_name} for a devastating counter-strike! {d_str}",
            "The force of your blow lifts the {m_name} off its feet! {d_str}",
            "You sever the {m_name}'s guard with brutal efficiency! {d_str}",
        ]
    )

    MAGE_ATTACKS = (
        [
            "Arcane energy hammers the {m_name}. {d_str}",
            "A raw bolt of mana sears the {m_name}'s skin. {d_str}",
            "You conjure a burst of power, scorching the {m_name}. {d_str}",
            "The weave responds to your call, striking the {m_name}. {d_str}",
            "You mutter a word of power, and the {m_name} recoils. {d_str}",
            "Sparks fly from your fingertips, burning the {m_name}. {d_str}",
            "A sudden pressure wave of magic slams into the {m_name}. {d_str}",
            "You weave a quick sigil, sending a dart of energy at the {m_name}. {d_str}",
            "The air crackles around you as you strike the {m_name}. {d_str}",
            "You focus your will, manifesting it as a blow against the {m_name}. {d_str}",
            "Elemental residue clings to the {m_name} after your attack. {d_str}",
            "You chant a brief syllable, and force erupts against the {m_name}. {d_str}",
        ],
        [
            "The air screams as concentrated mana obliterates the {m_name}'s guard! {d_str}",
            "A blinding flash! Your spell consumes the {m_name} in raw power. {d_str}",
            "You unravel the {m_name}'s very essence with a surge of arcane force! {d_str}",
            "Pure energy arcs from your fingers, turning the {m_name} into a conduit of pain! {d_str}",
            "Reality distorts around the {m_name} as your spell impacts! {d_str}",
            "You overcharge the spell, sending the {m_name} flying in a blast of light! {d_str}",
            "The {m_name} is engulfed in a chaotic storm of magic! {d_str}",
            "You tap into the deep ley lines, unleashing a torrent of destruction! {d_str}",
        ]
    )

    ROGUE_ATTACKS = (
        [
            "You slip through an opening, cutting the {m_name}. {d_str}",
            "A silent, surgical strike lands true on the {m_name}. {d_str}",
            "A rapid feint leaves the {m_name} exposed to your blade. {d_str}",
            "You find a gap in the {m_name}'s armor. {d_str}",
            "Quick as a viper, you slash the {m_name}. {d_str}",
            "You sidestep a clumsy attack and punish the {m_name}. {d_str}",
            "Your dagger flicks out, drawing a thin line of red on the {m_name}. {d_str}",
            "You move faster than the {m_name} can follow, striking its flank. {d_str}",
            "A cheap shot, but effective—you hit the {m_name} where it hurts. {d_str}",
            "You dance out of reach, stinging the {m_name} with a quick thrust. {d_str}",
            "Your blade is a blur, catching the {m_name} off balance. {d_str}",
            "Precise and deadly, your attack lands on the {m_name}. {d_str}",
        ],
        [
            "Perfect execution! Your blade finds a vital artery on the {m_name}. {d_str}",
            "You vanish for a heartbeat, reappearing as your dagger sinks deep. {d_str}",
            "A spray of blood marks your precision strike on the {m_name}! {d_str}",
            "You exploit a micro-second gap, driving your blade into the {m_name}'s weak point! {d_str}",
            "You sever a tendon, bringing the {m_name} to its knees! {d_str}",
            "Cold steel meets warm flesh in a lethal display of skill! {d_str}",
            "The {m_name} never saw it coming—your strike is true and deep! {d_str}",
            "You twist the blade, inflicting maximum pain and damage! {d_str}",
        ]
    )

    CLERIC_ATTACKS = (
        [
            "You strike the {m_name} with righteous fury. {d_str}",
            "Your weapon descends like judgment upon the {m_name}. {d_str}",
            "A flash of holy light accompanies your blow against the {m_name}. {d_str}",
            "You batter the {m_name} with the weight of your conviction. {d_str}",
            "You chant a hymn of battle, your strike guided by faith. {d_str}",
            "Your mace connects with a solid, purifying thud against the {m_name}. {d_str}",
            "You drive back the darkness with a heavy swing at the {m_name}. {d_str}",
            "Divine power reinforces your arm as you hit the {m_name}. {d_str}",
            "You punish the {m_name} for its existence. {d_str}",
            "Sacred sparks fly as your weapon impacts the {m_name}. {d_str}",
            "You stand firm, your attack carrying the weight of the church. {d_str}",
            "With a prayer on your lips, you smite the {m_name}. {d_str}",
        ],
        [
            "Divine judgment descends! The {m_name} reels from the holy impact. {d_str}",
            "Your weapon glows with blinding light, smiting the {m_name} where it stands! {d_str}",
            "Faith guides your hand into a devastating blow against the {m_name}! {d_str}",
            "A halo of light erupts as you crush the {m_name} with sacred force! {d_str}",
            "The heavens themselves seem to aid your strike! {d_str}",
            "You purge the corruption with a single, bone-shattering blow! {d_str}",
            "Holy fire sears the {m_name} as your weapon connects! {d_str}",
            "You are the hammer of the gods, and the {m_name} is the anvil! {d_str}",
        ]
    )

    RANGER_ATTACKS = (
        [
            "Your arrow thuds into the {m_name}. {d_str}",
            "A well-placed shot strikes the {m_name}. {d_str}",
            "Your bow sings—the {m_name} recoils from the hit. {d_str}",
            "You loose an arrow, catching the {m_name} in the flank. {d_str}",
            "You snap-fire a shot, hitting the {m_name} in stride. {d_str}",
            "You strafe to the side, firing a shaft into the {m_name}. {d_str}",
            "Your fletching brushes your cheek as you send death at the {m_name}. {d_str}",
            "A quick draw, a loose string, and the {m_name} is hit. {d_str}",
            "You target a joint, slowing the {m_name} with a sharp hit. {d_str}",
            "The wind carries your shot true to the {m_name}. {d_str}",
            "You calmly plant an arrow in the {m_name}'s hide. {d_str}",
            "Your aim is steady, your shot is true against the {m_name}. {d_str}",
        ],
        [
            "A perfect shot! Your arrow pierces the {m_name}'s eye! {d_str}",
            "You loose the shaft before the {m_name} can blink—dead center! {d_str}",
            "The wind guides your aim into a lethal strike on the {m_name}! {d_str}",
            "An impossible shot! You pin the {m_name} with a high-velocity arrow! {d_str}",
            "Your arrow punches through armor and flesh alike! {d_str}",
            "You thread the needle, hitting a vital organ! {d_str}",
            "The {m_name} stumbles, an arrow protruding from its throat! {d_str}",
            "One shot, one devastating impact! {d_str}",
        ]
    )

    DEFAULT_ATTACKS = (
        [
            "You strike cleanly, hitting the {m_name}. {d_str}",
            "A decisive blow lands on the {m_name}. {d_str}",
            "Steel meets flesh as you hit the {m_name}. {d_str}",
        ],
        [
            "An incredible blow! The {m_name} staggers violently. {d_str}",
            "You find a weakness and exploit it with brutal force! {d_str}",
        ]
    )

    # --- CLASS VICTORY PHRASES ---
    WARRIOR_VICTORY = [
        "With a final, brutal swing, you cleave the {name} in two.",
        "The {name} falls, its weapon shattered by your overwhelming force.",
        "You wipe the blood from your blade as the {name} collapses.",
        "Your boot rests on the fallen {name}. The battle is won.",
        "Silence falls as your enemy lies broken at your feet.",
    ]

    MAGE_VICTORY = [
        "The {name} disintegrates into ash, consumed by your magic.",
        "You lower your hand, the last embers fading from the {name}'s corpse.",
        "Frozen in a final scream, the {name} shatters into ice.",
        "The air cools as the {name} falls, its energy spent.",
        "Your spellwork leaves nothing but a smoking crater where the {name} stood.",
    ]

    ROGUE_VICTORY = [
        "The {name} slumps forward, never seeing the final strike.",
        "You sheath your blade before the {name} even hits the ground.",
        "A single, clean cut ends the {name}'s struggle.",
        "You step back into the shadows as the {name} breathes its last.",
        "Bleeding from a dozen wounds, the {name} finally succumbs.",
    ]

    CLERIC_VICTORY = [
        "The light fades, leaving the {name} purified in death.",
        "You offer a brief prayer as the {name} returns to the earth.",
        "Divine judgment has been dealt. The {name} falls.",
        "Your weapon lowers, the {name} purged of its corruption.",
        "Peace returns to the battlefield as the {name} is vanquished.",
    ]

    RANGER_VICTORY = [
        "The {name} falls, a single arrow protruding from its heart.",
        "You lower your bow, watching the {name} take its final breath.",
        "The hunt is over. The {name} lies still.",
        "You retrieve your arrow from the fallen {name}.",
        "Nature claims the {name} once more.",
    ]

    GENERIC_VICTORY = [
        "The {name} collapses, the threat fading.",
        "With a final gasp, the {name} falls silent.",
        "You stand victorious over the fallen {name}.",
        "The {name} lies defeated at your feet.",
    ]

    # --- SKILL PHRASES ---
    SKILL_PHRASES = {
        # --- WARRIOR ---
        "power_strike": [
            "You channel all your might into a single, devastating blow with **{skill_name}**!",
            "Muscles straining, you deliver a bone-crushing **{skill_name}** to the {m_name}!",
            "Your weapon glows with kinetic energy as **{skill_name}** impacts the target!",
        ],
        "cleave": [
            "You swing your weapon in a massive arc, unleashing **{skill_name}**!",
            "Your blade sings through the air, striking multiple foes with **{skill_name}**!",
            "A wide sweep of steel clears the path—**{skill_name}** lands true!",
        ],
        "endure": [
            "You grit your teeth and brace for impact, activating **{skill_name}**.",
            "You steel your resolve, letting **{skill_name}** harden your defenses.",
            "Adrenaline floods your veins as you prepare to withstand the onslaught.",
        ],
        # --- MAGE ---
        "fireball": [
            "You chant the ancient words, and a roaring **{skill_name}** erupts from your hands!",
            "Flames coalesce into a sphere of destruction as you cast **{skill_name}**!",
            "The air shimmers with heat before **{skill_name}** turns the {m_name} to ash!",
        ],
        "ice_lance": [
            "Moisture in the air freezes instantly as you hurl an **{skill_name}**!",
            "A jagged shard of ice forms at your command—**{skill_name}** strikes true!",
            "You conjure a spear of permafrost, driving it into the {m_name}!",
        ],
        "mana_shield": [
            "A shimmering barrier of pure energy surrounds you—**{skill_name}** is active.",
            "You weave a protective shell of mana, invoking **{skill_name}**.",
            "Arcane sigils flare around you, absorbing the next blow.",
        ],
        "explosion": [
            "You unleash your ultimate power—**{skill_name}** obliterates everything in sight!",
            "The world turns white as **{skill_name}** detonates with cataclysmic force!",
            "Gravity itself seems to buckle as you channel **{skill_name}**!",
        ],
        # --- ROGUE ---
        "double_strike": [
            "Your blades become a blur as you execute a **{skill_name}**!",
            "One strike high, one low—**{skill_name}** catches the {m_name} off guard!",
            "You move faster than the eye can follow, landing two hits in a heartbeat!",
        ],
        "toxic_blade": [
            "You coat your weapon in deadly venom and deliver a **{skill_name}**!",
            "A green glint on your steel betrays the poison of **{skill_name}**.",
            "The {m_name} hisses in pain as **{skill_name}** infects its blood!",
        ],
        # --- CLERIC ---
        "heal": [
            "You call upon divine grace, and **{skill_name}** closes your wounds.",
            "A warm, golden light bathes you as **{skill_name}** restores your vitality.",
            "Faith manifests as physical restoration—**{skill_name}** mends your flesh.",
        ],
        "smite": [
            "Holy fire descends from the heavens! **{skill_name}** purges the wicked!",
            "You channel the wrath of the gods into a searing **{skill_name}**!",
            "Blinding light erupts as you judge the {m_name} with **{skill_name}**!",
        ],
        "blessing": [
            "You recite a sacred prayer, granting a **{skill_name}** to bolster your strength.",
            "Divine favor shines upon you as you invoke **{skill_name}**.",
            "A halo of light forms above you, empowering your every move.",
        ],
        # --- RANGER ---
        "true_shot": [
            "You hold your breath, steady your aim, and loose a **{skill_name}**!",
            "Your arrow flies with supernatural precision—a perfect **{skill_name}**!",
            "Time seems to slow as you line up the kill shot with **{skill_name}**!",
        ],
        "multi_shot": [
            "You nock multiple arrows at once and unleash a **{skill_name}**!",
            "A rain of arrows darkens the sky as you use **{skill_name}**!",
            "You fire in rapid succession, turning the air into a deadly volley!",
        ],
    }

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
    def player_attack(player, monster: dict, damage: int, is_crit: bool, player_class_id: int) -> str:
        m_name = str(monster.get("name", "the enemy"))

        # Helper to format damage
        def fmt(dmg, crit):
            base = f"`{dmg}` damage"
            return f"{base} **(CRITICAL!)**" if crit else base

        d_str = fmt(damage, is_crit)
        pool = None

        if player_class_id == 1:
            pool = CombatPhrases.WARRIOR_ATTACKS
        elif player_class_id == 2:
            pool = CombatPhrases.MAGE_ATTACKS
        elif player_class_id == 3:
            pool = CombatPhrases.ROGUE_ATTACKS
        elif player_class_id == 4:
            pool = CombatPhrases.CLERIC_ATTACKS
        elif player_class_id == 5:
            pool = CombatPhrases.RANGER_ATTACKS
        else:
            pool = CombatPhrases.DEFAULT_ATTACKS

        # Select pool based on crit
        phrases = pool[1] if is_crit else pool[0]
        return random.choice(phrases).format(m_name=m_name, d_str=d_str)

    @staticmethod
    def player_skill(player, monster, skill, damage, is_crit) -> str:
        m_name = str(monster.get("name", "the enemy"))
        skill_name = str(skill.get("name", "a skill"))
        skill_key = skill.get("key_id", "")
        crit_text = " **(CRITICAL!)**" if is_crit else ""

        # Check for specific skill phrases
        if skill_key in CombatPhrases.SKILL_PHRASES:
            phrase = random.choice(CombatPhrases.SKILL_PHRASES[skill_key])
            return f"{phrase.format(skill_name=skill_name, m_name=m_name)} (`{damage}` damage){crit_text}"

        # Generic Fallback
        phrases = [
            f"You unleash **{skill_name}**! It crashes into the {m_name} for `{damage}` damage!{crit_text}",
            f"Focusing your strength, you invoke **{skill_name}**, striking the {m_name} for `{damage}` damage.{crit_text}",
            f"Power erupts as **{skill_name}** lands— `{damage}` damage dealt!{crit_text}",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_heal(player, skill, heal_amount) -> str:
        skill_name = str(skill.get("name", "a healing spell"))
        skill_key = skill.get("key_id", "")

        # Check for specific skill phrases
        if skill_key in CombatPhrases.SKILL_PHRASES:
            phrase = random.choice(CombatPhrases.SKILL_PHRASES[skill_key])
            return f"{phrase.format(skill_name=skill_name)} (+`{heal_amount}` HP)"

        # Generic Fallback
        phrases = [
            f"You invoke **{skill_name}**. Warmth floods your body, restoring `{heal_amount}` HP.",
            f"A whispered prayer— **{skill_name}** mends your wounds for `{heal_amount}` HP.",
            f"Light gathers around you as **{skill_name}** takes effect (+`{heal_amount}` HP).",
        ]
        return random.choice(phrases)

    @staticmethod
    def player_buff(player, skill) -> str:
        skill_name = str(skill.get("name", "a buff"))
        skill_key = skill.get("key_id", "")

        # Check for specific skill phrases
        if skill_key in CombatPhrases.SKILL_PHRASES:
            phrase = random.choice(CombatPhrases.SKILL_PHRASES[skill_key])
            return f"{E.BUFF} {phrase.format(skill_name=skill_name)}"

        # Generic Fallback
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
    def telegraph_warning(monster, skill) -> str:
        m_name = str(monster.get("name", "the creature"))
        skill_name = str(skill.get("name", "Unknown Attack"))
        skill_type = skill.get("type", "physical")

        # Magic types -> Interrupt (Attack)
        if skill_type in ["magical", "fire", "ice", "poison", "water", "wind", "earth", "dark", "holy"]:
            hint = "**INTERRUPT** (Attack!)"
            phrases = [
                f"⚠️ The {m_name} begins chanting **{skill_name}**! {hint}",
                f"⚠️ Dark energy gathers for **{skill_name}** around the {m_name}! {hint}",
                f"⚠️ The {m_name} focuses to cast **{skill_name}**! {hint}",
            ]
        # Physical types -> Parry (Defend)
        else:
            hint = "**PARRY** (Defend!)"
            phrases = [
                f"⚠️ The {m_name} winds up for a massive **{skill_name}**! {hint}",
                f"⚠️ The {m_name} roars and prepares to crush you with **{skill_name}**! {hint}",
                f"⚠️ The {m_name} takes a heavy stance for **{skill_name}**! {hint}",
            ]
        return random.choice(phrases)

    @staticmethod
    def counter_success(monster, skill, counter_type) -> str:
        m_name = str(monster.get("name", "the creature"))
        skill_name = str(skill.get("name", "attack"))

        if counter_type == "interrupt":
            return f"⚡ **INTERRUPTED!** You strike the {m_name} while it channels **{skill_name}**! (CRITICAL HIT + STUN)"
        else:
            return f"🛡️ **PARRIED!** You deflect the {m_name}'s **{skill_name}** perfectly! (REFLECT DAMAGE + STUN)"

    @staticmethod
    def player_victory(monster, exp, gold, leveled_up, new_level, player_class_id: int | None = None) -> str:
        m_name = str(monster.get("name", "the enemy"))

        pool = CombatPhrases.GENERIC_VICTORY
        if player_class_id == 1:
            pool = CombatPhrases.WARRIOR_VICTORY
        elif player_class_id == 2:
            pool = CombatPhrases.MAGE_VICTORY
        elif player_class_id == 3:
            pool = CombatPhrases.ROGUE_VICTORY
        elif player_class_id == 4:
            pool = CombatPhrases.CLERIC_VICTORY
        elif player_class_id == 5:
            pool = CombatPhrases.RANGER_VICTORY

        phrase = random.choice(pool).format(name=m_name)

        msg = f"{phrase}\nGained `{exp} EXP`"

        if gold > 0:
            msg += f" and `{gold} Aurum`"

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
