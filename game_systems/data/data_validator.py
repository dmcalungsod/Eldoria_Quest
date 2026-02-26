import logging
from typing import Any

logger = logging.getLogger("eldoria.data")


class DataValidator:
    """
    Centralized validation logic for game data files.
    Ensures that JSON data loaded from disk matches expected schemas.
    """

    @staticmethod
    def validate_location_schema(data: dict[str, Any]) -> list[str]:
        """
        Validates the schema of adventure locations.

        Args:
            data: The dictionary of location data loaded from JSON.

        Returns:
            A list of error messages. Empty list if validation passes.
        """
        errors = []

        required_keys = {
            "name",
            "emoji",
            "min_rank",
            "level_req",
            "duration_options",
            "monsters",
            "description",
        }

        for loc_id, loc_data in data.items():
            # 1. Check required keys
            missing_keys = required_keys - loc_data.keys()
            if missing_keys:
                errors.append(f"Location '{loc_id}' missing required keys: {missing_keys}")
                continue  # Skip further checks for this location to avoid crashes

            # 2. Check types
            if not isinstance(loc_data["name"], str):
                errors.append(f"Location '{loc_id}': 'name' must be a string.")
            if not isinstance(loc_data["emoji"], str):
                errors.append(f"Location '{loc_id}': 'emoji' must be a string.")
            if not isinstance(loc_data["min_rank"], str):
                errors.append(f"Location '{loc_id}': 'min_rank' must be a string.")
            if not isinstance(loc_data["level_req"], int):
                errors.append(f"Location '{loc_id}': 'level_req' must be an integer.")
            if not isinstance(loc_data["duration_options"], list):
                errors.append(f"Location '{loc_id}': 'duration_options' must be a list of integers.")
            else:
                if not all(isinstance(d, int) for d in loc_data["duration_options"]):
                    errors.append(f"Location '{loc_id}': 'duration_options' contains non-integer values.")

            if not isinstance(loc_data["monsters"], list):
                errors.append(f"Location '{loc_id}': 'monsters' must be a list.")
            else:
                # Validate monster entries: [monster_id, weight]
                for idx, entry in enumerate(loc_data["monsters"]):
                    if not isinstance(entry, list | tuple) or len(entry) != 2:
                        errors.append(f"Location '{loc_id}': 'monsters' entry at index {idx} must be [id, weight].")
                    elif not isinstance(entry[0], str) or not isinstance(entry[1], int):
                        errors.append(
                            f"Location '{loc_id}': 'monsters' entry at index {idx} has invalid types (expected [str, int])."
                        )

            if not isinstance(loc_data["description"], str):
                errors.append(f"Location '{loc_id}': 'description' must be a string.")

            # 3. Check optional keys structure
            if "night_monsters" in loc_data:
                if not isinstance(loc_data["night_monsters"], list):
                    errors.append(f"Location '{loc_id}': 'night_monsters' must be a list.")
                else:
                    for idx, entry in enumerate(loc_data["night_monsters"]):
                        if not isinstance(entry, list | tuple) or len(entry) != 2:
                            errors.append(
                                f"Location '{loc_id}': 'night_monsters' entry at index {idx} must be [id, weight]."
                            )
                        elif not isinstance(entry[0], str) or not isinstance(entry[1], int):
                            errors.append(
                                f"Location '{loc_id}': 'night_monsters' entry at index {idx} has invalid types (expected [str, int])."
                            )

            if "gatherables" in loc_data:
                if not isinstance(loc_data["gatherables"], list):
                    errors.append(f"Location '{loc_id}': 'gatherables' must be a list.")
                else:
                    for idx, entry in enumerate(loc_data["gatherables"]):
                        if not isinstance(entry, list | tuple) or len(entry) != 2:
                            errors.append(
                                f"Location '{loc_id}': 'gatherables' entry at index {idx} must be [id, weight]."
                            )
                        elif not isinstance(entry[0], str) or not isinstance(entry[1], int):
                            errors.append(
                                f"Location '{loc_id}': 'gatherables' entry at index {idx} has invalid types (expected [str, int])."
                            )

            if "conditional_monsters" in loc_data:
                if not isinstance(loc_data["conditional_monsters"], list):
                    errors.append(f"Location '{loc_id}': 'conditional_monsters' must be a list.")
                else:
                    for idx, entry in enumerate(loc_data["conditional_monsters"]):
                        if not isinstance(entry, dict):
                            errors.append(
                                f"Location '{loc_id}': 'conditional_monsters' entry at index {idx} must be a dict."
                            )
                        else:
                            if "monster_key" not in entry or "weight" not in entry:
                                errors.append(
                                    f"Location '{loc_id}': 'conditional_monsters' entry at index {idx} missing keys."
                                )

            if "special_events" in loc_data:
                if not isinstance(loc_data["special_events"], list):
                    errors.append(f"Location '{loc_id}': 'special_events' must be a list of strings.")
                elif not all(isinstance(e, str) for e in loc_data["special_events"]):
                    errors.append(f"Location '{loc_id}': 'special_events' must contain only strings.")

        return errors
