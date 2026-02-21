"""
combat_phrases.py

Provides atmospheric narration for combat.
Hardened: Safe string formatting and robust key handling.
"""

import random
import re

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
            "A magnificent {name} steps forward, its antlers like a crown of bone.",
            "The forest parts for a {name}, its gaze heavy with ancient judgment.",
            "A {name} lowers its head, snorting a challenge into the cold air.",
            "Hooves strike stone—a {name} stands its ground against you.",
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
            "A {name} unfurls from the undergrowth, thorns glistening.",
            "Vines twist and snap—a {name} has noticed you.",
            "The greenery shifts, revealing the hungry form of a {name}.",
        ],
        "Bramble": [
            "Thorns scratch at your armor as a {name} emerges.",
            "A tangled mass of briars moves—a {name} blocks the way.",
            "The {name} rustles, its thorny hide promising pain.",
        ],
        "Sporeling": [
            "A cloud of toxic dust heralds the {name}.",
            "A {name} waddles forward, puffing out clouds of spores.",
            "The air tastes of mold as a {name} approaches.",
        ],
        "Wisp": [
            "The temperature plummets as a {name} flickers into existence.",
            "A spectral chill washes over you—a {name} drifts closer.",
            "A {name} manifests from the gloom, eyes burning with cold light.",
            "Ethereal silence falls, broken only by the hum of a {name}.",
            "A ball of cold fire dances in the air—a {name} approaches.",
        ],
        "Shade": [
            "A shadow detaches itself from the wall—a {name} forms.",
            "Darkness coalesces into the shape of a {name}.",
            "The light dims as a {name} steps from the void.",
        ],
        "Revenant": [
            "A {name} rises, fueled by hate and dark magic.",
            "The air grows heavy with malice—a {name} is here.",
            "A {name} stares at you with eyes that have seen the grave.",
        ],
        "Wight": [
            "Frost forms on the ground as a {name} approaches.",
            "A {name} draws a weapon of cold iron, eyes burning blue.",
            "The chill of the grave follows the {name}.",
        ],
        "Stormling": [
            "Static charges the air—a {name} crackles into view.",
            "A small storm takes shape—a {name} buzzes with energy.",
            "Sparks fly as a {name} darts around you.",
        ],
        "Duskling": [
            "Twilight seems to follow the {name}.",
            "A {name} blends with the shadows, hard to track.",
            "The dim light reveals a {name} waiting for you.",
        ],
        "Sprite": [
            "A mischievous giggle echoes—a {name} appears.",
            "A {name} flits through the air, trailing sparkles.",
            "Small but dangerous, a {name} hover in front of you.",
        ],
        "Crawler": [
            "Damp earth churns as a {name} scuttles forth.",
            "A {name} emerges from the muck, clicking its mandibles.",
            "Something wet and many-legged moves in the shadows—a {name} appears.",
            "The stench of rot heralds the arrival of a {name}.",
            "Insects flee as a {name} drags itself into view.",
        ],
        "Urch": [
            "Spines rattle as a {name} scuttles closer.",
            "A {name} rolls into view, its spikes looking deadly.",
            "The {name} clicks its beak, ready to feed.",
        ],
        "Lurker": [
            "Water ripples—a {name} rises from the depths.",
            "A {name} waits patiently in the shadows.",
            "You feel watched—a {name} reveals itself.",
        ],
        "Undead": [
            "A {name} shambles forward, bones rattling with ancient hatred.",
            "The grave soil shifts, revealing a {name}.",
            "A hollow groan echoes as a {name} lurches toward you.",
            "Death itself seems to cling to the {name} approaching you.",
            "Empty sockets stare into your soul as a {name} advances.",
        ],
        "Skeleton": [
            "Bones click and clatter—a {name} assembles itself.",
            "A {name} raises a rusted weapon, jaw hanging loose.",
            "The {name} steps forward, a mockery of life.",
        ],
        "Zombie": [
            "A rotting {name} moans, hungry for flesh.",
            "The stench of decay announces a {name}.",
            "A {name} drags its foot, moving with relentless purpose.",
        ],
        "Brute": [
            "A hulking {name} crashes through the undergrowth.",
            "The ground shakes as a {name} charges toward you.",
            "Muscles bulging, a {name} roars a challenge.",
        ],
        # --- NEW MONSTER TYPES ---
        "Golem": [
            "The ground trembles as a massive {name} lurches forward.",
            "Heavy footsteps echo—a {name} blocks your path.",
            "Stone grinds against stone as a {name} animates.",
            "A {name} towers over you, an ancient guardian awakened.",
            "Dust falls from the ceiling as a {name} takes a step.",
        ],
        "Gargoyle": [
            "Stone wings snap open—a {name} descends from above.",
            "A statue moves—the {name} turns its gaze upon you.",
            "With a heavy thud, a {name} lands before you.",
            "Granite claws scrape stone as a {name} prepares to strike.",
            "A {name} leers at you from its perch before diving.",
        ],
        "Elemental": [
            "The air warps around a {name} as it manifests.",
            "Raw energy crackles—a {name} takes form.",
            "A {name} surges forward, embodying nature's wrath.",
            "The elements themselves rebel—a {name} is born.",
            "A swirling vortex coalesces into a {name}.",
        ],
        "Drake": [
            "A {name} hisses, scales scraping against rock.",
            "Leathery wings beat the air—a {name} swoops down.",
            "Smoke and heat herald the arrival of a {name}.",
            "A {name} roars, the sound vibrating in your chest.",
            "Predatory eyes track your movement—a {name} hunts.",
        ],
        "Siren": [
            "A haunting melody drifts through the air—a {name} appears.",
            "Beautiful yet deadly, a {name} rises from the water.",
            "The {name}'s song pulls at your mind, urging you closer.",
            "Water cascades off a {name} as it emerges to feed.",
            "A {name} smiles, but its eyes are cold and hungry.",
        ],
        "Eel": [
            "Water churns as a {name} slithers into view.",
            "A long, sinuous shape moves in the darkness—a {name} strikes.",
            "Teeth flash in the gloom—a {name} is upon you.",
            "A {name} winds its way through the currents, seeking prey.",
            "Bio-luminescence flickers—a {name} attacks.",
        ],
        "Construct": [
            "Gears grind and mana hums—a {name} activates.",
            "A {name} clanks forward, driven by ancient magic.",
            "Cold metal and glowing runes mark the {name}'s approach.",
            "A {name} turns its mechanical gaze toward you.",
            "Steam hisses from the joints of a {name}.",
        ],
        "Void": [
            "Reality distorts around a {name}.",
            "Shadows deepen, birthing a {name} from the abyss.",
            "A {name} flickers into existence, defying the light.",
            "The air feels thin and cold near the {name}.",
            "A {name} stares back, a window into nothingness.",
        ],
        "Tortoise": [
            "A {name} lumbers forward, its shell scarred by time.",
            "The earth shakes under the slow tread of a {name}.",
            "An armored {name} snaps its beak aggressively.",
            "A massive shell shifts—the {name} reveals itself.",
            "The {name} is slow, but its presence is undeniable.",
        ],
        "Hare": [
            "A {name} darts past, too fast to track.",
            "Twitching ears signal the arrival of a {name}.",
            "A {name} leaps from cover, eyes wide and feral.",
            "The {name} moves with unnatural speed.",
            "A blur of fur—a {name} is attacking.",
        ],
        "Salamander": [
            "A {name} scurries over hot rocks, tail flickering.",
            "Heat radiates from the {name} as it approaches.",
            "A {name} hisses, its skin glowing with inner fire.",
        ],
        "Guardian": [
            "An ancient {name} stands vigil, weapons drawn.",
            "You have trespassed—the {name} moves to intercept.",
            "A {name} blocks the way, silent and imposing.",
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
    # Structure: (Normal List, Critical List)
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
            ],
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
            ],
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
            ],
            [
                "A root constricts your chest, cracking ribs! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} brings a massive trunk down, flattening you! `{dmg}` damage! **(CRITICAL!)**",
                "Thorns tear deep into muscle, leaving you bleeding! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        # Mapped types for Treant-like
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
            ],
            [
                "The {name} passes straight through your heart—liquid ice fills your veins! `{dmg}` damage! **(CRITICAL!)**",
                "Soul-flaying cold wracks your body! `{dmg}` damage! **(CRITICAL!)**",
                "The {name} feeds directly on your life force! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        # Mapped types for Wisp-like
        "Shade": "Wisp",
        "Revenant": "Wisp",
        "Wight": "Wisp",
        "Stormling": "Wisp",
        "Duskling": "Wisp",
        "Sprite": "Wisp",
        "Void": "Wisp", # Void feels wisp-like/spectral
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
            ],
        ),
        # Mapped types
        "Urch": "Crawler",
        "Lurker": "Crawler",
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
            ],
        ),
        # Mapped types
        "Skeleton": "Undead",
        "Zombie": "Undead",
        # --- NEW TYPES ---
        "Golem": (
            [
                "A massive stone fist slams into you— `{dmg}` damage.",
                "The {name} stomps, sending a shockwave that hits for `{dmg}` damage.",
                "You are struck by a heavy limb— `{dmg}` damage.",
                "The {name} crushes you against the wall— `{dmg}` damage.",
                "Rock grinds on bone as the {name} hits you— `{dmg}` damage.",
            ],
            [
                "The {name} brings both fists down, flattening you! `{dmg}` damage! **(CRITICAL!)**",
                "A boulder-like fist cracks your ribs! `{dmg}` damage! **(CRITICAL!)**",
                "The impact shakes your very bones! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Gargoyle": "Golem",
        "Construct": "Golem",
        "Guardian": "Golem",
        "Drake": (
            [
                "The {name} snaps its jaws shut on you— `{dmg}` damage.",
                "A powerful tail whip knocks the wind out of you— `{dmg}` damage.",
                "Claws sharp as daggers rake your chest— `{dmg}` damage.",
                "The {name} breathes fire, singing your armor— `{dmg}` damage.",
                "You are battered by wings and claws— `{dmg}` damage.",
            ],
            [
                "The {name}'s fangs pierce deep, shaking you violently! `{dmg}` damage! **(CRITICAL!)**",
                "You are engulfed in a point-blank breath attack! `{dmg}` damage! **(CRITICAL!)**",
                "Massive claws tear through your defense like paper! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Salamander": "Drake",
        "Elemental": (
            [
                "Raw energy blasts you for `{dmg}` damage.",
                "The {name} lashes out with a whip of magic— `{dmg}` damage.",
                "You are burned by the {name}'s touch— `{dmg}` damage.",
                "The air around the {name} explodes, hitting you for `{dmg}` damage.",
                "A surge of elemental power knocks you back— `{dmg}` damage.",
            ],
            [
                "The {name} overloads, blasting you with pure chaos! `{dmg}` damage! **(CRITICAL!)**",
                "You are consumed by the elemental storm! `{dmg}` damage! **(CRITICAL!)**",
                "The {name}'s core flares, searing you to the bone! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Siren": (
            [
                "A piercing scream shatters your focus— `{dmg}` damage.",
                "The {name} strikes with unexpected speed— `{dmg}` damage.",
                "Sonic waves batter your body— `{dmg}` damage.",
                "The {name} claws at you— `{dmg}` damage.",
            ],
            [
                "The {name}'s song turns your blood to ice! `{dmg}` damage! **(CRITICAL!)**",
                "A deafening shriek ruptures your eardrums! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Eel": "Siren", # Aquatic/fast
        "Tortoise": (
            [
                "The {name} snaps its beak, catching your arm— `{dmg}` damage.",
                "A heavy shell slam knocks you back— `{dmg}` damage.",
                "The {name} tramples you slowly but heavily— `{dmg}` damage.",
            ],
            [
                "The {name}'s beak crushes bone! `{dmg}` damage! **(CRITICAL!)**",
                "You are pinned and crushed under the {name}'s weight! `{dmg}` damage! **(CRITICAL!)**",
            ],
        ),
        "Hare": "Wolf", # Fast, biting
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

    # --- SKILL PHRASES (New) ---
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

    # --- MONSTER SKILL TYPE PHRASES ---
    MONSTER_SKILL_PHRASES = {
        "fire": [
            "The {m_name} inhales deeply, unleashing a torrent of **{skill_name}**!",
            "Heat builds in the air—**{skill_name}** engulfs you!",
            "A cone of **{skill_name}** scours the ground where you stand!",
            "Flames erupt as the {m_name} uses **{skill_name}**!",
        ],
        "flame": "fire",
        "ember": "fire",
        "burn": "fire",
        "ice": [
            "The air freezes instantly as **{skill_name}** hits!",
            "Shards of ice fly from the {m_name}—**{skill_name}**!",
            "A freezing wind heralds **{skill_name}**, chilling you to the bone!",
            "The {m_name} breathes out a cloud of **{skill_name}**!",
        ],
        "frost": "ice",
        "frozen": "ice",
        "cold": "ice",
        "chill": "ice",
        "void": [
            "Shadows reach out to strangle you—**{skill_name}**!",
            "The {m_name} tears a hole in reality with **{skill_name}**!",
            "Darkness consumes the light as **{skill_name}** hits!",
            "You feel your soul tugged away by **{skill_name}**!",
        ],
        "dark": "void",
        "shadow": "void",
        "null": "void",
        "abyssal": "void",
        "water": [
            "A high-pressure jet of **{skill_name}** slams into you!",
            "The {m_name} summons a crashing wave of **{skill_name}**!",
            "You are battered by the force of **{skill_name}**!",
        ],
        "tide": "water",
        "aqua": "water",
        "bubble": "water",
        "breath": [
            "The {m_name} exhales a deadly cloud of **{skill_name}**!",
            "A noxious fume—**{skill_name}**—fills the air!",
            "You cough and gag as **{skill_name}** washes over you!",
        ],
        "beam": [
            "A focused lance of energy—**{skill_name}**—pierces the air!",
            "The {m_name} focuses its power into a searing **{skill_name}**!",
            "Light bends and twists as **{skill_name}** fires!",
        ],
        "ray": "beam",
        "slash": [
            "The {m_name} lunges with a vicious **{skill_name}**!",
            "Claws flash—**{skill_name}** tears at your defense!",
            "A brutal **{skill_name}** threatens to open you up!",
        ],
        "strike": "slash",
        "bite": "slash",
        "claw": "slash",
        "crush": [
            "The ground heaves under the force of **{skill_name}**!",
            "A shockwave of **{skill_name}** knocks you off balance!",
            "The {m_name} slams the ground, sending a **{skill_name}** your way!",
        ],
        "slam": "crush",
        "heavy": "crush",
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

        # --- WARRIOR (ID 1) ---
        if player_class_id == 1:
            if is_crit:
                pool = [
                    f"You put your entire weight behind the swing, shattering the {m_name}'s defense! {d_str}",
                    f"A thunderous impact! Your weapon crushes into the {m_name}. {d_str}",
                    f"You roar with effort, cleaving deep into the {m_name}'s flesh! {d_str}",
                    f"You bash the {m_name} with your shield before delivering a fatal slash! {d_str}",
                    f"You catch the {m_name} off balance and drive your blade home! {d_str}",
                ]
            else:
                pool = [
                    f"You cleave into the {m_name}, steel ringing against bone. {d_str}",
                    f"A heavy blow forces the {m_name} back. {d_str}",
                    f"Your blade bites into the {m_name}'s hide. {d_str}",
                    f"You drive your shoulder into the strike, hitting the {m_name}. {d_str}",
                    f"You deflect an attack and counter with a solid hit. {d_str}",
                    f"You step in close, pummeling the {m_name}. {d_str}",
                    f"With a grunt of effort, you land a telling blow on the {m_name}. {d_str}",
                ]

        # --- MAGE (ID 2) ---
        elif player_class_id == 2:
            if is_crit:
                pool = [
                    f"The air screams as concentrated mana obliterates the {m_name}'s guard! {d_str}",
                    f"A blinding flash! Your spell consumes the {m_name} in raw power. {d_str}",
                    f"You unravel the {m_name}'s very essence with a surge of arcane force! {d_str}",
                    f"Pure energy arcs from your fingers, turning the {m_name} into a conduit of pain! {d_str}",
                    f"Your magic flares uncontrollably, scorching the {m_name} with primal force! {d_str}",
                ]
            else:
                pool = [
                    f"Arcane energy hammers the {m_name}. {d_str}",
                    f"A raw bolt of mana sears the {m_name}'s skin. {d_str}",
                    f"You conjure a burst of power, scorching the {m_name}. {d_str}",
                    f"The weave responds to your call, striking the {m_name}. {d_str}",
                    f"You mutter a word of power, and the {m_name} recoils. {d_str}",
                    f"You weave a spell of pain, wreathing the {m_name} in fire. {d_str}",
                    f"The air crackles as your magic slams into the {m_name}. {d_str}",
                ]

        # --- ROGUE (ID 3) ---
        elif player_class_id == 3:
            if is_crit:
                pool = [
                    f"Perfect execution! Your blade finds a vital artery on the {m_name}. {d_str}",
                    f"You vanish for a heartbeat, reappearing as your dagger sinks deep. {d_str}",
                    f"A spray of blood marks your precision strike on the {m_name}! {d_str}",
                    f"You exploit a micro-second gap, driving your blade into the {m_name}'s weak point! {d_str}",
                    f"You slide under the {m_name}'s guard and deliver a lethal cut! {d_str}",
                ]
            else:
                pool = [
                    f"You slip through an opening, cutting the {m_name}. {d_str}",
                    f"A silent, surgical strike lands true on the {m_name}. {d_str}",
                    f"A rapid feint leaves the {m_name} exposed to your blade. {d_str}",
                    f"You find a gap in the {m_name}'s armor. {d_str}",
                    f"Quick as a viper, you slash the {m_name}. {d_str}",
                    f"Silent and deadly, you carve a line of red across the {m_name}. {d_str}",
                    f"Before the {m_name} can react, your blade has already struck. {d_str}",
                ]

        # --- CLERIC (ID 4) ---
        elif player_class_id == 4:
            if is_crit:
                pool = [
                    f"Divine judgment descends! The {m_name} reels from the holy impact. {d_str}",
                    f"Your weapon glows with blinding light, smiting the {m_name} where it stands! {d_str}",
                    f"Faith guides your hand into a devastating blow against the {m_name}! {d_str}",
                    f"A halo of light erupts as you crush the {m_name} with sacred force! {d_str}",
                    f"The power of the gods flows through you, breaking the {m_name}! {d_str}",
                ]
            else:
                pool = [
                    f"You strike the {m_name} with righteous fury. {d_str}",
                    f"Your weapon descends like judgment upon the {m_name}. {d_str}",
                    f"A flash of holy light accompanies your blow against the {m_name}. {d_str}",
                    f"You batter the {m_name} with the weight of your conviction. {d_str}",
                    f"You chant a hymn of battle, your strike guided by faith. {d_str}",
                    f"Divine light flares, searing the {m_name} with holy wrath. {d_str}",
                    f"A prayer on your lips, you bring your weapon down with force. {d_str}",
                ]

        # --- RANGER (ID 5) ---
        elif player_class_id == 5:
            if is_crit:
                pool = [
                    f"A perfect shot! Your arrow pierces the {m_name}'s eye! {d_str}",
                    f"You loose the shaft before the {m_name} can blink—dead center! {d_str}",
                    f"The wind guides your aim into a lethal strike on the {m_name}! {d_str}",
                    f"An impossible shot! You pin the {m_name} with a high-velocity arrow! {d_str}",
                    f"Your arrow finds the chink in the {m_name}'s armor, sinking deep! {d_str}",
                ]
            else:
                pool = [
                    f"Your arrow thuds into the {m_name}. {d_str}",
                    f"A well-placed shot strikes the {m_name}. {d_str}",
                    f"Your bow sings—the {m_name} recoils from the hit. {d_str}",
                    f"You loose an arrow, catching the {m_name} in the flank. {d_str}",
                    f"You snap-fire a shot, hitting the {m_name} in stride. {d_str}",
                    f"Your arrow flies true, striking the {m_name} with precision. {d_str}",
                    f"Quick as a thought, you put an arrow into the {m_name}. {d_str}",
                ]

        # --- DEFAULT ---
        else:
            if is_crit:
                pool = [
                    f"An incredible blow! The {m_name} staggers violently. {d_str}",
                    f"You find a weakness and exploit it with brutal force! {d_str}",
                    f"You connect with a savage strike! {d_str}",
                ]
            else:
                pool = [
                    f"You strike cleanly, hitting the {m_name}. {d_str}",
                    f"A decisive blow lands on the {m_name}. {d_str}",
                    f"Steel meets flesh as you hit the {m_name}. {d_str}",
                    f"You manage to land a hit on the {m_name}. {d_str}",
                ]

        return random.choice(pool)

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
        skill_name_lower = skill_name.lower()

        # Try to find a matching keyword for skill type
        matched_pool = None
        for key, value in CombatPhrases.MONSTER_SKILL_PHRASES.items():
            # Use regex to match whole words to prevent "slice" matching "ice"
            if re.search(rf"\b{key}\b", skill_name_lower):
                if isinstance(value, str):
                     # If mapped (e.g., "flame" -> "fire"), retrieve the real list
                    matched_pool = CombatPhrases.MONSTER_SKILL_PHRASES.get(value)
                else:
                    matched_pool = value
                break

        if matched_pool:
            phrase = random.choice(matched_pool)
            return f"{phrase.format(m_name=m_name, skill_name=skill_name)} (`{damage}` damage)"

        # Generic Fallback
        phrases = [
            f"The {m_name} unleashes **{skill_name}**! It hits for `{damage}` damage!",
            f"Dark energy gathers— **{skill_name}** strikes you for `{damage}` damage!",
            f"The {m_name} channels a deadly art: **{skill_name}** deals `{damage}` damage!",
            f"You are blasted by **{skill_name}** for `{damage}` damage!",
        ]
        return random.choice(phrases)

    @staticmethod
    def monster_buff(monster, buff_data) -> str:
        m_name = str(monster.get("name", "the creature"))
        phrases = [
            f"The {m_name} roars, its power swelling.",
            f"The {m_name} glows as it strengthens.",
            f"A dark aura surrounds the {m_name}.",
            f"The {m_name}'s eyes burn brighter with newfound power.",
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
            f"The battle is won; the {m_name} is no more.",
            f"You wipe your blade as the {m_name} crumples.",
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
            f"Wounds knit together as the {m_name} invokes **{skill_name}** (+`{amount}` HP).",
        ]
        return random.choice(phrases)
