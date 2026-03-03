import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import SKILL_SCHEMA

logger = logging.getLogger("eldoria.data")

def load_skills():
    """
    Loads skill data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "skills.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: skills.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: skills.json is invalid JSON: {e}")
        return {}

    # Validate Schema
    top_schema = {"type": dict, "values_schema": {"type": dict, "schema": SKILL_SCHEMA}}

    errors = DataValidator.validate(data, top_schema, "skills")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded skill data contains schema errors.")

    logger.info(f"Loaded {len(data)} skills from {data_path.name}")
    return data

class SkillData:
    _skills = None

    @classmethod
    def get_all(cls):
        if cls._skills is None:
            cls._skills = load_skills()
        return cls._skills

def __getattr__(name):
    if name == "SKILLS":
        return SkillData.get_all()
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = ["SkillData"]
