import logging
from typing import Any, List, Dict

logger = logging.getLogger("eldoria.data")


class DataValidator:
    """
    Centralized validation logic for game data files using declarative schemas.
    """

    @staticmethod
    def validate(data: Any, schema: Dict[str, Any], path: str = "") -> List[str]:
        """
        Validates data against a schema.

        Args:
            data: The data to validate.
            schema: The schema definition.
            path: Current path in the data structure (for error messages).

        Returns:
            List of error messages.
        """
        errors = []

        # 1. Type Check
        type_errors = DataValidator._validate_type(data, schema, path)
        if type_errors:
            return type_errors

        # 2. Options Check (Enum)
        options_errors = DataValidator._validate_options(data, schema, path)
        if options_errors:
            return options_errors

        # 3. Range Checks
        errors.extend(DataValidator._validate_range(data, schema, path))

        # 4. List Validation
        if isinstance(data, list):
            errors.extend(DataValidator._validate_list(data, schema, path))

        # 5. Dict Validation
        if isinstance(data, dict):
            errors.extend(DataValidator._validate_dict(data, schema, path))

        return errors

    @staticmethod
    def _validate_type(data: Any, schema: Dict[str, Any], path: str) -> List[str]:
        expected_type = schema.get("type")
        if expected_type:
            if not isinstance(data, expected_type):
                return [f"{path}: Expected type {expected_type.__name__}, got {type(data).__name__}"]
        return []

    @staticmethod
    def _validate_options(data: Any, schema: Dict[str, Any], path: str) -> List[str]:
        if "options" in schema and data not in schema["options"]:
            return [f"{path}: Value '{data}' is not in valid options: {schema['options']}"]
        return []

    @staticmethod
    def _validate_range(data: Any, schema: Dict[str, Any], path: str) -> List[str]:
        errors = []
        if isinstance(data, (int, float)):
            if "min" in schema and data < schema["min"]:
                errors.append(f"{path}: Value {data} is less than minimum {schema['min']}")
            if "max" in schema and data > schema["max"]:
                errors.append(f"{path}: Value {data} is greater than maximum {schema['max']}")
        return errors

    @staticmethod
    def _validate_list(data: List[Any], schema: Dict[str, Any], path: str) -> List[str]:
        errors = []
        # Length check
        if "length" in schema and len(data) != schema["length"]:
            errors.append(f"{path}: Expected list length {schema['length']}, got {len(data)}")

        # Homogeneous list validation
        if "element_schema" in schema:
            for idx, item in enumerate(data):
                errors.extend(DataValidator.validate(item, schema["element_schema"], f"{path}[{idx}]"))

        # Fixed-structure list (tuple-like) validation
        if "elements" in schema:
            if len(data) != len(schema["elements"]):
                # checked by length if present, otherwise safe to ignore or warn
                pass
            else:
                for idx, (item, item_schema) in enumerate(zip(data, schema["elements"])):
                    errors.extend(DataValidator.validate(item, item_schema, f"{path}[{idx}]"))
        return errors

    @staticmethod
    def _validate_dict(data: Dict[str, Any], schema: Dict[str, Any], path: str) -> List[str]:
        errors = []
        # Keys Schema (all keys must match)
        if "keys_schema" in schema:
            for key in data.keys():
                errors.extend(DataValidator.validate(key, schema["keys_schema"], f"{path}.key({key})"))

        # Values Schema (all values must match)
        if "values_schema" in schema:
            for key, value in data.items():
                errors.extend(DataValidator.validate(value, schema["values_schema"], f"{path}[{key}]"))

        # Specific structure validation (schema for specific keys)
        if "schema" in schema:
            nested_schema = schema["schema"]

            # Check required fields
            for key, field_schema in nested_schema.items():
                if field_schema.get("required", False) and key not in data:
                    errors.append(f"{path}: Missing required key '{key}'")

            # Check defined fields
            for key, value in data.items():
                if key in nested_schema:
                    errors.extend(DataValidator.validate(value, nested_schema[key], f"{path}.{key}"))
                # We typically allow extra fields unless strict mode (not implemented)
        return errors

    @staticmethod
    def validate_location_schema(data: dict[str, Any]) -> List[str]:
        """
        Deprecated: Wrapper for backward compatibility using the new schema system.
        """
        from game_systems.data.schemas import LOCATION_SCHEMA

        # The top level data is a dict of {id: location_data}
        # We validate it as a dict where values must match LOCATION_SCHEMA
        top_schema = {
            "type": dict,
            "values_schema": {
                "type": dict,
                "schema": LOCATION_SCHEMA
            }
        }
        return DataValidator.validate(data, top_schema, "locations")
