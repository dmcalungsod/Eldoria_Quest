"""
Player Creator for Eldoria Quest

Handles:
- Creating player profiles
- Creating base stats from class definitions
- Validating class IDs
"""

from .player_stats import PlayerStats
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS


class PlayerCreator:
    def __init__(self, db):
        self.db = db

    def create_player(
        self,
        discord_id: int,
        username: str,
        class_id: int,
        race: str = None,
        gender: str = None,
    ):
        """Creates a new player after validating class ID and ensuring no duplicates."""

        # Check if player already exists
        if self.db.player_exists(discord_id):
            return False, "You already created a character."

        # Locate class by ID
        class_name = None
        for name, data in CLASS_DEFINITIONS.items():
            if data["id"] == class_id:
                class_name = name
                break

        if not class_name:
            return False, "Invalid class ID."

        class_data = CLASS_DEFINITIONS[class_name]

        # Create a stats object to calculate initial HP/MP
        stats = PlayerStats(
            str_base=class_data["stats"]["STR"],
            end_base=class_data["stats"]["END"],
            dex_base=class_data["stats"]["DEX"],
            agi_base=class_data["stats"]["AGI"],
            mag_base=class_data["stats"]["MAG"],
            lck_base=class_data["stats"]["LCK"],
        )

        # Get initial max HP and MP from the new stats object
        initial_hp = stats.max_hp
        initial_mp = stats.max_mp

        # Save to database
        self.db.create_player(
            discord_id=discord_id,
            name=username,
            class_id=class_id,
            race=race,
            gender=gender,
            stats_data=stats.to_dict(),
            initial_hp=initial_hp,
            initial_mp=initial_mp,
        )

        # --- THIS IS THE FIX: Add default skills ---
        conn = None
        try:
            conn = self.db.connect()
            cur = conn.cursor()

            # 1. Find all default skills (learn_cost = 0) for this class_id
            # --- MODIFIED QUERY ---
            cur.execute(
                "SELECT key_id FROM skills WHERE class_id = ? AND learn_cost = 0", 
                (class_id,)
            )
            # --- END OF MODIFICATION ---
            
            default_skills = cur.fetchall()

            # 2. Add them to the player_skills table
            for skill in default_skills:
                cur.execute(
                    """
                    INSERT INTO player_skills (discord_id, skill_key, skill_level)
                    VALUES (?, ?, 1)
                    """,
                    (discord_id, skill["key_id"]),
                )

            conn.commit()
        except Exception as e:
            print(f"Error adding default skills for {discord_id}: {e}")
            # We can just log this and not fail character creation
        finally:
            if conn:
                conn.close()
        # --- END OF FIX ---

        return True, f"Welcome **{username}**, you are now a **{class_name}**!"