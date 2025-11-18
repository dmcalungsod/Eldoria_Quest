"""
quest_data.py

Contains all quest definitions for Eldoria Quest, sorted by tier.
This data is imported by populate_database.py.
"""

import json

# ======================================================================
# F-TIER QUESTS
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
        # --- FIX: Changed "Forest Slime" to "Verdant Slime" and "Glimmer Slime" ---
        json.dumps({"defeat": {"Verdant Slime": 5, "Glimmer Slime": 5}}),
        # --- FIX: Changed item name to match consumables.py ---
        json.dumps({"exp": 45, "aurum": 20, "item": "Dewfall Tonic"}),
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
        # --- FIX: Changed item name to match consumables.py ---
        json.dumps({"exp": 25, "aurum": 10, "item": "Thicket Antidote"}),
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
        json.dumps({"exp": 40, "aurum": 15}),
    ),
    (
        4,
        "A Pest Problem",
        "F",
        "Supply Merchant Doran",
        "Forest Edge",
        "Giant forest rats are tearing into supply crates.",
        "Doran’s shipments have been gnawed open by oversized rodents infused with Veil-sickness. Their boldness grows daily, and his livelihood is at risk. Clear them out before he loses another week’s worth of grain and cloth.",
        # --- FIX: Changed "Forest Rat" to "Goblin Grunt" (since rats don't exist) ---
        json.dumps({"defeat": {"Goblin Grunt": 8}}),
        json.dumps({"exp": 35, "aurum": 18}),
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
        json.dumps({"exp": 20, "aurum": 12}),
    ),
    (
        6,
        "Clear the Campsite",
        "F",
        "Young Explorer Rima",
        "Eastwood Camp",
        "Clear goblins from a campsite Rima wants to use.",
        "Rima, an overly enthusiastic explorer, set up camp deep in goblin-infested brush. Before she can proceed with her “grand expedition,” she needs the area cleared of lurking scavenger goblins.",
        # --- FIX: Changed "Scavenger Goblin" to "Goblin Grunt" ---
        json.dumps({"defeat": {"Goblin Grunt": 5}}),
        json.dumps({"exp": 45, "aurum": 14}),
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
        json.dumps({"exp": 30, "aurum": 10}),
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
        json.dumps({"exp": 20, "aurum": 8}),
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
        # --- FIX: Changed item name to match consumables.py ---
        json.dumps({"exp": 30, "aurum": 10, "item": "Trailman's Ration"}),
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
        json.dumps({"exp": 25, "aurum": 10}),
    ),
]

# ======================================================================
# E-TIER QUESTS
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
        # --- FIX: Changed "Goblin Skirmisher" to "Goblin Scout" ---
        json.dumps({"defeat": {"Goblin Scout": 7}, "retrieve": {"Map Fragment": 1}}),
        json.dumps({"exp": 60, "aurum": 25}),
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
        # --- FIX: Changed item name to match consumables.py ---
        json.dumps({"exp": 55, "aurum": 24, "item": "Thicket Antidote"}),
    ),
    (
        13,
        "Echoes in the Hollow",
        "E",
        "Hermit Sorin",
        "Hollowtree Den",
        "Investigate eerie whispers from a rotten tree cavern.",
        "Travelers claim that the Hollowtree whispers names, luring wanderers closer. Sorin suspects a Veil-born sprite nesting inside. He needs someone who won’t be fooled by its illusions.",
        # --- FIX: Changed "Mischief Sprite" to "Burbling Sprite" ---
        json.dumps({"investigate": "Hollowtree", "defeat": {"Burbling Sprite": 1}}),
        json.dumps({"exp": 70, "aurum": 22}),
    ),
    (
        14,
        "The Lumberjack’s Wrath",
        "E",
        "Lumberjack Bran",
        "Birchfall Path",
        "Eliminate a territorial Treeling.",
        "A sentient sap-creature—the Treeling—has claimed Birchfall Path, harassing workers and smashing tools. Bran asks for aid before the creature’s roots choke out the entire path.",
        # --- FIX: Changed "Treeling" to "Vineling" ---
        json.dumps({"defeat": {"Vineling": 1}}),
        # --- FIX: Changed equipment to a high-value consumable ---
        json.dumps({"exp": 90, "aurum": 28, "item": "Elixir of Verdant Heart"}),
    ),
    (
        15,
        "Shadows Over the Water",
        "E",
        "Fisher Amon",
        "Moonwater Shore",
        "Water spirits are disturbing fishermen.",
        "Moonwater’s surface shimmers even without sun, revealing restless Naiads that drag nets underwater. Amon fears someone will be taken next. He needs protection.",
        # --- FIX: Changed "Moonwater Naiad" to "Fen Wisp" ---
        json.dumps({"defeat": {"Fen Wisp": 3}}),
        json.dumps({"exp": 65, "aurum": 20}),
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
        json.dumps({"exp": 55, "aurum": 30}),
    ),
    (
        17,
        "A Test of Aim",
        "E",
        "Ranger Alyss",
        "Ranger Outpost",
        "Practice combat against agile forest beasts.",
        "Alyss trains new recruits by sending them after Swift-tail Hares—nimble creatures infused with faint forest magic. Catching them tests reflex and precision.",
        # --- FIX: Changed "Swift-tail Hare" to "Gloam Hare" ---
        json.dumps({"defeat": {"Gloam Hare": 5}}),
        # --- FIX: Changed equipment to a consumable ---
        json.dumps({"exp": 50, "aurum": 12, "item": "Runner's Cordial"}),
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
        json.dumps({"exp": 70, "aurum": 26}),
    ),
    (
        19,
        "Spider Nest Purge",
        "E",
        "Guard Captain Rhea",
        "Webwood",
        "Destroy a growing spider nest.",
        "The Webwood’s population of brood spiders has ballooned, stringing webs across traveler roads. Their venom weakens limbs, making escape impossible. Rhea requires an adventurer to thin their numbers.",
        # --- FIX: Changed "Brood Spider" to "Thicket Spider" ---
        json.dumps({"defeat": {"Thicket Spider": 6}}),
        # --- FIX: Changed material to a consumable ---
        json.dumps({"exp": 85, "aurum": 32, "item": "Panacea Root Paste"}),
    ),
    (
        20,
        "Mushroom Menace",
        "E",
        "Gatherer Pim",
        "Sporebrush Patch",
        "Defeat aggressive fungus creatures.",
        "Sporeshrooms have sprouted beyond their usual cycle, animated by warped forest mana. Pim’s harvesting routes are blocked unless these lumbering fungi are cleared.",
        # --- FIX: Changed "Sporeshroom" to "Sporeling" ---
        json.dumps({"defeat": {"Sporeling": 4}}),
        json.dumps({"exp": 80, "aurum": 30}),
    ),
]

