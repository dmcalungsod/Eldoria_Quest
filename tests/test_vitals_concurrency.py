
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.getcwd())

# MOCK PYMONGO BEFORE IMPORT
mock_pymongo = MagicMock()
mock_errors = MagicMock()
mock_errors.DuplicateKeyError = Exception
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_errors

# Also need to mock 'pymongo.collection' and 'pymongo.results' potentially,
# but let's see if this is enough.

from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402


class MockDatabaseManager:
    def __init__(self):
        self.player_data = {
            "discord_id": 123,
            "current_hp": 50,
            "current_mp": 50,
            "aurum": 1000
        }
        self.stats_data = {
            "STR": {"base": 10},
            "END": {"base": 5}, # END 5 -> +50 HP -> Total 100 HP
            "DEX": {"base": 10},
            "AGI": {"base": 10},
            "MAG": {"base": 16}, # MAG 16 -> +80 MP -> Total 100 MP
            "LCK": {"base": 10}
        }

    def get_combat_context_bundle(self, discord_id):
        # Return minimal context for testing
        return {
            "player": self.player_data.copy(),
            "stats": self.stats_data,
            "buffs": [],
            "skills": [],
            "active_session": {}
        }

    def get_active_boosts(self):
        return []

    def set_player_vitals(self, discord_id, hp, mp):
        # This is the vulnerable method
        self.player_data["current_hp"] = hp
        self.player_data["current_mp"] = mp

    def execute_heal(self, discord_id, max_hp, max_mp, cost):
        # Simulates external heal
        self.player_data["current_hp"] = max_hp
        self.player_data["current_mp"] = max_mp

    def update_adventure_session(self, *args, **kwargs):
        return True

    def get_player_stats_json(self, discord_id):
        return self.stats_data

    def get_active_world_event(self):
        return None

    def update_player_vitals_delta(
        self, discord_id, hp_delta, mp_delta, max_hp, max_mp
    ):
        # Emulate the atomic update with clamping
        # Apply delta
        new_hp = self.player_data["current_hp"] + hp_delta
        new_mp = self.player_data["current_mp"] + mp_delta

        # Clamp (Min)
        new_hp = min(max_hp, new_hp)
        new_mp = min(max_mp, new_mp)

        # Clamp (Max)
        new_hp = max(0, new_hp)
        new_mp = max(0, new_mp)

        self.player_data["current_hp"] = new_hp
        self.player_data["current_mp"] = new_mp

class TestHealRaceCondition(unittest.TestCase):
    def setUp(self):
        # Need to patch DatabaseManager where AdventureSession uses it
        # But AdventureSession takes db as argument
        pass

    def test_heal_overwritten_by_adventure(self):
        self.db = MockDatabaseManager()
        self.user_id = 123

        # 1. Setup Session
        # We need to mock 'AdventureRewards', 'CombatHandler', 'EventHandler' inside AdventureSession
        # because they might try to use real DB calls if not careful.
        # AdventureSession instantiates them in __init__.

        with patch("game_systems.adventure.adventure_session.AdventureRewards") as MockRewards, \
             patch("game_systems.adventure.adventure_session.CombatHandler") as MockCombat, \
             patch("game_systems.adventure.adventure_session.EventHandler") as MockEvents, \
             patch("game_systems.adventure.adventure_session.LOCATIONS", {"loc_1": {"name": "Test", "monsters": []}}):

            session = AdventureSession(self.db, MagicMock(), MagicMock(), self.user_id, {"location_id": "loc_1", "active": 1, "logs": "[]", "loot_collected": "{}", "active_monster_json": None})

            # Mock active monster to force combat logic
            session.active_monster = {"name": "Goblin", "HP": 50, "max_hp": 50, "tier": "Normal"}

            # 2. Mock Combat Handler to simulate:
            #    a) External Heal happens
            #    b) Combat deals damage based on ORIGINAL state

            # Setup the mocked combat instance
            mock_combat_instance = MockCombat.return_value

            def mock_resolve_turn(*args, **kwargs):
                # A. Simulate External Heal (e.g. via Infirmary)
                # Player was at 50 HP. Heals to 100.
                self.db.execute_heal(self.user_id, 100, 100, 10)

                # B. Combat calculates result based on OLD context (HP 50)
                # Takes 10 damage -> 40 HP
                return {
                    "winner": None,
                    "phrases": ["Took 10 damage"],
                    "hp_current": 40, # 50 - 10
                    "mp_current": 50,
                    "monster_hp": 50,
                    "turn_report": {},
                    "active_boosts": {},
                    "monster_data": session.active_monster
                }

            mock_combat_instance.resolve_turn.side_effect = mock_resolve_turn

            # 3. Run Step
            # This will fetch context (HP 50), run resolve_turn (Heal to 100, then return 40),
            # then call set_player_vitals(40).
            session.simulate_step(action="attack")

            # Verify persist_vitals=False was passed to resolve_turn (prevent double update regression)
            # mock_combat_instance.resolve_turn was called 8 times. Check arguments.
            self.assertTrue(mock_combat_instance.resolve_turn.called)

            # Check the keyword arguments of the calls
            # We can inspect call_args_list to see all calls
            for call in mock_combat_instance.resolve_turn.call_args_list:
                args, kwargs = call
                self.assertIn("persist_vitals", kwargs, "persist_vitals argument missing in resolve_turn call")
                self.assertFalse(kwargs["persist_vitals"], "Auto-combat must use persist_vitals=False to prevent double DB updates")

            # 4. Assert
            final_hp = self.db.player_data["current_hp"]

            # If bug exists, HP is 40 (Heal lost)
            # If fixed, HP should be 90 (100 - 10)

            # With the fix, the sequence is:
            # 1. Start: HP 50
            # 2. Heal: HP -> 100
            # 3. Combat: Delta -10
            # 4. Result: 100 - 10 = 90

            self.assertEqual(final_hp, 90, f"Bug Fixed: External heal preserved. Expected 90, got {final_hp}")

if __name__ == "__main__":
    unittest.main()
