"""
quest_data.py

Contains all quest definitions for Eldoria Quest, sorted by tier.
REBALANCED: Rewards significantly increased to match the steep leveling curve.
"""

import json

# ======================================================================
# F-TIER QUESTS (Level 1-5)
# ======================================================================
QUESTS_F_TIER = [
    (
        1,
        "Culling the Slimes",
        "F",
        "Farmer Tallen",
        "Willowcreek Outskirts",
        "Slimes are devouring crops and farm tools.",
        "Moisture from the Broken Veil has thickened the forest air, spawning an abnormal number of Forest Slimes. Farmer Tallen’s fields have become a slow-moving tide of gelatinous pests. He seeks someone willing to drive them back before planting season is ruined.",
        json.dumps({"defeat": {"Verdant Slime": 5, "Glimmer Slime": 5}}),
        # OLD: 45 XP / 20 G
        # NEW: 250 XP / 60 G + Item
        json.dumps({"exp": 250, "aurum": 60, "item": "Dewfall Tonic"}),
    ),
    (
        2,
        "Gathering Healing Herbs",
        "F",
        "Herbalist Mirra",
        "Whispering Thicket",
        "The local healer needs fresh medicinal plants.",
        "The Whispering Thicket grows herbs found nowhere else, especially Moonleaf—gleaming silver leaves used to treat fevers. With monsters stirring, Mirra can’t safely gather them herself. She requests an adventurer to harvest the plants before night-dew poisons their potency.",
        json.dumps({"gather": {"Moonleaf Herb": 5}}),
        # OLD: 25 XP / 10 G
        # NEW: 200 XP / 45 G
        json.dumps({"exp": 200, "aurum": 45, "item": "Thicket Antidote"}),
    ),
    (
        3,
        "Lost Child of the Creek",
        "F",
        "Guard Orlin",
        "Willowcreek",
        "A villager’s child wandered into the forest.",
        "A young girl, Lina, chased her pet sprite into the treeline and never returned. The local guard is stretched thin and needs someone swift to search the nearby clearings. Time is short—nightfall brings predators hungrier than wolves.",
        json.dumps({"locate": "Lina", "escort": "Lina"}),
        # NEW: 300 XP / 75 G
        json.dumps({"exp": 300, "aurum": 75}),
    ),
    (
        4,
        "A Pest Problem",
        "F",
        "Supply Merchant Doran",
        "Forest Edge",
        "Giant forest rats are tearing into supply crates.",
        "Doran’s shipments have been gnawed open by oversized rodents infused with Veil-sickness. Their boldness grows daily, and his livelihood is at risk. Clear them out before he loses another week’s worth of grain and cloth.",
        json.dumps({"defeat": {"Goblin Grunt": 8}}),
        # NEW: 275 XP / 65 G
        json.dumps({"exp": 275, "aurum": 65}),
    ),
    (
        5,
        "Timber Run",
        "F",
        "Carpenter Elwin",
        "Lumberjack’s Road",
        "Deliver chopped timber to Willowcreek.",
        "Travelers fear the woodland paths at dusk, forcing Elwin’s workers to abandon their supply of freshly cut lumber. The carpenter needs someone resilient enough to haul the materials before thieves or creatures steal them away.",
        json.dumps({"transport": {"Timber Bundle": 1}}),
        # NEW: 150 XP / 90 G (High gold for labor)
        json.dumps({"exp": 150, "aurum": 90}),
    ),
    (
        6,
        "Clear the Campsite",
        "F",
        "Young Explorer Rima",
        "Eastwood Camp",
        "Clear goblins from a campsite Rima wants to use.",
        "Rima, an overly enthusiastic explorer, set up camp deep in goblin-infested brush. Before she can proceed with her “grand expedition,” she needs the area cleared of lurking scavenger goblins.",
        json.dumps({"defeat": {"Goblin Grunt": 5}}),
        # NEW: 225 XP / 50 G
        json.dumps({"exp": 225, "aurum": 50}),
    ),
    (
        7,
        "Strange Tracks",
        "F",
        "Hunter Yorin",
        "North Ferntrail",
        "Investigate unusual beast tracks near town.",
        "Claw marks and hoofprints twisted by corruption have appeared near the northern trail. Yorin suspects a malformed creature but needs confirmation from someone willing to venture deeper.",
        json.dumps({"examine": {"Track Sites": 3}, "report_to": "Hunter Yorin"}),
        # NEW: 200 XP / 45 G
        json.dumps({"exp": 200, "aurum": 45}),
    ),
    (
        8,
        "Lantern Delivery",
        "F",
        "Shopkeeper Helia",
        "Willowcreek",
        "Deliver lanterns to patrolling guards.",
        "With fog thickening earlier each day, sentries require new lanterns to maintain visibility. Highwaymen have grown bold at dusk, so the guards depend on timely supply delivery.",
        json.dumps({"deliver": {"Lanterns": 3}}),
        # NEW: 150 XP / 40 G
        json.dumps({"exp": 150, "aurum": 40}),
    ),
    (
        9,
        "A Meal for the Road",
        "F",
        "Innkeeper Vero",
        "Cranelight Inn",
        "Gather ingredients for travel rations.",
        "Vero’s inn prepares provisions for those venturing into the forest. He needs fresh mushroom caps and forest berries, both of which grow near shallow cave mouths—often watched by lurking slimes.",
        json.dumps({"collect": {"Cavecap Mushroom": 4, "Wild Berry": 3}}),
        # NEW: 220 XP / 45 G
        json.dumps({"exp": 220, "aurum": 45, "item": "Trailman's Ration"}),
    ),
    (
        10,
        "The Broken Snare",
        "F",
        "Trapper Dane",
        "Southwood",
        "Retrieve parts from damaged animal traps.",
        "Dane’s metal snares were shattered, bent by something far stronger than wolves. He wishes to salvage what remains before it rusts or is stolen by goblins.",
        json.dumps({"retrieve": {"Trap Springs": 3}}),
        # NEW: 180 XP / 55 G
        json.dumps({"exp": 180, "aurum": 55}),
    ),
]

