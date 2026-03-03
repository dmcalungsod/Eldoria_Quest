import sys
from unittest.mock import MagicMock

# Patch dependencies before importing production code
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.errors"] = MagicMock()
sys.modules["discord"] = MagicMock()
sys.modules["discord.ext"] = MagicMock()
sys.modules["discord.ext.commands"] = MagicMock()

import unittest  # noqa: E402
from unittest.mock import patch  # noqa: E402

# Import after mocking
from game_systems.adventure.combat_handler import CombatHandler  # noqa: E402
from game_systems.data.monsters import MONSTERS  # noqa: E402


class TestMonsterDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.handler = CombatHandler(self.mock_db, 12345)

        # Patch MONSTERS to use a local copy for testing
        self.test_monster_key = "test_goblin"
        self.test_monster_data = {
            "name": "Test Goblin",
            "level": 1,
            "tier": "Normal",
            "hp": 50,
            "atk": 5,
            "def": 2,
            "xp": 10,
            "drops": [("gold", 100)],
            "skills": [],
        }

        # Patch the MONSTERS dictionary itself
        self.monsters_patcher = patch.dict(
            "game_systems.data.monsters.MONSTERS", {self.test_monster_key: self.test_monster_data}, clear=True
        )
        self.monsters_patcher.start()

    def tearDown(self):
        self.monsters_patcher.stop()

    @patch("game_systems.adventure.combat_handler.WorldEventSystem")
    @patch("game_systems.adventure.combat_handler.WorldTime")
    def test_spectral_tide_does_not_mutate_global_monsters(self, MockWorldTime, MockWorldEventSystem):
        """
        Verify that the Spectral Tide event does not permanently add drops to the global MONSTERS template.
        """
        # Setup mocks
        MockWorldTime.is_night.return_value = False
        MockWorldTime.get_phase_flavor.return_value = "It is day."

        # Mock Event System (return None to skip blood moon checks)
        mock_event_system = MockWorldEventSystem.return_value
        mock_event_system.get_current_event.return_value = None

        # Mock DB for Spectral Tide
        self.mock_db.get_active_tournament.return_value = {"type": "spectral_tide"}

        # Force random checks to trigger Spectral Tide logic
        # First random.choices selects monster, then random.random check for Spectral Tide (0.1 < 0.20)
        with (
            patch("random.choices", return_value=[self.test_monster_key]),
            patch("random.random", side_effect=[0.1, 0.9]),
        ):  # 0.1 triggers Spectral, 0.9 fails next time
            # First combat initiation - Should add ectoplasm to active_monster
            monster1, _ = self.handler.initiate_combat({"monsters": [(self.test_monster_key, 100)]})

            # Verify monster has ectoplasm
            self.assertTrue(any(d[0] == "ectoplasm" for d in monster1["drops"]), "Monster should have ectoplasm")

            # Verify global template is UNCHANGED
            global_monster = MONSTERS[self.test_monster_key]

            # This is the assertion that will FAIL if the bug exists
            has_ecto = any(d[0] == "ectoplasm" for d in global_monster["drops"])
            if has_ecto:
                print(f"DEBUG: Global monster drops polluted: {global_monster['drops']}")

            self.assertFalse(has_ecto, "CRITICAL: Global MONSTERS data was modified! 'ectoplasm' found in template.")

            # Run again to be sure (no spectral tide this time)
            monster2, _ = self.handler.initiate_combat({"monsters": [(self.test_monster_key, 100)]})

            # This assertion will also FAIL if bug exists because pollution persists
            self.assertFalse(
                any(d[0] == "ectoplasm" for d in monster2["drops"]),
                "Monster 2 should NOT have ectoplasm (pollution persisted!)",
            )


if __name__ == "__main__":
    unittest.main()
