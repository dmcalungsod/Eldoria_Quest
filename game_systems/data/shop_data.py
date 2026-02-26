"""
shop_data.py

Defines shop inventories for the Guild Supply Depot and special event merchants.
Inventory Structure: {item_key: {"price": int, "daily_limit": int}}
"""

SHOP_INVENTORY = {
    "hp_potion_1": {"price": 40, "daily_limit": 5},
    "mp_potion_1": {"price": 40, "daily_limit": 5},
    "antidote_basic": {"price": 40, "daily_limit": 3},
    "smoke_pellet": {"price": 45, "daily_limit": 5},
    "food_ration": {"price": 15, "daily_limit": 5},
    "hp_potion_2": {"price": 90, "daily_limit": 3},
    "mp_potion_2": {"price": 90, "daily_limit": 3},
    "strength_brew": {"price": 120, "daily_limit": 3},
    "dex_elixir": {"price": 120, "daily_limit": 3},
}

# Special Merchants may not have limits (or have different ones)
MYSTIC_MERCHANT_INVENTORY = {
    "elixir_luck": {"price": 300, "daily_limit": 2},
    "volatile_brew": {"price": 450, "daily_limit": 2},
    "shadow_veil": {"price": 500, "daily_limit": 2},
    "regen_potion": {"price": 350, "daily_limit": 3},
    "resist_elixir": {"price": 400, "daily_limit": 3},
    "campfire_stew": {"price": 100, "daily_limit": 5},
}
