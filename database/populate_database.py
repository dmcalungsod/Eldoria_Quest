"""
populate_database.py

Loads data from the game dictionary modules and inserts them into EQ_Game.db.
Run this AFTER running create_database.py to create the schema.

Expected modules:
- monsters (MONSTERS dict)
- quest_items (QUEST_ITEMS dict)
- consumables (CONSUMABLES dict)
- equipments (EQUIPMENTS dict)
- class_equipments (CLASS_EQUIPMENTS dict, CLASS_SETS dict)

If you placed those modules in a package folder (e.g. 'systems'), either:
- run this script from that parent so imports work, or
- adjust the import paths accordingly.
"""

import sqlite3
import json
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DB = "EQ_Game.db"

# Attempt imports from the game_systems.data package
try:
    from game_systems.data import monsters
    from game_systems.data import quest_items
    from game_systems.data import consumables
    from game_systems.data import equipments
    from game_systems.data import class_equipments
except ImportError as e:
    print("Failed to import data modules from 'game_systems/data'.")
    print("Please ensure you are running this script from the root of the project.")
    print("Import error:", e)
    sys.exit(1)


from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS

# ... (rest of the imports)

# Basic classes to insert
# This is now handled by the insert_classes function below

def insert_classes(conn):
    cur = conn.cursor()
    print("Inserting classes...")
    
    classes_to_insert = []
    for name, data in CLASS_DEFINITIONS.items():
        classes_to_insert.append((data['id'], name, data['description']))

    cur.executemany("INSERT OR IGNORE INTO classes (id, name, description) VALUES (?, ?, ?);", classes_to_insert)
    conn.commit()


def insert_monsters(conn):
    cur = conn.cursor()
    print("Inserting monsters...")
    for key, m in monsters.MONSTERS.items():
        name = m.get("name")
        description = m.get("description", "")
        tier = m.get("tier", "Normal")
        level = int(m.get("level", 1))
        hp = int(m.get("hp", 1))
        attack = int(m.get("atk", 1))
        defense = int(m.get("def", 0))
        dex = int(m.get("dex", 0)) if "dex" in m else level  # fallback
        magic = int(m.get("magic", 0)) if "magic" in m else 0
        gold = int(max(1, level * 3))
        xp = int(m.get("xp", max(1, level * 5)))
        biome = m.get("biome", "Forest")

        cur.execute("""
            INSERT INTO monsters (name, description, tier, level, hp, attack, defense, dexterity, magic, gold_drop, exp_drop, biome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, tier, level, hp, attack, defense, dex, magic, gold, xp, biome))

    conn.commit()


def insert_quest_items(conn):
    cur = conn.cursor()
    print("Inserting quest items...")
    for key, q in quest_items.QUEST_ITEMS.items():
        name = q.get("name")
        description = q.get("notes", q.get("description", ""))
        rarity = q.get("rarity", "Common")
        value = q.get("value", 0)
        # quest_id left null for now
        cur.execute("""
            INSERT INTO quest_items (name, description, rarity, quest_id, value)
            VALUES (?, ?, ?, NULL, ?)
        """, (name, description, rarity, value))
    conn.commit()


def insert_consumables(conn):
    cur = conn.cursor()
    print("Inserting consumables...")
    for key, c in consumables.CONSUMABLES.items():
        name = c.get("name")
        description = c.get("description", "")
        rarity = c.get("rarity", "Common")
        effect = json.dumps(c.get("effect", {}))
        value = c.get("value", 0)
        cur.execute("""
            INSERT INTO consumables (name, description, rarity, effect, value)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, rarity, effect, value))
    conn.commit()


