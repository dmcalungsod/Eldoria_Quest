import os
import sys

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS

def test_monsters_balance():
    """Verifies that monster drop rates are balanced correctly."""

    # Feral Stag (monster_017)
    stag = MONSTERS.get("monster_017")
    assert stag, "Feral Stag not found"

    drops = dict(stag["drops"])
    # Expected Nerf
    assert drops.get("magic_stone_medium") == 50, f"Feral Stag magic_stone_medium expected 50, got {drops.get('magic_stone_medium')}"
    assert drops.get("boss_talon") == 80, f"Feral Stag boss_talon expected 80, got {drops.get('boss_talon')}"
    assert drops.get("celestial_dust") == 10, f"Feral Stag celestial_dust expected 10, got {drops.get('celestial_dust')}"

    # Duskling (monster_028)
    duskling = MONSTERS.get("monster_028")
    assert duskling, "Duskling not found"
    drops = dict(duskling["drops"])
    assert drops.get("magic_stone_medium") == 90, f"Duskling magic_stone_medium expected 90, got {drops.get('magic_stone_medium')}"

    # Cogwork Spider (monster_126)
    spider = MONSTERS.get("monster_126")
    assert spider, "Cogwork Spider not found"
    drops = dict(spider["drops"])
    assert drops.get("magic_stone_medium") == 10, f"Cogwork Spider magic_stone_medium expected 10, got {drops.get('magic_stone_medium')}"

    # Void Stalker (monster_116)
    stalker = MONSTERS.get("monster_116")
    assert stalker, "Void Stalker not found"
    drops = dict(stalker["drops"])
    assert drops.get("magic_stone_large") == 50, f"Void Stalker magic_stone_large expected 50, got {drops.get('magic_stone_large')}"

def test_locations_balance():
    """Verifies that location gatherables are balanced correctly."""

    # Shrouded Fen
    fen = LOCATIONS.get("shrouded_fen")
    assert fen, "Shrouded Fen not found"
    gather = dict(fen["gatherables"])
    assert gather.get("magic_stone_medium") == 30, f"Shrouded Fen magic_stone_medium expected 30, got {gather.get('magic_stone_medium')}"
    assert gather.get("ancient_wood") == 35, f"Shrouded Fen ancient_wood expected 35, got {gather.get('ancient_wood')}"

    # Clockwork Halls
    halls = LOCATIONS.get("clockwork_halls")
    assert halls, "Clockwork Halls not found"
    gather = dict(halls["gatherables"])
    assert gather.get("magic_stone_medium") == 25, f"Clockwork Halls magic_stone_medium expected 25, got {gather.get('magic_stone_medium')}"
    assert gather.get("magic_stone_large") == 5, f"Clockwork Halls magic_stone_large expected 5, got {gather.get('magic_stone_large')}"

    # Void Sanctum
    void = LOCATIONS.get("void_sanctum")
    assert void, "Void Sanctum not found"
    gather = dict(void["gatherables"])
    assert gather.get("magic_stone_flawless") == 20, f"Void Sanctum magic_stone_flawless expected 20, got {gather.get('magic_stone_flawless')}"

if __name__ == "__main__":
    try:
        test_monsters_balance()
        test_locations_balance()
        print("🎉 ALL BALANCE CHECKS PASSED")
    except AssertionError as e:
        print(f"❌ BALANCE CHECK FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ ERROR: {e}")
        sys.exit(1)
