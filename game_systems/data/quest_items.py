"""
QUEST_ITEMS — Eldoria Quest (Forest beginner zone)
--------------------------------------------------
A curated list of 30 quest items for early quests in the forest region.
Each quest item:
{
  "id": "quest_key",
  "name": str,
  "rarity": str,
  "notes": str
}
Rarities: Common, Uncommon, Rare, Epic, Legendary, Mythical (quests may demand high rarities)
"""

QUEST_ITEMS = {
    "q_forest_note_01": {
        "id": "q_forest_note_01",
        "name": "Torn Letter — Rookwood",
        "rarity": "Common",
        "notes": "A rain-spattered scrap, with a frantic scrawl asking for aid near the eastern glade.",
    },
    "q_spider_venom_vial": {
        "id": "q_spider_venom_vial",
        "name": "Glass Vial of Thicket Venom",
        "rarity": "Uncommon",
        "notes": "Collected from the fangs of Thicket Spiders; a healer seeks this for an antidote.",
    },
    "q_relic_frag_01": {
        "id": "q_relic_frag_01",
        "name": "Relic Fragment — Verdant Sigil",
        "rarity": "Rare",
        "notes": "A shard of a once-hallowed sigil; three are needed to restore the shrine.",
    },
    "q_farmers_locket": {
        "id": "q_farmers_locket",
        "name": "Farmer Edrin's Locket",
        "rarity": "Common",
        "notes": "A brass locket lost in the brambles; a local offers coin for its return.",
    },
    "q_moonroot_seed": {
        "id": "q_moonroot_seed",
        "name": "Moonroot Seed",
        "rarity": "Uncommon",
        "notes": "Said to sprout under moonlight; required by a druidic ritual.",
    },
    "q_wand_wood_chip": {
        "id": "q_wand_wood_chip",
        "name": "Chip of Elderwood",
        "rarity": "Rare",
        "notes": "A splinter from a warlock's staff; the mage's guild requires it for study.",
    },
    "q_owl_feather": {
        "id": "q_owl_feather",
        "name": "Silver-Striped Owl Feather",
        "rarity": "Common",
        "notes": "Used in letter-calling charms and children’s trinkets.",
    },
    "q_branded_coin": {
        "id": "q_branded_coin",
        "name": "Branded Coin of the Red March",
        "rarity": "Uncommon",
        "notes": "A soldier’s token; a missing veteran's family seeks it.",
    },
    "q_glade_map_piece": {
        "id": "q_glade_map_piece",
        "name": "Fragment of Old Map (Glade)",
        "rarity": "Common",
        "notes": "One of several fragments showing a secret hunting path.",
    },
    "q_signet_seal": {
        "id": "q_signet_seal",
        "name": "Small Signet Seal",
        "rarity": "Rare",
        "notes": "An insignia of a minor noble—lost at the edge of the wood.",
    },
    "q_herbal_compendium_page": {
        "id": "q_herbal_compendium_page",
        "name": "Compendium Page: Verdant Tonics",
        "rarity": "Uncommon",
        "notes": "A page torn from an old herbalist's manual; sought by the apothecary.",
    },
    "q_mossy_stone": {
        "id": "q_mossy_stone",
        "name": "Moss-Blessed Stone",
        "rarity": "Uncommon",
        "notes": "A votive rock used in glade rites; missing from a circle.",
    },
    "q_bloodstained_note": {
        "id": "q_bloodstained_note",
        "name": "Bloodstained Note",
        "rarity": "Rare",
        "notes": "Written with a hand shaking from fear—mentions the 'Nightbloom'.",
    },
    "q_sunshroom_spore": {
        "id": "q_sunshroom_spore",
        "name": "Sunshroom Spore Cluster",
        "rarity": "Uncommon",
        "notes": "A culinary delicacy; a chef in the village will pay handsomely.",
    },
    "q_ranger_patch": {
        "id": "q_ranger_patch",
        "name": "Ranger Scout’s Patch",
        "rarity": "Common",
        "notes": "A lost token from a ranger patrol; its leader asks for its return.",
    },
    "q_hollow_heart": {
        "id": "q_hollow_heart",
        "name": "Hollow Heart (Carved Wood)",
        "rarity": "Rare",
        "notes": "A carved heart said to calm tormented spirits when burned.",
    },
    "q_blessed_wax": {
        "id": "q_blessed_wax",
        "name": "Wax of the Green Shrine",
        "rarity": "Common",
        "notes": "Needed to rekindle votive candles at the forest shrine.",
    },
    "q_ritual_braid": {
        "id": "q_ritual_braid",
        "name": "Ritual Braid of Twine",
        "rarity": "Uncommon",
        "notes": "Used to bind a ward—much sought by novice clerics.",
    },
    "q_poison_antidote_recipe": {
        "id": "q_poison_antidote_recipe",
        "name": "Antidote Recipe (Scrawl)",
        "rarity": "Rare",
        "notes": "A scribbled recipe pointing to the correct antidote herbs.",
    },
    "q_hunter_whistle": {
        "id": "q_hunter_whistle",
        "name": "Horned Hunter's Whistle",
        "rarity": "Common",
        "notes": "Calls a companion hound; a hunter's child lost theirs.",
    },
    "q_fallen_banner": {
        "id": "q_fallen_banner",
        "name": "Torn Banner of the Old Guard",
        "rarity": "Uncommon",
        "notes": "A relic of a skirmish; the town historian desires it.",
    },
    "q_arcane_etching": {
        "id": "q_arcane_etching",
        "name": "Arcane Etching Stone",
        "rarity": "Rare",
        "notes": "Used by mages for simple enchantments; only a few remain.",
    },
    "q_mysterious_seedling": {
        "id": "q_mysterious_seedling",
        "name": "Mysterious Seedling",
        "rarity": "Epic",
        "notes": "A sapling rumored to sprout with whispered secrets.",
    },
    "q_bloodroot_petal": {
        "id": "q_bloodroot_petal",
        "name": "Bloodroot Petal",
        "rarity": "Uncommon",
        "notes": "A rare medicinal bloom used in urgent salves.",
    },
    "q_guardian_crest": {
        "id": "q_guardian_crest",
        "name": "Guardian Crest Fragment",
        "rarity": "Rare",
        "notes": "A fragment of an old crest; two more pieces needed.",
    },
    "q_nightingale_song": {
        "id": "q_nightingale_song",
        "name": "Nightingale Song Jar",
        "rarity": "Epic",
        "notes": "A jar that captures a bird’s trill—legend says it heals sorrow.",
    },
    "q_forest_relic": {
        "id": "q_forest_relic",
        "name": "Forest Relic (Purity Stone)",
        "rarity": "Legendary",
        "notes": "A relic of the glade's founding—central to a long quest chain.",
    },
}