# ======================================================================
# E-TIER QUESTS (Level 5-10)
# ======================================================================
QUESTS_E_TIER = [
    (
        11,
        "Goblin Skirmishers",
        "E",
        "Guard Captain Rhea",
        "Eastern Forest",
        "Goblins are organizing raids.",
        "For the first time in seasons, goblins have formed war skirmishes. Their scouts have been spotted mapping forest paths—an alarming sign of future raids. Rhea needs swift action before these pests grow bold enough to strike Willowcreek.",
        json.dumps({"defeat": {"Goblin Scout": 7}, "retrieve": {"Map Fragment": 1}}),
        # OLD: 60 XP / 25 G
        # NEW: 450 XP / 120 G
        json.dumps({"exp": 450, "aurum": 120}),
    ),
    (
        12,
        "Venom in the Roots",
        "E",
        "Apothecary Lune",
        "Deepgrove Roots",
        "Collect venom samples from poisonous snakes.",
        "Strange serpents have slithered into the grove, their fangs dripping an iridescent toxin unseen since before the Sundering. Lune hopes to refine an antidote—but only if someone brings her samples.",
        json.dumps({"collect": {"Serpent Venom": 3}}),
        # NEW: 400 XP / 100 G
        json.dumps({"exp": 400, "aurum": 100, "item": "Thicket Antidote"}),
    ),
    (
        13,
        "Echoes in the Hollow",
        "E",
        "Hermit Sorin",
        "Hollowtree Den",
        "Investigate eerie whispers from a rotten tree cavern.",
        "Travelers claim that the Hollowtree whispers names, luring wanderers closer. Sorin suspects a Veil-born sprite nesting inside. He needs someone who won’t be fooled by its illusions.",
        json.dumps({"investigate": "Hollowtree", "defeat": {"Burbling Sprite": 1}}),
        # NEW: 500 XP / 140 G
        json.dumps({"exp": 500, "aurum": 140}),
    ),
    (
        14,
        "The Lumberjack’s Wrath",
        "E",
        "Lumberjack Bran",
        "Birchfall Path",
        "Eliminate a territorial Treeling.",
        "A sentient sap-creature—the Treeling—has claimed Birchfall Path, harassing workers and smashing tools. Bran asks for aid before the creature’s roots choke out the entire path.",
        json.dumps({"defeat": {"Vineling": 1}}),
        # NEW: 600 XP / 180 G
        json.dumps({"exp": 600, "aurum": 180, "item": "Elixir of Verdant Heart"}),
    ),
    (
        15,
        "Shadows Over the Water",
        "E",
        "Fisher Amon",
        "Moonwater Shore",
        "Water spirits are disturbing fishermen.",
        "Moonwater’s surface shimmers even without sun, revealing restless Naiads that drag nets underwater. Amon fears someone will be taken next. He needs protection.",
        json.dumps({"defeat": {"Fen Wisp": 3}}),
        # NEW: 420 XP / 90 G
        json.dumps({"exp": 420, "aurum": 90}),
    ),
    (
        16,
        "Broken Idol Pieces",
        "E",
        "Traveling Scholar Firren",
        "Mossdeep Trail",
        "Recover fragments of an ancient forest idol.",
        "Goblins shattered a woodland idol to steal its gemstones. Firren wishes to reassemble the relic before its latent magic spills into the wild.",
        json.dumps({"retrieve": {"Idol Fragments": 4}}),
        # NEW: 380 XP / 130 G
        json.dumps({"exp": 380, "aurum": 130}),
    ),
    (
        17,
        "A Test of Aim",
        "E",
        "Ranger Alyss",
        "Ranger Outpost",
        "Practice combat against agile forest beasts.",
        "Alyss trains new recruits by sending them after Swift-tail Hares—nimble creatures infused with faint forest magic. Catching them tests reflex and precision.",
        json.dumps({"defeat": {"Gloam Hare": 5}}),
        # NEW: 350 XP / 60 G
        json.dumps({"exp": 350, "aurum": 60, "item": "Runner's Cordial"}),
    ),
    (
        18,
        "The Missing Courier",
        "E",
        "Town Hall",
        "Northern Road",
        "Find a courier who vanished en route to Willowcreek.",
        "A forest courier carrying urgent correspondence never arrived. Tracks suggest he was chased off-road by beasts. His satchel holds valuable village contracts.",
        json.dumps({"find": "Courier", "retrieve": "Mail Satchel"}),
        # NEW: 450 XP / 100 G
        json.dumps({"exp": 450, "aurum": 100}),
    ),
    (
        19,
        "Spider Nest Purge",
        "E",
        "Guard Captain Rhea",
        "Webwood",
        "Destroy a growing spider nest.",
        "The Webwood’s population of brood spiders has ballooned, stringing webs across traveler roads. Their venom weakens limbs, making escape impossible. Rhea requires an adventurer to thin their numbers.",
        json.dumps({"defeat": {"Thicket Spider": 6}}),
        # NEW: 550 XP / 150 G
        json.dumps({"exp": 550, "aurum": 150, "item": "Panacea Root Paste"}),
    ),
    (
        20,
        "Mushroom Menace",
        "E",
        "Gatherer Pim",
        "Sporebrush Patch",
        "Defeat aggressive fungus creatures.",
        "Sporeshrooms have sprouted beyond their usual cycle, animated by warped forest mana. Pim’s harvesting routes are blocked unless these lumbering fungi are cleared.",
        json.dumps({"defeat": {"Sporeling": 4}}),
        # NEW: 500 XP / 130 G
        json.dumps({"exp": 500, "aurum": 130}),
    ),
]

