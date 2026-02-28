import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("json_verifier")


def verify_json_file(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            json.load(f)
        logger.info(f"✅ JSON Valid: {filepath}")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Error in {filepath}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error reading {filepath}: {e}")
        return False


def main():
    files_to_check = [
        "game_systems/data/adventure_locations.json",
        "game_systems/data/monsters.json",
        "game_systems/data/materials.json",
        "game_systems/data/quest_items.json",
    ]

    all_valid = True
    for fpath in files_to_check:
        if not verify_json_file(fpath):
            all_valid = False

    if all_valid:
        logger.info("All JSON files are valid.")
        sys.exit(0)
    else:
        logger.error("JSON validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
