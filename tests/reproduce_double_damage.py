import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, ANY

# Add repo root to path
sys.path.append(os.getcwd())

# MOCK PYMONGO BEFORE IMPORT
mock_pymongo = MagicMock()
mock_errors = MagicMock()
mock_errors.DuplicateKeyError = Exception
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_errors

# Now import
from game_systems.adventure import adventure_session  # noqa: E402
from game_systems.adventure.adventure_session import AdventureSession  # noqa: E402
from game_systems.adventure.combat_handler import CombatHandler # noqa: E402

class ReproduceDoubleDamage(unittest.TestCase):
    def setUp(self):
        # Mock DB Manager
        self.db = MagicMock()
        self.db.update_player_vitals_delta = MagicMock()
        self.db.update_adventure_session = MagicMock()

        self.user_id = 123

        # Initial Session Data
        self.session_data = {
            "discord_id": self.user_id,
            "location_id": "loc_1",
            "active": 1,
            "logs": "[]",
            "loot_collected": "{}",
            "active_monster_json": json.dumps({
                "name": "Goblin", "HP": 100, "max_hp": 100,
                "level": 1, "tier": "Normal", "xp": 10,
                "drops": [], "atk": 10, "def": 0
            }),
            "version": 1
        }

        # Setup DB mocks
        self.db.get_active_adventure.return_value = self.session_data

        # Setup Context Bundle
        self.bundle = {
            "player": {
                "discord_id": 123, "current_hp": 100, "current_mp": 50,
                "class_id": 1, "level": 1, "experience": 0, "exp_to_next": 1000
            },
            "stats": {"HP": {"base": 100}, "MP": {"base": 50}, "STR": {"base": 10}, "AGI": {"base": 10}},
            "buffs": [],
            "skills": [],
            "active_session": self.session_data,
            "vitals": {"current_hp": 100, "current_mp": 50}
        }
        self.db.get_combat_context_bundle.return_value = self.bundle
        self.db.get_active_boosts.return_value = []
        self.db.get_active_world_event.return_value = None

        # Patch LOCATIONS
        self.locations_patcher = patch.dict(
            adventure_session.LOCATIONS, {"loc_1": {"name": "Test Location", "monsters": []}}
        )
        self.locations_patcher.start()

    def tearDown(self):
        self.locations_patcher.stop()

    def test_vitals_update_on_failed_session_save(self):
        """
        Simulates a race condition where the session save fails (optimistic lock),
        but the vitals update (HP loss) still executes.
        """
        # Create Session Object
        session = AdventureSession(self.db, MagicMock(), MagicMock(), self.user_id, self.session_data)

        # Mock Combat Handler to simulate damage
        # We Mock resolve_turn to return a result that implies damage taken
        # AND check that it calls update_player_vitals_delta internally (default behavior)

        # NOTE: In the real code, CombatHandler.resolve_turn calls db.update_player_vitals_delta
        # if persist_vitals=True (default).
        # We want to verify that this call happens even if subsequent session save fails.

        # To do this, we need to let CombatHandler run, but mock the DB calls it makes.

        # We need to make sure CombatHandler is using our mocked DB
        session.combat.db = self.db

        # Mock CombatEngine inside CombatHandler to control the outcome
        with patch("game_systems.adventure.combat_handler.CombatEngine") as MockEngine:
            instance = MockEngine.return_value
            instance.run_combat_turn.return_value = {
                "winner": None,
                "phrases": ["Took damage!"],
                "hp_current": 90, # -10 HP
                "mp_current": 50,
                "monster_hp": 90,
                "turn_report": {},
                "active_boosts": {}
            }

            # Setup update_adventure_session to FAIL (return False)
            self.db.update_adventure_session.return_value = False

            # Run the step
            result = session.simulate_step(context_bundle=self.bundle, action="attack")

            # Verify update_player_vitals_delta WAS NOT called
            # This confirms the Fix: Vitals are NOT updated if Session failed
            self.db.update_player_vitals_delta.assert_not_called()

            # Verify session update WAS attempted
            self.db.update_adventure_session.assert_called()

            # Verify result indicates error (due to save failure)
            logs = result.get("sequence", [])
            combined_logs = "".join([str(x) for x in logs])
            self.assertIn("System Error", combined_logs)

            print("\n[SUCCESS] Fix Verified: Vitals update prevented on session save failure.")

if __name__ == "__main__":
    unittest.main()
