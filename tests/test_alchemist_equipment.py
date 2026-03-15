"""
tests/test_alchemist_equipment.py

Tests specifically for Alchemist equipment logic, stat budgets, and slot conflicts.
"""

import os
import sys
from unittest.mock import MagicMock

# Mock Database / Pymongo
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

from game_systems.data.class_equipments import CLASS_EQUIPMENTS, STAT_BUDGETS  # noqa: E402
from game_systems.items.equipment_manager import EquipmentManager  # noqa: E402


@pytest.fixture
def eq_manager():
    # Return manager with mocked DB
    db = MagicMock()
    return EquipmentManager(db)


def test_alchemist_coat_stat_budget():
    """Verify the stat budget for alchemist_coat is correct."""
    budget = STAT_BUDGETS.get("alchemist_coat")
    assert budget is not None, "alchemist_coat budget missing"
    assert budget["MAG"] == 0.5
    assert budget["DEX"] == 0.3
    assert budget["END"] == 0.2


def test_alchemist_coat_generation():
    """Verify that alchemist_coat items are actually generated."""
    coats = [
        item for item in CLASS_EQUIPMENTS.values() if item["slot"] == "alchemist_coat" and item["class"] == "Alchemist"
    ]
    assert len(coats) > 0, "No Alchemist Coats generated"

    # Check stats of a sample coat (e.g., Common)
    sample = next((c for c in coats if c["rarity"] == "Common"), None)
    assert sample is not None

    stats = sample["stats_bonus"]
    # For Common Level 1, budget is 1.
    # ceil(1 * 0.5) = 1 MAG
    # ceil(1 * 0.3) = 1 DEX
    # ceil(1 * 0.2) = 1 END
    assert stats.get("MAG") >= 1
    assert stats.get("DEX") >= 1
    assert stats.get("END") >= 1


def test_alchemist_equip_restrictions(eq_manager):
    """Test what an Alchemist can and cannot equip."""

    # Mock Alchemist Player
    player_data = {"level": 10, "rank": "F", "class_name": "Alchemist"}

    # 1. Allowed Item (Alchemist Coat)
    coat_item = {"slot": "alchemist_coat", "level_req": 1}
    # Note: check_requirements checks Level/Rank/Class Restriction tags
    # It does NOT check 'allowed_slots' from class_data (that's done in equip_item)
    # But EquipmentManager.equip_item calls _get_player_allowed_slots.

    # We'll mock the DB calls needed for `equip_item` to test the full flow partially,
    # or just test `_get_player_allowed_slots`.

    # Let's test _get_player_allowed_slots first
    eq_manager.db.get_player_field.return_value = 6  # Alchemist ID

    allowed = eq_manager._get_player_allowed_slots(123)
    assert "alchemist_coat" in allowed
    assert "tome" in allowed
    assert "medium_armor" in allowed
    assert "robe" in allowed
    assert "staff" not in allowed
    assert "heavy_armor" not in allowed


def test_body_slot_conflict_logic(eq_manager):
    """Verify that alchemist_coat is mutually exclusive with other body armor."""

    # Mock equipped items
    eq_manager.db.get_equipped_items.return_value = [{"id": 1, "slot": "robe", "item_name": "Old Robe"}]

    # Item to equip: Alchemist Coat
    new_item = {"slot": "alchemist_coat"}

    # We want to see if 'robe' is identified as a conflict
    # logic in equip_item:
    # if target_slot in BODY_SLOTS: slots_to_check.update(BODY_SLOTS)

    target_slot = "alchemist_coat"
    slots_to_check = set()

    if target_slot in eq_manager.BODY_SLOTS:
        slots_to_check.update(eq_manager.BODY_SLOTS)

    assert "robe" in slots_to_check
    assert "heavy_armor" in slots_to_check
    assert "alchemist_coat" in slots_to_check

    # Verify strict logic
    assert "helm" not in slots_to_check