# ======================================================================
# D-TIER QUESTS
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
        # --- FIX: Changed "Goblin Lieutenant Krag" to "Bramble Goblin" (a tougher goblin) ---
        json.dumps({"defeat": {"Bramble Goblin": 1}}),
        json.dumps({"exp": 120, "aurum": 55, "item": "Captains' Ale (Embolden)"}),  # Fixed item
    ),
    (
        22,
        "Forest Spirit in Pain",
        "D",
        "Druidess Leira",
        "Heartwood Glade",
        "Aid a wounded forest spirit.",
        "A Heartwood Sprite has been corrupted by a splinter of Veil energy lodged in its body. Leira believes an adventurer with a steady hand can help remove it—if they can survive its thrashing.",
        # --- FIX: Changed "Sprite" to "Wisp-Sentinel" ---
        json.dumps({"subdue": "Wisp-Sentinel", "remove": "Veil Splinter"}),
        json.dumps({"exp": 110, "aurum": 40, "item": "Sap of Renewal"}),  # Fixed item
    ),
    (
        23,
        "Hunt the Moonfang Wolf",
        "D",
        "Hunter Yorin",
        "Moonfang Den",
        "Hunt a powerful forest wolf touched by moonlight.",
        "The Moonfang Wolf is a silver-coated predator that leads lesser wolves with eerie discipline. Yorin fears it will turn its pack upon the village unless someone challenges it.",
        # --- FIX: Changed "Moonfang Wolf" to "Ridge Wolf" ---
        json.dumps({"defeat": {"Ridge Wolf": 1}}),
        json.dumps({"exp": 150, "aurum": 60, "item": "Glade Salve Vial"}),  # Fixed item
    ),
    (
        24,
        "Entangled Roots",
        "D",
        "Woodsman Eddan",
        "Rootcoil Valley",
        "Destroy corrupted root-beasts.",
        "Tanglesap Creatures—animated roots—have begun striking at loggers. Their claws are formed of hardened bark and their bodies pulse with sickly green glow.",
        # --- FIX: Changed "Tanglesap Creature" to "Young Treant" ---
        json.dumps({"defeat": {"Young Treant": 3}}),
        json.dumps({"exp": 100, "aurum": 30}),
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
        json.dumps({"exp": 90, "aurum": 25}),
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
        json.dumps({"exp": 100, "aurum": 35, "item": "Lunaris Tonic"}),  # Fixed item
    ),
    (
        27,
        "Cleanse the Shrine",
        "D",
        "Shrine Keeper Mara",
        "Moonshadow Shrine",
        "Purify a shrine corrupted by Veil energy.",
        "The Moonshadow Shrine’s white stones have turned black-veined, its pool reflecting horrors instead of moonlight. Mara needs an adventurer to drive off the wraithlings haunting it.",
        # --- FIX: Changed "Wraithling" to "Rookwood Shade" ---
        json.dumps({"defeat": {"Rookwood Shade": 5}, "use": "Purification Amulet"}),
        json.dumps({"exp": 130, "aurum": 45, "item": "Wardkeeper's Vial"}),  # Fixed item
    ),
    (
        28,
        "The Spider Matron",
        "D",
        "Guard Captain Rhea",
        "Webwood Nest",
        "Hunt the matriarch of the spider colony.",
        "The brood spiders answer to a single massive mother whose venom sacs can rot bark. Her growing brood threatens to spread beyond Webwood entirely.",
        # --- FIX: Changed "Spider Matron Vesska" to "Thicket Spider" (just more of them) ---
        json.dumps({"defeat": {"Thicket Spider": 10}}),
        json.dumps({"exp": 160, "aurum": 70, "item": "Panacea Root Paste"}),  # Fixed item
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
        json.dumps({"exp": 85, "aurum": 30}),
    ),
    (
        30,
        "The Whispering Oak",
        "D",
        "Druidess Leira",
        "Whispering Oak Circle",
        "Investigate a sacred tree murmuring with corrupted voices.",
        "The Whispering Oak, ancient guardian of the forest, has begun muttering in tones unlike any druidic language. Leira suspects an unseen parasite clinging to its bark—one born of the Veil.",
        # --- FIX: Changed "Oak Parasite" to "Pine Wight" ---
        json.dumps({"inspect": "Oak", "defeat": {"Pine Wight": 1}}),
        json.dumps({"exp": 140, "aurum": 50, "item": "Luck-Blessed Cordial"}),  # Fixed item
    ),
]


# ======================================================================
# COMBINED LIST FOR POPULATOR
# ======================================================================
ALL_QUESTS = QUESTS_F_TIER + QUESTS_E_TIER + QUESTS_D_TIER
