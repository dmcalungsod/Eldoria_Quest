"""
game_systems/data/shop_data.py

Centralized configuration for the Adventurer's Guild Shop.
Defines prices and stock limits to enforce scarcity.
"""

# Base Prices (Aurum)
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

# Max Stock per Restock Cycle (Scarcity Enforcement)
SHOP_STOCK_LIMITS = {
    "hp_potion_1": 3,
    "mp_potion_1": 3,
    "antidote_basic": 2,
    "smoke_pellet": 2,
    "food_ration": 5,
    "hp_potion_2": 1,
    "mp_potion_2": 1,
    "strength_brew": 1,
    "dex_elixir": 1,
}
