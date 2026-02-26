import unittest
from unittest.mock import patch

from game_systems.adventure.adventure_events import AdventureEvents
from game_systems.core.world_time import TimePhase


class TestAdventureEventsCoverage(unittest.TestCase):

    @patch('game_systems.adventure.adventure_events.random.random')
    @patch('game_systems.adventure.adventure_events.random.choice')
    def test_regeneration_coverage(self, mock_choice, mock_random):
        # Mock choice to return the first element for predictability
        mock_choice.side_effect = lambda x: x[0]

        # Test 1: Critical HP
        # 1. Low HP check (True) -> Enter block
        # 2. Atmosphere check (False)
        mock_random.side_effect = [0.1, 0.9]
        logs = AdventureEvents.regeneration(hp_percent=0.1)
        self.assertIn("Blood drips", logs[0])

        # Test 2: High HP
        # 1. Low HP check (False - skipped due to hp_percent)
        # 2. High HP check (True) -> Enter block
        # 3. Atmosphere check (False)
        mock_random.side_effect = [0.1, 0.9]
        logs = AdventureEvents.regeneration(hp_percent=0.9)
        self.assertIn("rhythm of the battle", logs[0])

        # Test 3: Class Specific
        # 1. Low HP (False)
        # 2. High HP (False)
        # 3. Class check (True)
        # 4. Atmosphere check (False)
        mock_random.side_effect = [0.1, 0.9]
        logs = AdventureEvents.regeneration(class_name="Warrior", hp_percent=0.5)
        self.assertIn("straps of your armor", logs[0])

        # Test 4: Location Specific (No random check for entry)
        # 1. Low HP (False)
        # 2. High HP (False)
        # 3. Class check (False - if forced fail)
        # 4. Atmosphere check (False)
        mock_random.side_effect = [0.9, 0.9]
        logs = AdventureEvents.regeneration(location_id="whispering_thicket", hp_percent=0.5, class_name="Warrior")
        self.assertIn("canopy is so thick", logs[0])

        # Test 5: Atmosphere Trigger
        # 1. Low HP (False)
        # 2. High HP (False)
        # 3. Class check (Skipped - "Adventurer" not in dict)
        # 4. Atmosphere check (True)
        # 5. Overrides check (e.g. Night) (True)
        # 6. Weather Override check (False)
        mock_random.side_effect = [0.1, 0.1, 0.9]
        logs = AdventureEvents.regeneration(location_id="forest", hp_percent=0.5, time_phase=TimePhase.NIGHT)
        self.assertEqual(len(logs), 2)
        self.assertIn("moon is hidden", logs[0]) # Night atmosphere

    @patch('game_systems.adventure.adventure_events.random.choice')
    def test_quest_event(self, mock_choice):
        mock_choice.side_effect = lambda x: x[0]
        self.assertIn("cluster", AdventureEvents.quest_event("gather", "Herb"))
        self.assertIn("hiding behind a rock", AdventureEvents.quest_event("locate", "Wolf").lower())
        self.assertIn("study", AdventureEvents.quest_event("examine", "Rune").lower())
        self.assertIn("mark", AdventureEvents.quest_event("unknown", "Thing").lower())

    @patch('game_systems.adventure.adventure_events.random.choice')
    def test_special_event_flavor(self, mock_choice):
        mock_choice.side_effect = lambda x: x[0]
        self.assertIn("sanctuary", AdventureEvents.special_event_flavor("safe_room"))
        self.assertIn("loose stone", AdventureEvents.special_event_flavor("hidden_stash"))
        self.assertIn("kneel", AdventureEvents.special_event_flavor("ancient_shrine"))
        self.assertIn("CLICK", AdventureEvents.special_event_flavor("trap_pit"))
        self.assertEqual(AdventureEvents.special_event_flavor("unknown"), "*A strange event occurs.*")

    @patch('game_systems.adventure.adventure_events.random.choice')
    def test_scavenge_event(self, mock_choice):
        mock_choice.side_effect = lambda x: x[0]
        self.assertIn("Aurum", AdventureEvents.scavenge_event("aurum", 10))
        self.assertIn("XP", AdventureEvents.scavenge_event("exp", 10))

    def test_no_event_found(self):
        self.assertTrue(len(AdventureEvents.no_event_found()) > 0)

    def test_surge_event(self):
        self.assertTrue(len(AdventureEvents.surge_event()) > 0)

    def test_wild_gather_event(self):
        self.assertIn("Berry", AdventureEvents.wild_gather_event("Berry"))