# ======================================================================
# D-TIER QUESTS (Level 10-15)
# ======================================================================
QUESTS_D_TIER = [
    (
        21,
        "The Goblin Lieutenant",
        "D",
        "Guard Captain Rhea",
        "Ruined Camp",
        "Take down a goblin commander.",
        "A cunning goblin lieutenant has unified several scattered tribes. His camp rings with stolen steel and crude banners. If left unchecked, an organized horde might rise.",
        json.dumps({"defeat": {"Bramble Goblin": 1}}),
        # OLD: 120 XP / 55 G
        # NEW: 800 XP / 300 G
        json.dumps({"exp": 800, "aurum": 300, "item": "Captains' Ale (Embolden)"}),
    ),
    (
        22,
        "Forest Spirit in Pain",
        "D",
        "Druidess Leira",
        "Heartwood Glade",
        "Aid a wounded forest spirit.",
        "A Heartwood Sprite has been corrupted by a splinter of Veil energy lodged in its body. Leira believes an adventurer with a steady hand can help remove it—if they can survive its thrashing.",
        json.dumps({"subdue": "Wisp-Sentinel", "remove": "Veil Splinter"}),
        # NEW: 750 XP / 250 G
        json.dumps({"exp": 750, "aurum": 250, "item": "Sap of Renewal"}),
    ),
    (
        23,
        "Hunt the Moonfang Wolf",
        "D",
        "Hunter Yorin",
        "Moonfang Den",
        "Hunt a powerful forest wolf touched by moonlight.",
        "The Moonfang Wolf is a silver-coated predator that leads lesser wolves with eerie discipline. Yorin fears it will turn its pack upon the village unless someone challenges it.",
        json.dumps({"defeat": {"Ridge Wolf": 1}}),
        # NEW: 900 XP / 350 G
        json.dumps({"exp": 900, "aurum": 350, "item": "Glade Salve Vial"}),
    ),
    (
        24,
        "Entangled Roots",
        "D",
        "Woodsman Eddan",
        "Rootcoil Valley",
        "Destroy corrupted root-beasts.",
        "Tanglesap Creatures—animated roots—have begun striking at loggers. Their claws are formed of hardened bark and their bodies pulse with sickly green glow.",
        json.dumps({"defeat": {"Young Treant": 3}}),
        # NEW: 700 XP / 200 G
        json.dumps({"exp": 700, "aurum": 200}),
    ),
    (
        25,
        "Signs of the First Boss (Thornhide Bear)",
        "D",
        "Guard Captain Rhea",
        "Western Deepwood",
        "Scout territory of the Thornhide Bear.",
        "Massive claw marks and uprooted trees mark the hunting grounds of Thornhide—the first of the forest’s three boss creatures. Before a slaying party mobilizes, Rhea needs precise scouting intel.",
        json.dumps({"survey": {"Bear Signs": 3}, "report_to": "Guard Captain Rhea"}),
        # NEW: 650 XP / 180 G
        json.dumps({"exp": 650, "aurum": 180}),
    ),
    (
        26,
        "A Merchant in Tears",
        "D",
        "Merchant Salvi",
        "Bramble Road",
        "Recover stolen trade goods.",
        "Bandit-goblins ambushed Salvi and fled into the thicket with his fabrics and spices. The merchant begs someone to reclaim the goods before the creatures burn or eat them.",
        json.dumps({"recover": {"Trade Crates": 5}}),
        # NEW: 750 XP / 250 G
        json.dumps({"exp": 750, "aurum": 250, "item": "Lunaris Tonic"}),
    ),
    (
        27,
        "Cleanse the Shrine",
        "D",
        "Shrine Keeper Mara",
        "Moonshadow Shrine",
        "Purify a shrine corrupted by Veil energy.",
        "The Moonshadow Shrine’s white stones have turned black-veined, its pool reflecting horrors instead of moonlight. Mara needs an adventurer to drive off the wraithlings haunting it.",
        json.dumps({"defeat": {"Rookwood Shade": 5}, "use": "Purification Amulet"}),
        # NEW: 850 XP / 280 G
        json.dumps({"exp": 850, "aurum": 280, "item": "Wardkeeper's Vial"}),
    ),
    (
        28,
        "The Spider Matron",
        "D",
        "Guard Captain Rhea",
        "Webwood Nest",
        "Hunt the matriarch of the spider colony.",
        "The brood spiders answer to a single massive mother whose venom sacs can rot bark. Her growing brood threatens to spread beyond Webwood entirely.",
        json.dumps({"defeat": {"Thicket Spider": 10}}),
        # NEW: 1000 XP / 400 G
        json.dumps({"exp": 1000, "aurum": 400, "item": "Panacea Root Paste"}),
    ),
    (
        29,
        "Before the Storm",
        "D",
        "Town Hall Council",
        "Willowcreek",
        "Prepare the town for coming threats.",
        "The council fears an impending surge of monsters, driven outward by the forest bosses awakening. They require supplies gathered and warnings spread to outlying homes.",
        json.dumps({"deliver": {"Warning Notices": 3}, "bring": {"Supply Sacks": 2}}),
        # NEW: 600 XP / 150 G
        json.dumps({"exp": 600, "aurum": 150}),
    ),
    (
        30,
        "The Whispering Oak",
        "D",
        "Druidess Leira",
        "Whispering Oak Circle",
        "Investigate a sacred tree murmuring with corrupted voices.",
        "The Whispering Oak, ancient guardian of the forest, has begun muttering in tones unlike any druidic language. Leira suspects an unseen parasite clinging to its bark—one born of the Veil.",
        json.dumps({"inspect": "Oak", "defeat": {"Pine Wight": 1}}),
        # NEW: 950 XP / 320 G
        json.dumps({"exp": 950, "aurum": 320, "item": "Luck-Blessed Cordial"}),
    ),
]

