"""
adventure_events.py

Provides dark-fantasy narrative text for non-combat exploration events.
Optimized for performance and future biome expansion.
"""

import random

import game_systems.data.emojis as E
from game_systems.core.world_time import Season, TimePhase, Weather


class AdventureEvents:
    """
    Generates atmospheric narrative lines for Eldoria’s exploration system.
    """

    # --- TIME-BASED ATMOSPHERE ---
    ATMOSPHERE_DAWN = [
        "The pale light of dawn reveals the path ahead.",
        "Mist rises from the ground as the sun begins to climb.",
        "The world wakes slowly, bathed in cold morning light.",
        "Dew glistens on the leaves, fresh from the night.",
        "Birds begin their morning chorus, piercing the silence.",
        "The air is crisp and cold, promising a new day.",
    ]

    ATMOSPHERE_DUSK = [
        "The sky turns purple and bruise-colored.",
        "Daylight fades, leaving only grey shadows.",
        "The horizon burns with the dying light of the sun.",
        "Shadows lengthen, distorting the shapes of the trees.",
        "A cool wind picks up, signaling the end of the day.",
        "The first stars struggle to pierce the twilight gloom.",
    ]

    ATMOSPHERE_NIGHT = [
        "The moon is hidden behind thick clouds.",
        "Darkness presses in from all sides.",
        "Strange sounds echo in the gloom.",
        "You feel eyes watching you from the darkness.",
        "The path is barely visible under the starlight.",
        "A chill settles deep in your bones.",
        "Something skitters nearby, unseen in the dark.",
        "The world is reduced to the small circle of your vision.",
    ]

    # --- SEASONAL ATMOSPHERE ---
    ATMOSPHERE_SPRING = [
        "Fresh shoots push through the thawing earth.",
        "The air is filled with the scent of wet soil and new life.",
        "A gentle rain washes away the remnants of winter.",
        "Buds unfurl on the branches, vibrant green against the bark.",
        "Streams swell with meltwater, rushing noisily nearby.",
        "The world feels restless, waking from a long sleep.",
    ]

    ATMOSPHERE_SUMMER = [
        "The heat is heavy and still, pressing down on the world.",
        "Insects buzz lazily in the humid air.",
        "Sunlight bakes the ground, cracking the dry earth.",
        "The canopy is full and lush, casting deep, cool shadows.",
        "Dust kicks up with every step in the dry heat.",
        "The air shimmers with mirages in the distance.",
    ]

    ATMOSPHERE_AUTUMN = [
        "Dry leaves crunch satisfyingly beneath your boots.",
        "The wind carries the scent of woodsmoke and decay.",
        "Trees stand like burning torches in shades of red and gold.",
        "A chill bite is in the air, warning of the coming cold.",
        "The forest floor is a carpet of rust-colored foliage.",
        "Harvest time is near; the world feels old and wise.",
    ]

    ATMOSPHERE_WINTER = [
        "Frost rimes the edges of your cloak.",
        "The air is sharp and metallic, stinging your lungs.",
        "Silence lies heavy over the frozen landscape.",
        "Your breath clouds in the freezing air.",
        "The ground is hard as iron beneath your feet.",
        "Pale sunlight offers no warmth against the biting cold.",
    ]

    # --- WEATHER-BASED ATMOSPHERE ---
    ATMOSPHERE_WEATHER = {
        Weather.RAIN: [
            "Rain lashes against your armor, washing away the dust.",
            "Mud sucks at your boots with every step.",
            "The steady drum of rain drowns out distant sounds.",
            "Water drips from the canopy, forming puddles on the path.",
            "A cold rain chills you to the bone.",
        ],
        Weather.STORM: [
            "Lightning splits the sky, briefly illuminating the darkness.",
            "Thunder rolls like a war drum in the distance.",
            "The wind howls, tearing at your cloak.",
            "Trees groan under the force of the gale.",
            "The storm rages, making travel difficult and dangerous.",
        ],
        Weather.FOG: [
            "Thick fog rolls in, obscuring the path ahead.",
            "Shapes move in the mist, just out of sight.",
            "The world is reduced to a grey haze.",
            "Sound is deadened by the heavy fog.",
            "You feel lost in the swirling white vapor.",
        ],
        Weather.SNOW: [
            "Snow crunch under your boots.",
            "The world is silent and white.",
            "Cold flakes melt on your skin.",
            "Your breath mists in the freezing air.",
        ],
        Weather.ASH: [
            "Grey ash falls like dirty snow.",
            "The air tastes of sulfur and burning.",
            "You cover your mouth to filter the choking dust.",
            "Heat radiates from the ground beneath the ash.",
        ],
        Weather.CLEAR: [
            "The sky is clear and open.",
            "Visibility is good, allowing you to see far.",
            "A gentle breeze stirs the air.",
        ],
    }

    # --- ATMOSPHERIC INTROS (New) ---
    ATMOSPHERE_FOREST = [
        "Sunlight fractures through the leaves, dappling the ground in shifting patterns.",
        "The wind sighs through the branches, carrying the scent of pine and old earth.",
        "A distant bird call echoes, sharp and lonely against the silence.",
        "Dust motes dance in a shaft of light that pierces the canopy.",
        "The undergrowth rustles with unseen life, watching your passage.",
        "Clouds drift overhead, casting fleeting shadows across your path.",
        "A sudden gust shakes the treetops, sending a cascade of leaves spiraling down.",
        "Moss-covered stones line the path, silent sentinels of a forgotten age.",
        "The air is cool and still, heavy with the promise of rain.",
        "Roots snake across the trail like the veins of the earth itself.",
        "Somewhere nearby, a stream babbles, indifferent to your journey.",
        "A ray of sun highlights a patch of wildflowers, a brief moment of beauty.",
    ]

    ATMOSPHERE_THICKET = [
        "Fog clings to the ground, swirling around your ankles like cold spirits.",
        "The air here is thick and humid, tasting of copper and decay.",
        "Twisted vines hang like nooses from the trees above.",
        "A sudden chill drops the temperature, making your breath mist.",
        "Silence presses in, heavy and unnatural, broken only by your heartbeat.",
        "The light turns grey and sickly as the canopy thickens.",
        "Thorns snag at your clothes, as if the forest itself is trying to hold you back.",
        "The ground is soft and yielding, threatening to swallow your boots.",
        "Strange, pale fungi grow in clusters, glowing faintly in the gloom.",
        "A crow watches you from a dead branch, its eyes intelligent and cruel.",
        "The wind whispers through the dry leaves, sounding almost like voices.",
        "Shadows seem to detach themselves from the trees, moving just out of sight.",
    ]

    ATMOSPHERE_ROOTS = [
        "Bioluminescent fungi cast a sickly pale glow on the cavern walls.",
        "Water drips rhythmically from a stalactite, marking the passage of time.",
        "The smell of ozone and rot fills the stagnant air.",
        "Shadows seem to lengthen and grasp at your boots.",
        "A low vibration thrums through the floor, as if the earth itself is groaning.",
        "The air is stale, heavy with the weight of the earth above.",
        "Your footsteps echo loudly, alerting anything that might be listening.",
        "Veins of unknown ore glitter in the darkness, tempting and treacherous.",
        "A cold draft flows from a side passage, carrying the scent of deep water.",
        "Roots break through the stone ceiling, hanging like paralyzed limbs.",
        "The silence here is absolute, pressing against your ears.",
        "Dust falls from above, a reminder of the crushing weight over your head.",
    ]

    ATMOSPHERE_CRYSTAL = [
        "The cavern walls pulse with a soft, rhythmic blue light.",
        "Your reflection is fractured into a thousand pieces by the crystal formations.",
        "A low hum fills the air, resonating in your bones.",
        "The ground is slick with condensation and crushed gemstones.",
        "Clusters of crystals chime softly in the subterranean breeze.",
        "Light refracts through the pillars, creating dazzling rainbows in the dark.",
        "The air is cold and crisp, smelling of ozone and ancient stone.",
        "Shadows here are sharp and jagged, cut by beams of luminescence.",
        "You hear the skittering of many legs echoing off the glass-like walls.",
        "A stalactite drips glowing fluid into a pool of still water.",
        "The silence is broken only by the faint crackle of magical energy.",
        "You feel watched by the very walls, as if the crystals have eyes.",
    ]

    ATMOSPHERE_ARENA = [
        "The roar of the crowd seems distant, muffled by your focus.",
        "Sand crunches beneath your boots, stained with the history of violence.",
        "The metallic tang of blood hangs in the dry air.",
        "Sunlight glares off the stone walls, blinding and unforgiving.",
        "Discarded weapons litter the edges of the pit, monuments to failure.",
        "The gate grinds open with a sound like a beast's growl.",
        "You feel the gaze of unseen spectators, hungry for spectacle.",
        "Dust swirls in the center of the arena, forming fleeting shapes.",
    ]

    ATMOSPHERE_MAGMA = [
        "The ground trembles beneath your feet, and cracks hiss with steam.",
        "Waves of heat distort the air, making the distant peaks shimmer.",
        "A geyser of magma erupts nearby, raining molten droplets.",
        "The smell of sulfur and burning rock is overpowering.",
        "Ash falls gently like grey snow, coating your armor.",
        "Lava flows sluggishly in rivers of fire, illuminating the dark rock.",
        "The roar of the volcano is a constant, low-frequency rumble.",
        "Sparks dance in the updrafts, fleeting and dangerous.",
        "You feel the intense heat radiating through the soles of your boots.",
        "Shadows flicker wildly as the magma bubbles and bursts.",
        "The air is dry and searing, parching your throat with every breath.",
        "Jagged obsidian formations loom like black teeth against the glow.",
    ]

    ATMOSPHERE_GROTTO = [
        "The sound of dripping water echoes endlessly in the dark.",
        "Bioluminescent algae paints the walls in soft, eerie blues.",
        "The air is damp and smells of salt and ancient stone.",
        "You hear the distant crash of subterranean waves.",
        "Slick, wet stone makes every step treacherous.",
        "Strange, pale fish dart away from your light.",
        "The pressure of the earth above feels immense.",
        "A cold mist rises from the dark pools around you.",
    ]

    ATMOSPHERE_CLOCKWORK = [
        "The sound of grinding gears echoes through the halls.",
        "Steam hisses from a broken pipe, obscuring your vision.",
        "The rhythmic ticking of a thousand clocks fills the air.",
        "Brass automatons stand frozen in the alcoves, watching.",
        "The air smells of oil and ozone.",
        "A sudden clang makes you jump.",
        "Pistons drive massive machinery in the distance.",
        "The floor vibrates with the energy of the ancient engine.",
    ]

    ATMOSPHERE_BLOOD_MOON = [
        "The moon is a crimson eye, watching your every move.",
        "The light is sickly red, casting long, bloody shadows.",
        "A low, rhythmic thrumming fills the air, like a giant heart.",
        "The stars are drowned out by the blood-red glow.",
        "Monsters howl in the distance, their voices twisted by madness.",
        "The air smells of iron and old blood.",
        "You feel a strange energy coursing through the land.",
        "The shadows seem to bleed into the light.",
    ]

    ATMOSPHERE_HARVEST = [
        "Golden light floods the forest, warming the earth.",
        "The scent of ripe fruit and blooming flowers fills the air.",
        "Nature seems to be celebrating, with life bursting from every corner.",
        "A gentle breeze carries the sweet smell of harvest.",
        "The world feels vibrant and alive, teeming with bounty.",
        "You spot colorful ribbons tied to the trees, marking the festival.",
        "The sun shines brighter, promising good fortune.",
        "Leaves rustle with a joyous energy.",
    ]

    ATMOSPHERE_ASHLANDS = [
        "The ground is hot beneath your boots, and ash chokes the air.",
        "Skeletal trees claw at the grey sky, stripped of all life.",
        "A constant, low rumble vibrates through the volcanic rock.",
        "The air smells of sulfur and old fire.",
        "Dust storms swirl across the barren plains, obscuring vision.",
        "You step over the charred remains of what was once a forest.",
        "Heat radiates from the cracks in the earth.",
        "The silence is heavy, broken only by the hiss of escaping steam.",
        "A red haze hangs over the horizon, where the lava flows.",
        "Nothing grows here but the twisted, thorny ash blossoms.",
        "The wind howls through the canyons like a dying beast.",
        "Your skin feels dry and tight from the oppressive heat.",
    ]

    ATMOSPHERE_OSSUARY = [
        "The rattle of bones echoes down the long, dark corridor.",
        "Dust motes dance in the pale light of a necromantic torch.",
        "You feel the weight of a thousand years of silence.",
        "Empty eye sockets seem to watch you from the walls.",
        "The air is cold and still, smelling of preservatives and decay.",
        "Shadows stretch and twist, mimicking the shapes of the dead.",
        "A cold draft chills you to the bone.",
        "You step on a loose tile, the sound echoing like a gunshot.",
        "Whispers drift from the darkness, unintelligible but menacing.",
        "The ossuary is a monument to death, vast and unending.",
        "Bones crunch underfoot, the only sound in the suffocating silence.",
        "A spectral chill passes through you, leaving frost on your armor.",
    ]

    ATMOSPHERE_ARCHIVES = [
        "Thousands of books float in the air, defying gravity.",
        "The sound of turning pages fills the silence like rustling leaves.",
        "Ink drips from the ceiling, forming puddles of dark magic.",
        "You feel the weight of forbidden knowledge pressing on your mind.",
        "The shelves seem to stretch on forever, disappearing into the gloom.",
        "A spectral librarian watches you from the end of the aisle.",
        "Dust motes swirl in the light of floating arcane candles.",
        "The air smells of old paper and ozone.",
        "Whispers emanate from the books, tempting you to read them.",
        "Shadows flicker as if they have a life of their own.",
        "A chill draft blows through the stacks, carrying the scent of decay.",
        "The silence here is heavy, broken only by your own heartbeat.",
    ]

    ATMOSPHERE_FROSTFALL = [
        "A biting wind screams across the ice, carrying the ghosts of the fallen.",
        "Snowdrifts hide treacherous crevices, waiting to swallow the unwary.",
        "The cold is a physical weight, pressing against your armor.",
        "Ice crystals form on your eyelashes, blurring your vision.",
        "The aurora borealis dances overhead, beautiful and indifferent.",
        "Ancient ruins poke through the snow, silent monuments to a lost age.",
        "The silence of the tundra is absolute, broken only by the wind.",
        "You trudge through knee-deep snow, every step a battle.",
        "A white wolf howls in the distance, a lonely and haunting sound.",
        "The air is so cold it burns your lungs with every breath.",
        "Frozen waterfalls hang like crystal curtains from the cliffs.",
        "Shadows on the ice seem to move, tracking your progress.",
    ]

    ATMOSPHERE_ABYSSAL = [
        "The crushing dark presses against your skin.",
        "You feel a steady, maddening pull downward.",
        "Whispers from the Void echo through the endless chasm.",
        "Every step feels heavier, as if gravity is collapsing.",
    ]

    ATMOSPHERE_OUROS = [
        "The silence is absolute, a crushing weight against your eardrums.",
        "Perfectly preserved buildings loom, their windows staring like empty eyes.",
        "Not a speck of dust moves. The air itself feels frozen in time.",
        "You catch yourself holding your breath to avoid breaking the stillness.",
        "Statues line the streets, or perhaps they were once people.",
        "Your reflection in the polished obsidian seems to move a fraction of a second too late.",
        "A profound sense of wrongness permeates every pristine cobblestone.",
        "You feel as though a single loud noise might shatter reality itself.",
        "The city's unnerving perfection mocks the chaos of the living.",
        "Time has forgotten this place, and it resents your intrusion.",
        "You listen for a heartbeat, but the city has none.",
        "The shadows here do not flicker; they are as static as the stone.",
    ]

    ATMOSPHERE_CRIMSON = [
        "The architecture twists in ways that make your eyes ache.",
        "Aether drips from the ceiling like coagulated blood.",
        "You hear the phantom clash of steel from a battle fought ages ago.",
        "An Echo of a Vanguard knight screams a silent order before shattering.",
        "The walls pulse with a sickening, rhythmic heartbeat.",
        "You catch the scent of ozone, copper, and profound despair.",
        "A shadow on the wall replays a horrific death on a loop.",
        "The air itself feels toxic, burning your throat with every breath.",
        "You step around a floating chunk of obsidian, defying gravity.",
        "The rift above watches you like a massive, unblinking eye.",
        "Voices of the fallen whisper tactical commands that lead to ruin.",
        "The red light casts long, impossible shadows that seem to grasp at you.",
    ]

    # --- REGENERATION PHRASES ---
    REGEN_PHRASES = [
        f"{E.FOREST} You pause to catch your breath by a stream...",
        f"{E.FOREST} You find a safe clearing and rest your weary limbs...",
        f"{E.FOREST} The air is calm. You take a moment to meditate...",
        f"{E.FOREST} A faint warmth settles over you as the forest seems to breathe.",
        f"{E.FOREST} You steady your heartbeat and let the world fall quiet.",
        f"{E.FOREST} Rest comes easily as the whisper of leaves soothes your thoughts.",
        f"{E.FOREST} You kneel beneath an ancient oak, drawing strength from its presence.",
        f"{E.FOREST} A soft glow filters through the canopy, easing your muscles.",
        f"{E.FOREST} You close your eyes, letting the earth cradle your exhaustion.",
        f"{E.FOREST} The scent of moss and rain helps clear your mind.",
        f"{E.FOREST} You wash your hands in a cold brook, feeling clarity return.",
        f"{E.FOREST} A moment of stillness blankets you, renewing resolve.",
    ]

    REGEN_PHRASES_THICKET = [
        f"{E.THICKET} The canopy is so thick here that day feels like twilight. You rest against a moss-slicked trunk.",
        f"{E.THICKET} You listen to the scuttling in the brush, forcing your breathing to slow.",
        f"{E.THICKET} Shadows stretch long and thin. You take a moment to bind a scrap of cloth over a scratch.",
        f"{E.THICKET} The air is heavy with pollen and unease. You wipe sweat from your brow.",
        f"{E.THICKET} You find a hollow beneath a gnarled root and crouch, staying out of sight.",
        f"{E.THICKET} Silence is a luxury here. You snatch a moment of peace while you can.",
    ]

    REGEN_PHRASES_ROOTS = [
        f"{E.CAVE} The air tastes of rot. You crouch between the twisted roots, hoping nothing sees you.",
        f"{E.CAVE} A low hum vibrates through the ground. You close your eyes, trying to ignore the corruption.",
        f"{E.CAVE} You wring out a cloth damp with gray water. There is no comfort here, only a brief pause.",
        f"{E.CAVE} The darkness presses in. You steady your nerves before moving on.",
        f"{E.CAVE} Beneath the tangled roots, you find a dry spot to rest your aching legs.",
        f"{E.CAVE} Every shadow looks like a threat. You rest with one hand on your weapon.",
    ]

    REGEN_PHRASES_CRYSTAL = [
        f"{E.CRYSTAL} You lean against a warm crystal pillar, letting its energy seep into you.",
        f"{E.CRYSTAL} The blue light is soothing. You take a moment to clear your mind.",
        f"{E.CRYSTAL} You find a safe alcove among the quartz and catch your breath.",
        f"{E.CRYSTAL} The hum of the crystals resonates with your heartbeat, calming you.",
        f"{E.CRYSTAL} You check your gear in the reflection of a massive gemstone.",
        f"{E.CRYSTAL} The air is pure here. You breathe deeply, feeling your strength return.",
    ]

    REGEN_PHRASES_ARENA = [
        f"{E.SWORDS} You wipe sweat from your brow. The next bout will be harder.",
        f"{E.SWORDS} The stone floor is cold beneath you. You check your weapon's edge.",
        f"{E.SWORDS} You take a knee, analyzing your previous strikes.",
        f"{E.SWORDS} Amidst the dust and blood, you find a second wind.",
        f"{E.SWORDS} You tighten your grip, letting the adrenaline fade just enough to think clearly.",
        f"{E.SWORDS} The arena is unforgiving. You use this moment to steel your resolve.",
    ]

    REGEN_PHRASES_MAGMA = [
        f"{E.VOLCANO} You find a shelf of cool rock away from the lava flow and rest.",
        f"{E.VOLCANO} The heat is exhausting. You drink deeply from your waterskin.",
        f"{E.VOLCANO} You wipe soot from your eyes and take a moment to breathe.",
        f"{E.VOLCANO} Shielded by a large boulder, you escape the worst of the heat.",
        f"{E.VOLCANO} You check your gear for heat damage while catching your breath.",
        f"{E.VOLCANO} The rhythmic pulsing of the earth lulls you into a brief trance.",
    ]

    REGEN_PHRASES_GROTTO = [
        f"{E.OCEAN} You find a dry ledge above the water and rest.",
        f"{E.OCEAN} The rhythmic sound of waves calms your nerves.",
        f"{E.OCEAN} You wring out your soaked cloak and take a breath.",
        f"{E.OCEAN} The bioluminescence is soothing. You watch the lights drift.",
        f"{E.OCEAN} You splash cold cave water on your face to stay alert.",
        f"{E.OCEAN} Huddled away from the damp, you check your weapons for rust.",
    ]

    REGEN_PHRASES_CLOCKWORK = [
        f"{E.GEAR} You find a quiet corner away from the moving parts and rest.",
        f"{E.GEAR} The rhythmic ticking helps you focus your breathing.",
        f"{E.GEAR} You adjust your gear while the steam clears.",
        f"{E.GEAR} Huddled behind a brass pillar, you take a moment.",
        f"{E.GEAR} You watch the mesmerizing rotation of the gears and calm your mind.",
    ]

    REGEN_PHRASES_ASHLANDS = [
        f"{E.VOLCANO} You find a windbreak behind a large obsidian boulder and rest.",
        f"{E.VOLCANO} The air is thick, but you manage to catch your breath.",
        f"{E.VOLCANO} You wipe the ash from your face and take a sip of warm water.",
        f"{E.VOLCANO} Huddled in a shallow depression, you wait for the dust to settle.",
        f"{E.VOLCANO} The heat is draining, but you force yourself to focus.",
        f"{E.VOLCANO} You inspect your gear for signs of melting or corrosion.",
    ]

    REGEN_PHRASES_OSSUARY = [
        f"{E.SKULL} You find a quiet alcove free of bones and rest.",
        f"{E.SKULL} The silence is oppressive, but you manage to catch your breath.",
        f"{E.SKULL} You lean against a sarcophagus, grateful for the respite.",
        f"{E.SKULL} You clear a space on the dusty floor and sit.",
        f"{E.SKULL} Ignoring the staring skulls, you bandage your wounds.",
        f"{E.SKULL} The cold air numbs your pain as you rest.",
        f"{E.SKULL} You find a moment of peace in the house of the dead.",
    ]

    REGEN_PHRASES_ARCHIVES = [
        "📚 You find a reading nook and rest your legs.",
        "📚 The quiet of the library soothes your nerves.",
        "📚 You lean against a stack of ancient tomes and catch your breath.",
        "📚 The smell of old paper is strangely comforting.",
        "📚 You bandage your wounds while ignoring the whispers.",
        "📚 A floating candle provides a warm light as you rest.",
    ]

    REGEN_PHRASES_ABYSSAL = [
        f"{E.CAVE} You wedge yourself into a crack in the stone, seeking safety from the falling dark.",
        f"{E.CAVE} In a rare moment of stillness, you bind your wounds before the descent continues.",
        f"{E.CAVE} The heavy air fills your lungs. You steel your resolve against the abyss.",
    ]

    REGEN_PHRASES_OUROS = [
        f"{E.TIME} You find a preserved plaza and sit, desperate for any sensation.",
        f"{E.TIME} The deafening silence rings in your ears as you force yourself to rest.",
        f"{E.TIME} You bind your wounds in the shadow of a motionless monument.",
        f"{E.TIME} Staring at an unmoving fountain, you wait for your racing heart to slow.",
        f"{E.TIME} A moment of pause stretches uncomfortably long in the dead city.",
        f"{E.TIME} The pristine cobblestones offer a strange, unsettling comfort.",
        f"{E.TIME} You close your eyes, trying to conjure a memory of sound.",
    ]

    REGEN_PHRASES_CRIMSON = [
        f"{E.BLOOD} You huddle behind a jagged outcrop, wiping Aether from your face.",
        f"{E.BLOOD} The veil bleeds around you as you force a bandage over your wound.",
        f"{E.BLOOD} You close your eyes to block out the shifting geometries and rest.",
        f"{E.BLOOD} A phantom knight falls beside you, an Echo fading as you catch your breath.",
        f"{E.BLOOD} You choke on the metallic air, steeling your resolve against the corruption.",
        f"{E.BLOOD} A brief lull in the whispers allows you a moment of desperate respite.",
        f"{E.BLOOD} You lean against a warm, pulsing wall, drawing whatever strength remains.",
    ]

    REGEN_LOW_HP = [
        f"{E.HEART} Blood drips from your fingers. You lean against a wall, forcing yourself to breathe.",
        f"{E.HEART} Your vision swims. You bind your wounds with trembling hands.",
        f"{E.HEART} Every step is agony. You collapse for a moment, gathering what little strength remains.",
        f"{E.HEART} You taste copper. Resting is no longer a choice; it is necessity.",
        f"{E.HEART} The world spins. You grit your teeth and tighten the bandage.",
    ]

    REGEN_HIGH_HP = [
        f"{E.BUFF} You feel the rhythm of the battle in your veins. You are ready for more.",
        f"{E.BUFF} Your breath comes easy. You sharpen your senses, scanning for the next threat.",
        f"{E.BUFF} You stretch your limbs, feeling the power coiling within your muscles.",
        f"{E.BUFF} Unscathed and undeterred, you take a moment to center yourself.",
        f"{E.BUFF} The danger only sharpens your focus. You are in control.",
    ]

    REGEN_CLASS_PHRASES = {
        "Warrior": [
            f"{E.SHIELD} You check the straps of your armor and wipe gore from your steel.",
            f"{E.SHIELD} The weight of your weapon is comforting. You stand ready.",
            f"{E.SHIELD} You roll your shoulders, working out the stiffness of battle.",
        ],
        "Mage": [
            f"{E.MANA} You murmur an incantation, letting the ambient mana restore your focus.",
            f"{E.MANA} You trace a sigil in the air, stabilizing the flow of magic within you.",
            f"{E.MANA} The hum of the ley lines soothes your mind.",
        ],
        "Rogue": [
            f"{E.DAGGER} You vanish into the shadows, checking your blades while unseen.",
            f"{E.DAGGER} You listen to the silence, your breath barely a whisper.",
            f"{E.DAGGER} You adjust your cloak, becoming one with the darkness.",
        ],
        "Cleric": [
            f"{E.HEAL} You whisper a prayer, and a soft light knits your fatigue away.",
            f"{E.HEAL} You clutch your holy symbol, finding peace in your faith.",
            f"{E.HEAL} A moment of grace descends upon you, washing away the pain.",
        ],
        "Ranger": [
            f"{E.BOW} You check the fletching of your arrows and scan the horizon.",
            f"{E.BOW} You read the wind and the earth, finding a safe path.",
            f"{E.BOW} The wild speaks to you, guiding you to a place of rest.",
        ],
    }

    GATHER_PHRASES = [
        f"{E.HERB} You spot a cluster of **{{}}** in the shade. You harvest it.",
        f"{E.HERB} A faint glow draws your attention — **{{}}**, thriving between roots.",
        f"{E.HERB} Beneath fallen leaves, you uncover **{{}}**, fresh and untouched.",
        f"{E.HERB} Hidden in a fold of roots you find **{{}}**; you collect it with care.",
        f"{E.HERB} A sharp herbal scent fills the air as you gather **{{}}**.",
    ]

    LOCATE_PHRASES = [
        f"{E.MAP} After searching the creek, you find **{{}}** hiding behind a rock!",
        f"{E.MAP} Tracks lead you to a hollow trunk — **{{}}** rests within.",
        f"{E.MAP} A soft whimper alerts you. **{{}}** lies curled beneath an outcrop.",
        f"{E.MAP} You follow tiny prints to a burrow and discover **{{}}**.",
        f"{E.MAP} A scrap of cloth catches your eye—behind it, **{{}}** waits.",
    ]

    EXAMINE_PHRASES = [
        f"{E.SCROLL} You find the **{{}}** and study it, noting every detail.",
        f"{E.SCROLL} Strange sigils surround the **{{}}**. You record them.",
        f"{E.SCROLL} You kneel, observing **{{}}** with deliberate focus.",
        f"{E.SCROLL} Dust and carvings frame the object; you catalog clues about **{{}}**.",
    ]

    FALLBACK_QUEST_PHRASES = [
        f"{E.CHECK} You mark **{{}}** in your Guild log.",
        f"{E.CHECK} Your search succeeds — **{{}}** confirmed.",
        f"{E.CHECK} You update the quest record: **{{}}** located.",
        f"{E.CHECK} A clue reveals **{{}}**. You take note.",
        f"{E.CHECK} You carefully bag evidence linked to **{{}}**.",
    ]

    WILD_GATHER_PHRASES = [
        f"{E.HERB} You stumble upon **{{}}** growing wild.",
        f"{E.HERB} A lucky find! You collect **{{}}** from the underbrush.",
        f"{E.HERB} You notice **{{}}** hidden nearby and secure it.",
        f"{E.HERB} The environment yields **{{}}** to your keen eye.",
        f"{E.HERB} You gather **{{}}** while catching your breath.",
    ]

    NO_EVENT_PHRASES = [
        f"{E.FOREST} You search the area but find nothing of interest.",
        f"{E.FOREST} The forest is quiet... too quiet.",
        f"{E.FOREST} A cold wind blows, but no monsters appear.",
        f"{E.FOREST} You follow a game trail, but it runs cold.",
        f"{E.FOREST} Only the rustle of distant branches answers your search.",
        f"{E.FOREST} You sense movement, but it fades before you can track it.",
        f"{E.FOREST} A hollow stillness clings to the woods.",
        f"{E.FOREST} You find old footprints… but whatever made them is long gone.",
        f"{E.FOREST} A faint echo drifts through the trees, revealing nothing.",
        f"{E.FOREST} Shadows stretch between the roots, hiding nothing of value.",
        f"{E.FOREST} A crow watches you silently before taking flight.",
        f"{E.FOREST} Your footsteps crunch through leaves, but no path unfolds.",
        f"{E.FOREST} The air thickens with the scent of rain.",
    ]

    SURGE_PHRASES = [
        f"{E.BUFF} Your health is full, so you push forward with renewed vigor!",
        f"{E.BUFF} Feeling unstoppable, you channel your energy into the hunt.",
        f"{E.BUFF} Vitality courses through you. You focus entirely on finding resources.",
        f"{E.BUFF} You are at peak condition. Your senses sharpen.",
        f"{E.BUFF} With no need to rest, you scour the area with double the effort.",
    ]

    SCAVENGE_AURUM_PHRASES = [
        f"{E.AURUM} You didn't find materials, but you spotted a pouch containing **{{}} Aurum**.",
        f"{E.AURUM} A gleam in the dirt reveals **{{}} Aurum**.",
        f"{E.AURUM} Hidden in a hollow stump, you find **{{}} Aurum**.",
    ]

    SCAVENGE_EXP_PHRASES = [
        f"{E.EXP} The search yielded no items, but you gained **{{}} XP** from studying the area.",
        f"{E.EXP} You find ancient markings, earning **{{}} XP**.",
        f"{E.EXP} Navigating the rough terrain grants you **{{}} XP**.",
    ]

    # --- SPECIAL EVENT PHRASES ---
    SAFE_ROOM_PHRASES = [
        f"{E.HEAL} You discover a hidden sanctuary, untouched by the dungeon's corruption.",
        f"{E.HEAL} A secure chamber with a fresh spring offers a moment of true respite.",
        f"{E.HEAL} You stumble into a fortified camp left by previous explorers.",
        f"{E.HEAL} A circle of protective runes keeps the monsters at bay.",
        f"{E.HEAL} You find a sunlit glade where the air feels pure and healing.",
    ]

    HIDDEN_STASH_PHRASES = [
        f"{E.LOOT} You notice a loose stone and pry it open to reveal a hidden cache!",
        f"{E.LOOT} Hidden within a hollow tree, you find a stash of supplies.",
        f"{E.LOOT} You uncover a buried chest, its lock long since rusted away.",
        f"{E.LOOT} A skeleton clutches a bag of valuables—you relieve it of its burden.",
        f"{E.LOOT} You spot a glimmer in the debris and dig out a forgotten treasure.",
    ]

    ANCIENT_SHRINE_PHRASES = [
        f"{E.EXP} You kneel before an ancient shrine, and knowledge flows into your mind.",
        f"{E.EXP} Touching the monolith, you see visions of the dungeon's history.",
        f"{E.EXP} The inscriptions on the wall glow, imparting forgotten secrets.",
        f"{E.EXP} You meditate at a place of power, expanding your understanding.",
        f"{E.EXP} A spectral guide appears briefly, pointing the way forward.",
    ]

    TRAP_PHRASES = [
        f"{E.TRAP} **CLICK.** You trigger a hidden mechanism!",
        f"{E.TRAP} The ground gives way beneath your feet!",
        f"{E.TRAP} A tripwire snaps, releasing a swinging log!",
        f"{E.TRAP} Poisonous darts fly from the walls!",
        f"{E.TRAP} You step on a rune that explodes with magical force!",
    ]

    _LOCATION_REGEN_PHRASES = {
        "whispering_thicket": REGEN_PHRASES_THICKET,
        "deepgrove_roots": REGEN_PHRASES_ROOTS,
        "crystal_caverns": REGEN_PHRASES_CRYSTAL,
        "molten_caldera": REGEN_PHRASES_MAGMA,
        "sunken_grotto": REGEN_PHRASES_GROTTO,
        "clockwork_halls": REGEN_PHRASES_CLOCKWORK,
        "guild_arena": REGEN_PHRASES_ARENA,
        "the_ashlands": REGEN_PHRASES_ASHLANDS,
        "forgotten_ossuary": REGEN_PHRASES_OSSUARY,
        "whispering_archives": REGEN_PHRASES_ARCHIVES,
        "abyssal_descent": REGEN_PHRASES_ABYSSAL,
        "silent_city_ouros": REGEN_PHRASES_OUROS,
        "the_crimson_citadel": REGEN_PHRASES_CRIMSON,
    }

    _LOCATION_ATMOSPHERE = {
        "whispering_thicket": ATMOSPHERE_THICKET,
        "deepgrove_roots": ATMOSPHERE_ROOTS,
        "crystal_caverns": ATMOSPHERE_CRYSTAL,
        "molten_caldera": ATMOSPHERE_MAGMA,
        "sunken_grotto": ATMOSPHERE_GROTTO,
        "clockwork_halls": ATMOSPHERE_CLOCKWORK,
        "guild_arena": ATMOSPHERE_ARENA,
        "the_ashlands": ATMOSPHERE_ASHLANDS,
        "forgotten_ossuary": ATMOSPHERE_OSSUARY,
        "whispering_archives": ATMOSPHERE_ARCHIVES,
        "abyssal_descent": ATMOSPHERE_ABYSSAL,
        "silent_city_ouros": ATMOSPHERE_OUROS,
        "the_crimson_citadel": ATMOSPHERE_CRIMSON,
    }

    _EVENT_ATMOSPHERE = {
        "blood_moon": ATMOSPHERE_BLOOD_MOON,
        "harvest_festival": ATMOSPHERE_HARVEST,
        "frostfall_expedition": ATMOSPHERE_FROSTFALL,
    }

    _TIME_PHASE_ATMOSPHERE = {
        TimePhase.NIGHT: ATMOSPHERE_NIGHT,
        TimePhase.DAWN: ATMOSPHERE_DAWN,
        TimePhase.DUSK: ATMOSPHERE_DUSK,
    }

    _SEASONAL_ATMOSPHERE = {
        Season.SPRING: ATMOSPHERE_SPRING,
        Season.SUMMER: ATMOSPHERE_SUMMER,
        Season.AUTUMN: ATMOSPHERE_AUTUMN,
        Season.WINTER: ATMOSPHERE_WINTER,
    }

    @classmethod
    def _get_base_regeneration_logs(cls, location_id: str | None, class_name: str, hp_percent: float) -> list:
        # 1. Critical HP (< 30%): 50% chance for dramatic low-health flavor
        if hp_percent < 0.30 and random.random() < 0.50:
            return [random.choice(cls.REGEN_LOW_HP)]

        # 2. High HP (> 80%): 30% chance for confident flavor
        if hp_percent > 0.80 and random.random() < 0.30:
            return [random.choice(cls.REGEN_HIGH_HP)]

        # 3. Class-Specific Flavor: 30% chance
        if class_name in cls.REGEN_CLASS_PHRASES and random.random() < 0.30:
            return [random.choice(cls.REGEN_CLASS_PHRASES[class_name])]

        # 4. Location-Specific or Generic Fallback
        phrases = cls._LOCATION_REGEN_PHRASES.get(location_id, cls.REGEN_PHRASES)
        return [random.choice(phrases)]

    @classmethod
    def _get_atmospheric_prepend(
        cls,
        location_id: str | None,
        time_phase: TimePhase,
        weather: Weather,
        season: Season | None,
        event_type: str | None,
    ) -> str | None:
        # 40% chance to add an atmospheric intro line
        if random.random() >= 0.40:
            return None

        atmosphere_pool = cls._LOCATION_ATMOSPHERE.get(location_id, cls.ATMOSPHERE_FOREST)

        # Event Override (High Priority)
        if event_type in cls._EVENT_ATMOSPHERE:
            atmosphere_pool = cls._EVENT_ATMOSPHERE[event_type]

        # Time Phase Override (30% chance)
        elif time_phase in cls._TIME_PHASE_ATMOSPHERE and random.random() < 0.3:
            atmosphere_pool = cls._TIME_PHASE_ATMOSPHERE[time_phase]

        # Weather Override (30-50% chance, overrides Time Phase/Location if selected)
        weather_chance = 0.5 if weather in (Weather.STORM, Weather.ASH) else 0.3
        if weather in cls.ATMOSPHERE_WEATHER and random.random() < weather_chance:
            atmosphere_pool = cls.ATMOSPHERE_WEATHER[weather]

        # Seasonal Override (25% chance)
        elif season in cls._SEASONAL_ATMOSPHERE and random.random() < 0.25:
            atmosphere_pool = cls._SEASONAL_ATMOSPHERE[season]

        return random.choice(atmosphere_pool)

    @classmethod
    def regeneration(
        cls,
        location_id: str | None = None,
        class_name: str = "Adventurer",
        hp_percent: float = 1.0,
        time_phase: TimePhase = TimePhase.DAY,
        weather: Weather = Weather.CLEAR,
        season: Season | None = None,
        event_type: str | None = None,
    ) -> list:
        base_logs = cls._get_base_regeneration_logs(location_id, class_name, hp_percent)

        atmospheric_line = cls._get_atmospheric_prepend(location_id, time_phase, weather, season, event_type)
        if atmospheric_line:
            base_logs.insert(0, atmospheric_line)

        return base_logs

    @staticmethod
    def quest_event(objective_type: str, target_name: str) -> str:
        if objective_type == "gather":
            return random.choice(AdventureEvents.GATHER_PHRASES).format(target_name)
        if objective_type == "locate":
            return random.choice(AdventureEvents.LOCATE_PHRASES).format(target_name)
        if objective_type in ("examine", "survey"):
            return random.choice(AdventureEvents.EXAMINE_PHRASES).format(target_name)
        return random.choice(AdventureEvents.FALLBACK_QUEST_PHRASES).format(target_name)

    @staticmethod
    def wild_gather_event(item_name: str) -> str:
        return random.choice(AdventureEvents.WILD_GATHER_PHRASES).format(item_name)

    @staticmethod
    def surge_event() -> str:
        return random.choice(AdventureEvents.SURGE_PHRASES)

    @staticmethod
    def scavenge_event(reward_type: str, amount: int) -> str:
        if reward_type == "aurum":
            return random.choice(AdventureEvents.SCAVENGE_AURUM_PHRASES).format(amount)
        return random.choice(AdventureEvents.SCAVENGE_EXP_PHRASES).format(amount)

    @staticmethod
    def special_event_flavor(event_key: str) -> str:
        if event_key == "safe_room":
            return random.choice(AdventureEvents.SAFE_ROOM_PHRASES)  # nosec B311
        elif event_key == "hidden_stash":
            return random.choice(AdventureEvents.HIDDEN_STASH_PHRASES)  # nosec B311
        elif event_key == "ancient_shrine":
            return random.choice(AdventureEvents.ANCIENT_SHRINE_PHRASES)  # nosec B311
        elif event_key == "trap_pit":
            return random.choice(AdventureEvents.TRAP_PHRASES)  # nosec B311
        return "*A strange event occurs.*"

    @staticmethod
    def no_event_found() -> str:
        return random.choice(AdventureEvents.NO_EVENT_PHRASES)
