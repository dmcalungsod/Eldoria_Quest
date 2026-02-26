
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pymongo BEFORE importing create_database
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

from database.create_database import create_tables

class TestCreateDatabase(unittest.TestCase):
    def test_create_tables_world_events_index(self):
        """Verify that indexes are created for world_events."""
        mock_db = MagicMock()

        # Configure mock_db to return different mocks for different collections
        # This allows us to inspect calls specific to world_events
        def get_collection(name):
            return getattr(mock_db, f"collection_{name}")

        mock_db.__getitem__.side_effect = get_collection

        # Call the function
        create_tables(mock_db)

        # Check world_events collection specific calls
        world_events_mock = mock_db.collection_world_events

        # We expect create_index("active") and create_index("end_time")
        # Check all calls to create_index on this collection
        calls = world_events_mock.create_index.call_args_list

        active_index_found = False
        end_time_index_found = False

        print("\nVerifying world_events indexes:")
        for call in calls:
            args, _ = call
            print(f"  - create_index({args})")
            if args and args[0] == "active":
                active_index_found = True
            if args and args[0] == "end_time":
                end_time_index_found = True

        if not active_index_found:
            self.fail("Missing index on 'active' for world_events collection")
        if not end_time_index_found:
            self.fail("Missing index on 'end_time' for world_events collection")

if __name__ == "__main__":
    unittest.main()