# ======================================================================
# C-TIER QUESTS (Level 15-20)
# ======================================================================
QUESTS_C_TIER = [
    (
        31,
        "Storm Warning",
        "C",
        "Weather-Watcher Jace",
        "The Shrouded Fen",
        "Suppress the rising number of Stormlings.",
        "Stormlings are crackling with unusual intensity, threatening to spark wildfires despite the damp. Jace needs them thinned out before the static charge becomes a lightning storm.",
        json.dumps({"defeat": {"Stormling": 8}}),
        json.dumps({"exp": 1200, "aurum": 350}),
    ),
    (
        32,
        "Mire Dredging",
        "C",
        "Blacksmith Gorn",
        "The Shrouded Fen",
        "Gather Iron Ore from the Fen.",
        "Gorn claims the iron found in the fen is tempered by the constant magical storms. He needs a fresh supply to forge weapons capable of piercing elite hides.",
        json.dumps({"gather": {"Iron Ore": 6}}),
        json.dumps({"exp": 1100, "aurum": 400}),
    ),
    (
        33,
        "Shadows in the Mist",
        "C",
        "Scout Valen",
        "The Shrouded Fen",
        "Hunt the elusive Dusklings.",
        "Dusklings use the fog to ambush patrols. Valen needs an adventurer to turn the tables and hunt the hunters.",
        json.dumps({"defeat": {"Duskling": 5}}),
        json.dumps({"exp": 1300, "aurum": 450}),
    ),
    (
        34,
        "The Lost Patrol",
        "C",
        "Captain Rhea",
        "The Shrouded Fen",
        "Locate the missing patrol unit.",
        "A squad sent to map the fen has gone silent. Rhea fears they've been led astray by wisps. Find them before the bog claims them forever.",
        json.dumps({"locate": "Missing Squad"}),
        json.dumps({"exp": 1250, "aurum": 300}),
    ),
    (
        35,
        "Essence of Decay",
        "C",
        "Alchemist Miral",
        "The Shrouded Fen",
        "Defeat Mire Lurkers for their essence.",
        "The slime of a Mire Lurker is potent but volatile. Miral needs samples fresh from the source to stabilize her latest brew.",
        json.dumps({"defeat": {"Mire Lurker": 6}}),
        json.dumps({"exp": 1150, "aurum": 380, "item": "Thicket Antidote"}),
    ),
    (
        36,
        "Revenant's Curse",
        "C",
        "Priestess Elara",
        "The Shrouded Fen",
        "Put Fen Revenants to rest.",
        "The restless dead in the fen are rising as Revenants. Elara asks you to grant them peace with steel and spell.",
        json.dumps({"defeat": {"Fen Revenant": 4}}),
        json.dumps({"exp": 1400, "aurum": 500, "item": "Dewfall Tonic"}),
    ),
    (
        37,
        "Ancient Wood Harvest",
        "C",
        "Carpenter Elwin",
        "The Shrouded Fen",
        "Gather Ancient Wood.",
        "The petrified wood of the fen is harder than stone. Elwin needs it for reinforcing the town gates.",
        json.dumps({"gather": {"Ancient Wood": 5}}),
        json.dumps({"exp": 1100, "aurum": 420}),
    ),
    (
        38,
        "The Glade Empress",
        "C",
        "Guildmaster Kael",
        "The Shrouded Fen",
        "Slay the Glade Empress.",
        "The corrupted heart of the fen has manifested as the Glade Empress. Her rule spreads rot. End her reign.",
        json.dumps({"defeat": {"Glade Empress": 1}}),
        json.dumps({"exp": 2500, "aurum": 1000, "item": "Magic Stone (Large)"}),
    ),
    (
        39,
        "Survey the Ruins",
        "C",
        "Historian Arin",
        "The Shrouded Fen",
        "Survey the sunken ruins.",
        "Old ruins have surfaced in the mire. Arin needs a sketch of the inscriptions before they sink again.",
        json.dumps({"survey": {"Sunken Inscriptions": 3}}),
        json.dumps({"exp": 1200, "aurum": 350}),
    ),
    (
        40,
        "Wisp Hunt",
        "C",
        "Mage Lyra",
        "The Shrouded Fen",
        "Disperse Wisp-Sentinels.",
        "The Wisp-Sentinels are coordinating the fen's defenses. Blind the enemy by removing their eyes.",
        json.dumps({"defeat": {"Wisp-Sentinel": 3}}),
        json.dumps({"exp": 1350, "aurum": 450}),
    ),
]

ALL_QUESTS = QUESTS_F_TIER + QUESTS_E_TIER + QUESTS_D_TIER + QUESTS_C_TIER
