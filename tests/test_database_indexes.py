import pytest
import mongomock
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.create_database import create_tables

class TestDatabaseIndexes:
    def test_world_events_indexes_created(self):
        """
        Integration test verifying that create_tables() creates
        the required indexes for the 'world_events' collection using mongomock.
        """
        # Arrange: Create an in-memory MongoDB client
        client = mongomock.MongoClient()
        db = client.test_db

        # Act: Execute the schema creation function against the mock DB
        create_tables(db)

        # Assert: Verify indexes exist via index_information()
        # Default index names are usually field_1 (e.g., active_1)
        indexes = db.world_events.index_information()

        # Helper to check if an index exists for a specific key
        def has_index_on_field(field_name):
            for index_name, index_info in indexes.items():
                # index_info['key'] is a list of tuples like [('active', 1)]
                keys = index_info['key']
                if len(keys) == 1 and keys[0][0] == field_name:
                    return True
            return False

        assert has_index_on_field("active"), f"Missing index on 'active'. Found: {indexes}"
        assert has_index_on_field("end_time"), f"Missing index on 'end_time'. Found: {indexes}"

if __name__ == "__main__":
    pytest.main([__file__])