def insert_equipments(conn):
    cur = conn.cursor()
    print("Inserting general equipments...")
    for key, e in equipments.EQUIPMENTS.items():
        name = e.get("name")
        description = e.get("description", "")
        rarity = e.get("rarity", "Common")
        slot = e.get("slot", "accessory")
        stats = e.get("stats_bonus", {})
        str_b = stats.get("STR", 0)
        dex_b = stats.get("DEX", 0)
        con_b = stats.get("CON", 0)
        int_b = stats.get("INT", 0)
        wis_b = stats.get("WIS", 0)
        cha_b = stats.get("CHA", 0)
        lck_b = stats.get("LCK", 0)
        min_level = e.get("level_req", 1)

        cur.execute("""
            INSERT INTO equipment (name, description, rarity, slot,
                                   str_bonus, dex_bonus, con_bonus, int_bonus,
                                   wis_bonus, cha_bonus, lck_bonus, min_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, rarity, slot, str_b, dex_b, con_b, int_b, wis_b, cha_b, lck_b, min_level))
    conn.commit()


def insert_class_equipments(conn):
    cur = conn.cursor()
    print("Inserting class-specific equipment...")
    # CLASS_EQUIPMENTS and CLASS_SETS
    # First, if CLASS_SETS available, insert into item_sets
    try:
        class_sets = getattr(class_equipments, "CLASS_SETS", {})
        if class_sets:
            print("Inserting item sets...")
            for set_name, meta in class_sets.items():
                bonus_desc = json.dumps(meta.get("set_bonus", {}))
                cur.execute("INSERT INTO item_sets (set_name, bonus_description) VALUES (?, ?)", (set_name, bonus_desc))
            conn.commit()
    except Exception:
        pass

    # Now insert class equipment rows
    for key, ce in class_equipments.CLASS_EQUIPMENTS.items():
        cls = ce.get("class")
        # Map class name to id (Warrior=1, Mage=2, Rogue=3, Cleric=4, Ranger=5)
        class_map = {"Warrior": 1, "Mage": 2, "Rogue": 3, "Cleric": 4, "Ranger": 5}
        class_id = class_map.get(cls, 0)
        name = ce.get("name")
        description = ce.get("description", "")
        rarity = ce.get("rarity", "Common")
        slot = ce.get("slot", "accessory")
        stats = ce.get("stats_bonus", {})
        str_b = stats.get("STR", 0)
        dex_b = stats.get("DEX", 0)
        con_b = stats.get("CON", 0)
        int_b = stats.get("INT", 0)
        wis_b = stats.get("WIS", 0)
        cha_b = stats.get("CHA", 0)
        lck_b = stats.get("LCK", 0)
        set_name = ce.get("set")
        min_level = ce.get("level_req", ce.get("min_level", 1))

        cur.execute("""
            INSERT INTO class_equipment (class_id, name, description, rarity, slot,
                                         str_bonus, dex_bonus, con_bonus, int_bonus,
                                         wis_bonus, cha_bonus, lck_bonus, set_name, min_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (class_id, name, description, rarity, slot,
              str_b, dex_b, con_b, int_b, wis_b, cha_b, lck_b, set_name, min_level))
    conn.commit()


def insert_quests(conn):
    cur = conn.cursor()
    print("Inserting quests...")
    
    quests_to_insert = [
        (1, "Culling the Slimes", "F", "Farmer Tallen", "Willowcreek Outskirts", "Slimes are devouring crops and farm tools.", 
         "Moisture from the Broken Veil has thickened the forest air, spawning an abnormal number of Forest Slimes. Farmer Tallen’s fields have become a slow-moving tide of gelatinous pests. He seeks someone willing to drive them back before planting season is ruined.",
         json.dumps({"defeat": {"Forest Slime": 10}, "collect": {"Residual Core": 3}}), 
         json.dumps({"exp": 45, "gold": 20, "item": "Minor Healing Draught"})),
        (2, "Gathering Healing Herbs", "F", "Herbalist Mirra", "Whispering Thicket", "The local healer needs fresh medicinal plants.",
         "The Whispering Thicket grows herbs found nowhere else, especially Moonleaf—gleaming silver leaves used to treat fevers. With monsters stirring, Mirra can’t safely gather them herself. She requests an adventurer to harvest the plants before night-dew poisons their potency.",
         json.dumps({"gather": {"Moonleaf Herb": 5}}),
         json.dumps({"exp": 25, "gold": 10, "item": "Herbal Salve"})),
        (3, "Lost Child of the Creek", "F", "Guard Orlin", "Willowcreek", "A villager’s child wandered into the forest.",
         "A young girl, Lina, chased her pet sprite into the treeline and never returned. The local guard is stretched thin and needs someone swift to search the nearby clearings. Time is short—nightfall brings predators hungrier than wolves.",
         json.dumps({"locate": "Lina", "escort": "Lina"}),
         json.dumps({"exp": 40, "gold": 15})),
        (4, "A Pest Problem", "F", "Supply Merchant Doran", "Forest Edge", "Giant forest rats are tearing into supply crates.",
         "Doran’s shipments have been gnawed open by oversized rodents infused with Veil-sickness. Their boldness grows daily, and his livelihood is at risk. Clear them out before he loses another week’s worth of grain and cloth.",
         json.dumps({"defeat": {"Forest Rat": 8}}),
         json.dumps({"exp": 35, "gold": 18})),
        (5, "Timber Run", "F", "Carpenter Elwin", "Lumberjack’s Road", "Deliver chopped timber to Willowcreek.",
         "Travelers fear the woodland paths at dusk, forcing Elwin’s workers to abandon their supply of freshly cut lumber. The carpenter needs someone resilient enough to haul the materials before thieves or creatures steal them away.",
         json.dumps({"transport": {"Timber Bundle": 1}}),
         json.dumps({"exp": 20, "gold": 12})),
        (6, "Clear the Campsite", "F", "Young Explorer Rima", "Eastwood Camp", "Clear goblins from a campsite Rima wants to use.",
         "Rima, an overly enthusiastic explorer, set up camp deep in goblin-infested brush. Before she can proceed with her “grand expedition,” she needs the area cleared of lurking scavenger goblins.",
         json.dumps({"defeat": {"Scavenger Goblin": 5}}),
         json.dumps({"exp": 45, "gold": 14})),
        (7, "Strange Tracks", "F", "Hunter Yorin", "North Ferntrail", "Investigate unusual beast tracks near town.",
         "Claw marks and hoofprints twisted by corruption have appeared near the northern trail. Yorin suspects a malformed creature but needs confirmation from someone willing to venture deeper.",
         json.dumps({"examine": {"Track Sites": 3}, "report_to": "Hunter Yorin"}),
         json.dumps({"exp": 30, "gold": 10})),
        (8, "Lantern Delivery", "F", "Shopkeeper Helia", "Willowcreek", "Deliver lanterns to patrolling guards.",
         "With fog thickening earlier each day, sentries require new lanterns to maintain visibility. Highwaymen have grown bold at dusk, so the guards depend on timely supply delivery.",
         json.dumps({"deliver": {"Lanterns": 3}}),
         json.dumps({"exp": 20, "gold": 8})),
        (9, "A Meal for the Road", "F", "Innkeeper Vero", "Cranelight Inn", "Gather ingredients for travel rations.",
         "Vero’s inn prepares provisions for those venturing into the forest. He needs fresh mushroom caps and forest berries, both of which grow near shallow cave mouths—often watched by lurking slimes.",
         json.dumps({"collect": {"Cavecap Mushroom": 4, "Wild Berry": 3}}),
         json.dumps({"exp": 30, "gold": 10, "item": "Small Stamina Snack"})),
        (10, "The Broken Snare", "F", "Trapper Dane", "Southwood", "Retrieve parts from damaged animal traps.",
          "Dane’s metal snares were shattered, bent by something far stronger than wolves. He wishes to salvage what remains before it rusts or is stolen by goblins.",
          json.dumps({"retrieve": {"Trap Springs": 3}}),
          json.dumps({"exp": 25, "gold": 10})),
        (11, "Goblin Skirmishers", "E", "Guard Captain Rhea", "Eastern Forest", "Goblins are organizing raids.",
          "For the first time in seasons, goblins have formed war skirmishes. Their scouts have been spotted mapping forest paths—an alarming sign of future raids. Rhea needs swift action before these pests grow bold enough to strike Willowcreek.",
          json.dumps({"defeat": {"Goblin Skirmisher": 7}, "retrieve": {"Map Fragment": 1}}),
          json.dumps({"exp": 60, "gold": 25})),
        (12, "Venom in the Roots", "E", "Apothecary Lune", "Deepgrove Roots", "Collect venom samples from poisonous snakes.",
          "Strange serpents have slithered into the grove, their fangs dripping an iridescent toxin unseen since before the Sundering. Lune hopes to refine an antidote—but only if someone brings her samples.",
          json.dumps({"collect": {"Serpent Venom": 3}}),
          json.dumps({"exp": 55, "gold": 24, "item": "Antidote Flask"})),
        (13, "Echoes in the Hollow", "E", "Hermit Sorin", "Hollowtree Den", "Investigate eerie whispers from a rotten tree cavern.",
          "Travelers claim that the Hollowtree whispers names, luring wanderers closer. Sorin suspects a Veil-born sprite nesting inside. He needs someone who won’t be fooled by its illusions.",
          json.dumps({"investigate": "Hollowtree", "defeat": {"Mischief Sprite": 1}}),
          json.dumps({"exp": 70, "gold": 22})),
        (14, "The Lumberjack’s Wrath", "E", "Lumberjack Bran", "Birchfall Path", "Eliminate a territorial Treeling.",
          "A sentient sap-creature—the Treeling—has claimed Birchfall Path, harassing workers and smashing tools. Bran asks for aid before the creature’s roots choke out the entire path.",
          json.dumps({"defeat": {"Treeling": 1}}),
          json.dumps({"exp": 90, "gold": 28, "item": "Bark-Stitched Gloves"})),
        (15, "Shadows Over the Water", "E", "Fisher Amon", "Moonwater Shore", "Water spirits are disturbing fishermen.",
          "Moonwater’s surface shimmers even without sun, revealing restless Naiads that drag nets underwater. Amon fears someone will be taken next. He needs protection.",
          json.dumps({"defeat": {"Moonwater Naiad": 3}}),
          json.dumps({"exp": 65, "gold": 20})),
        (16, "Broken Idol Pieces", "E", "Traveling Scholar Firren", "Mossdeep Trail", "Recover fragments of an ancient forest idol.",
          "Goblins shattered a woodland idol to steal its gemstones. Firren wishes to reassemble the relic before its latent magic spills into the wild.",
          json.dumps({"retrieve": {"Idol Fragments": 4}}),
          json.dumps({"exp": 55, "gold": 30})),
        (17, "A Test of Aim", "E", "Ranger Alyss", "Ranger Outpost", "Practice combat against agile forest beasts.",
          "Alyss trains new recruits by sending them after Swift-tail Hares—nimble creatures infused with faint forest magic. Catching them tests reflex and precision.",
          json.dumps({"defeat": {"Swift-tail Hare": 5}}),
          json.dumps({"exp": 50, "gold": 12, "item": "Wooden Ranger Pendant"})),
        (18, "The Missing Courier", "E", "Town Hall", "Northern Road", "Find a courier who vanished en route to Willowcreek.",
          "A forest courier carrying urgent correspondence never arrived. Tracks suggest he was chased off-road by beasts. His satchel holds valuable village contracts.",
          json.dumps({"find": "Courier", "retrieve": "Mail Satchel"}),
          json.dumps({"exp": 70, "gold": 26})),
        (19, "Spider Nest Purge", "E", "Guard Captain Rhea", "Webwood", "Destroy a growing spider nest.",
          "The Webwood’s population of brood spiders has ballooned, stringing webs across traveler roads. Their venom weakens limbs, making escape impossible. Rhea requires an adventurer to thin their numbers.",
          json.dumps({"defeat": {"Brood Spider": 6}}),
          json.dumps({"exp": 85, "gold": 32, "item": "Venom Sac"})),
        (20, "Mushroom Menace", "E", "Gatherer Pim", "Sporebrush Patch", "Defeat aggressive fungus creatures.",
          "Sporeshrooms have sprouted beyond their usual cycle, animated by warped forest mana. Pim’s harvesting routes are blocked unless these lumbering fungi are cleared.",
          json.dumps({"defeat": {"Sporeshroom": 4}}),
          json.dumps({"exp": 80, "gold": 30})),
        (21, "The Goblin Lieutenant", "D", "Guard Captain Rhea", "Ruined Camp", "Take down a goblin commander.",
          "A cunning goblin lieutenant has unified several scattered tribes. His camp rings with stolen steel and crude banners. If left unchecked, an organized horde might rise.",
          json.dumps({"defeat": {"Goblin Lieutenant Krag": 1}}),
          json.dumps({"exp": 120, "gold": 55, "item": "Krag’s Insignia"})),
        (22, "Forest Spirit in Pain", "D", "Druidess Leira", "Heartwood Glade", "Aid a wounded forest spirit.",
          "A Heartwood Sprite has been corrupted by a splinter of Veil energy lodged in its body. Leira believes an adventurer with a steady hand can help remove it—if they can survive its thrashing.",
          json.dumps({"subdue": "Sprite", "remove": "Veil Splinter"}),
          json.dumps({"exp": 110, "gold": 40, "item": "Blessing of Vital Sap"})),
        (23, "Hunt the Moonfang Wolf", "D", "Hunter Yorin", "Moonfang Den", "Hunt a powerful forest wolf touched by moonlight.",
          "The Moonfang Wolf is a silver-coated predator that leads lesser wolves with eerie discipline. Yorin fears it will turn its pack upon the village unless someone challenges it.",
          json.dumps({"defeat": {"Moonfang Wolf": 1}}),
          json.dumps({"exp": 150, "gold": 60, "item": "Moonfang Pelt"})),
        (24, "Entangled Roots", "D", "Woodsman Eddan", "Rootcoil Valley", "Destroy corrupted root-beasts.",
          "Tanglesap Creatures—animated roots—have begun striking at loggers. Their claws are formed of hardened bark and their bodies pulse with sickly green glow.",
          json.dumps({"defeat": {"Tanglesap Creature": 3}}),
          json.dumps({"exp": 100, "gold": 30})),
        (25, "Signs of the First Boss (Thornhide Bear)", "D", "Guard Captain Rhea", "Western Deepwood", "Scout territory of the Thornhide Bear.",
          "Massive claw marks and uprooted trees mark the hunting grounds of Thornhide—the first of the forest’s three boss creatures. Before a slaying party mobilizes, Rhea needs precise scouting intel.",
          json.dumps({"survey": {"Bear Signs": 3}, "report_to": "Guard Captain Rhea"}),
          json.dumps({"exp": 90, "gold": 25})),
        (26, "A Merchant in Tears", "D", "Merchant Salvi", "Bramble Road", "Recover stolen trade goods.",
          "Bandit-goblins ambushed Salvi and fled into the thicket with his fabrics and spices. The merchant begs someone to reclaim the goods before the creatures burn or eat them.",
          json.dumps({"recover": {"Trade Crates": 5}}),
          json.dumps({"exp": 100, "gold": 35, "item": "Salvi’s Trade Token"})),
        (27, "Cleanse the Shrine", "D", "Shrine Keeper Mara", "Moonshadow Shrine", "Purify a shrine corrupted by Veil energy.",
          "The Moonshadow Shrine’s white stones have turned black-veined, its pool reflecting horrors instead of moonlight. Mara needs an adventurer to drive off the wraithlings haunting it.",
          json.dumps({"defeat": {"Wraithling": 5}, "use": "Purification Amulet"}),
          json.dumps({"exp": 130, "gold": 45, "item": "Blessed Talisman"})),
        (28, "The Spider Matron", "D", "Guard Captain Rhea", "Webwood Nest", "Hunt the matriarch of the spider colony.",
          "The brood spiders answer to a single massive mother whose venom sacs can rot bark. Her growing brood threatens to spread beyond Webwood entirely.",
          json.dumps({"defeat": {"Spider Matron Vesska": 1}}),
          json.dumps({"exp": 160, "gold": 70, "item": "Vesska’s Venom"})),
        (29, "Before the Storm", "D", "Town Hall Council", "Willowcreek", "Prepare the town for coming threats.",
          "The council fears an impending surge of monsters, driven outward by the forest bosses awakening. They require supplies gathered and warnings spread to outlying homes.",
          json.dumps({"deliver": {"Warning Notices": 3}, "bring": {"Supply Sacks": 2}}),
          json.dumps({"exp": 85, "gold": 30})),
        (30, "The Whispering Oak", "D", "Druidess Leira", "Whispering Oak Circle", "Investigate a sacred tree murmuring with corrupted voices.",
          "The Whispering Oak, ancient guardian of the forest, has begun muttering in tones unlike any druidic language. Leira suspects an unseen parasite clinging to its bark—one born of the Veil.",
          json.dumps({"inspect": "Oak", "defeat": {"Oak Parasite": 1}}),
          json.dumps({"exp": 140, "gold": 50, "item": "Oakwood Charm"}))
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO quests (id, title, tier, quest_giver, location, summary, description, objectives, rewards)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, quests_to_insert)
    conn.commit()


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        insert_classes(conn)
        insert_monsters(conn)
        insert_quest_items(conn)
        insert_consumables(conn)
        insert_equipments(conn)
        insert_class_equipments(conn)
        insert_quests(conn)
        print("✔ Database population complete.")
    except Exception as e:
        print("Error populating database:", e)
    finally:
        conn.close()



if __name__ == "__main__":
    main()
