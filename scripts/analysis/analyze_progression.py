import sys
import os
import json
from collections import Counter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from database.database_manager import DatabaseManager

def main():
    db = DatabaseManager()

    players = db._col('players').find()

    total_players = 0
    level_counts = Counter()
    rank_counts = Counter()
    class_counts = Counter()

    for player in players:
        total_players += 1
        level = player.get('level', 1)
        level_counts[level] += 1
        class_id = player.get('class_id')
        class_counts[class_id] += 1

        discord_id = player.get('discord_id')
        guild_member = db.get_guild_member_data(discord_id)
        if guild_member:
            rank = guild_member.get('rank', 'F')
            rank_counts[rank] += 1

    print(f"Total Players: {total_players}")
    print(f"Level Distribution: {dict(level_counts)}")
    print(f"Rank Distribution: {dict(rank_counts)}")
    print(f"Class Distribution: {dict(class_counts)}")

if __name__ == "__main__":
    main()
