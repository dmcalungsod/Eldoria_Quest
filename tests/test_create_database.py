import os
import sys
import unittest
from unittest.mock import MagicMock

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

        # Call the function
        create_tables(mock_db)

        # In the refactored loop, db[col_name] is accessed via __getitem__
        # So the actual collection object is mock_db.__getitem__("world_events")
        world_events_mock = mock_db.__getitem__("world_events")

        # Check all calls to create_index on this collection
        calls = world_events_mock.create_index.call_args_list

        active_index_found = False
        end_time_index_found = False

        print("\nVerifying world_events indexes:")
        for call in calls:
            args, _ = call
            # args[0] is typically a list of tuples like [( "active", ASCENDING )]
            # or a tuple. Extract the key name.
            if args:
                index_keys = args[0]
                if isinstance(index_keys, tuple) and index_keys[0] == "active":
                    active_index_found = True
                elif isinstance(index_keys, tuple) and index_keys[0] == "end_time":
                    end_time_index_found = True
                elif isinstance(index_keys, str):
                    if index_keys == "active":
                        active_index_found = True
                    elif index_keys == "end_time":
                        end_time_index_found = True

        if not active_index_found:
            self.fail("Missing index on 'active' for world_events collection")
        if not end_time_index_found:
            self.fail("Missing index on 'end_time' for world_events collection")


if __name__ == "__main__":
    unittest.main()
