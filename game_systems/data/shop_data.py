"""
shop_data.py

Defines shop inventories for the Guild Supply Depot and special event merchants.
Includes purchase limits to enforce scarcity and encourage crafting.
"""

SHOP_INVENTORY = {
    "hp_potion_1": 40,
    "mp_potion_1": 40,
    "antidote_basic": 40,
    "smoke_pellet": 45,
    "food_ration": 15,
    "hp_potion_2": 90,
    "mp_potion_2": 90,
    "strength_brew": 120,
    "dex_elixir": 120,
}

# Realism: Daily purchase limits to prevent hoarding and simulate guild rationing.
SHOP_PURCHASE_LIMITS = {
    "hp_potion_1": 3,
    "mp_potion_1": 3,
    "food_ration": 5,
    "antidote_basic": 2,
    "smoke_pellet": 3,
    "strength_brew": 1,
    "dex_elixir": 1,
    "hp_potion_2": 1,
    "mp_potion_2": 1,
}

MYSTIC_MERCHANT_INVENTORY = {
    "elixir_luck": 300,
    "volatile_brew": 450,
    "shadow_veil": 500,
    "regen_potion": 350,
    "resist_elixir": 400,
    "campfire_stew": 100,
}
