"""
test_data_validation.py

Tests for the centralized DataValidator and Schema system.
"""

from game_systems.data.data_validator import DataValidator


class TestDataValidator:
    def test_basic_validation(self):
        schema = {"type": str}
        assert DataValidator.validate("hello", schema) == []
        assert len(DataValidator.validate(123, schema)) == 1

    def test_nested_dict(self):
        schema = {"type": dict, "schema": {"name": {"type": str, "required": True}, "age": {"type": int}}}

        valid_data = {"name": "Alice", "age": 30}
        assert DataValidator.validate(valid_data, schema) == []

        invalid_data = {"age": 30}  # Missing name
        assert len(DataValidator.validate(invalid_data, schema)) == 1

        invalid_type = {"name": "Bob", "age": "thirty"}
        assert len(DataValidator.validate(invalid_type, schema)) == 1

    def test_list_validation(self):
        schema = {"type": list, "element_schema": {"type": int}}

        valid_data = [1, 2, 3]
        assert DataValidator.validate(valid_data, schema) == []

        invalid_data = [1, "two", 3]
        assert len(DataValidator.validate(invalid_data, schema)) == 1

    def test_tuple_validation(self):
        schema = {"type": list, "elements": [{"type": str}, {"type": int}]}

        valid_data = ["item", 10]
        assert DataValidator.validate(valid_data, schema) == []

        invalid_data = ["item", "10"]
        assert len(DataValidator.validate(invalid_data, schema)) == 1

    def test_adventure_locations_integration(self):
        from game_systems.data.adventure_locations import LOCATIONS

        assert len(LOCATIONS) > 0
        # If LOCATIONS loaded, it means validation passed (or logged warnings)
        # We can explicitly validate one to be sure
        first_loc = list(LOCATIONS.values())[0]
        # Note: In memory, lists are converted to tuples, so we can't strictly validate against JSON schema
        # But we can check basic fields
        assert isinstance(first_loc["name"], str)

    def test_monsters_integration(self):
        from game_systems.data.monsters import MONSTERS

        assert len(MONSTERS) > 0
        # In memory, drops are tuples, skills are objects
        # Validation happens on load, so we just ensure load success

    def test_consumables_integration(self):
        from game_systems.data.consumables import CONSUMABLES

        assert len(CONSUMABLES) > 0

    def test_equipments_integration(self):
        from game_systems.data.equipments import EQUIPMENT_DATA

        assert len(EQUIPMENT_DATA) > 0
