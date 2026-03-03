import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock pymongo before importing game systems
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.collection"] = MagicMock()
sys.modules["pymongo.database"] = MagicMock()

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_systems.data.adventure_locations import LOCATIONS


class TestFloorDepthData(unittest.TestCase):
    def test_locations_have_floor_depth_and_danger_level(self):
        """Verify all locations have valid floor_depth and danger_level fields."""
        self.assertTrue(len(LOCATIONS) > 0, "Locations data is empty")
        for loc_id, loc_data in LOCATIONS.items():
            self.assertIn("floor_depth", loc_data, f"Location {loc_id} is missing 'floor_depth'")
            self.assertIn("danger_level", loc_data, f"Location {loc_id} is missing 'danger_level'")
            self.assertIsInstance(loc_data["floor_depth"], int, f"Location {loc_id} 'floor_depth' is not an integer")
            self.assertIsInstance(loc_data["danger_level"], int, f"Location {loc_id} 'danger_level' is not an integer")
            self.assertGreaterEqual(loc_data["floor_depth"], 1, f"Location {loc_id} 'floor_depth' is less than 1")
            self.assertGreaterEqual(loc_data["danger_level"], 1, f"Location {loc_id} 'danger_level' is less than 1")


if __name__ == "__main__":
    unittest.main()
