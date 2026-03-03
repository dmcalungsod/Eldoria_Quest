import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from db_helper import get_guild_members, get_players  # noqa: E402


def main():
    players = get_players()
    guild_members = get_guild_members()

    if not players:
        print("No player data available. Skipping analysis.")
        return

    # Index guild members by discord_id for fast lookup
    guild_index = {m["discord_id"]: m for m in guild_members}

    total_players = 0
    level_counts = Counter()
    rank_counts = Counter()
    class_counts = Counter()

    for player in players:
        total_players += 1
        level = player.get("level", 1)
        level_counts[level] += 1

        class_id = player.get("class_id")
        class_counts[class_id] += 1

        discord_id = player.get("discord_id")
        guild_member = guild_index.get(discord_id)
        if guild_member:
            rank = guild_member.get("rank", "F")
            rank_counts[rank] += 1

    print(f"Total Players:     {total_players}")
    print("\nLevel Distribution:")
    for level in sorted(level_counts):
        print(f"  Level {level:>3}: {level_counts[level]} players")

    print("\nRank Distribution:")
    for rank in sorted(rank_counts):
        print(f"  Rank {rank}: {rank_counts[rank]} players")

    print("\nClass Distribution:")
    for class_id in sorted(class_counts, key=lambda x: (x is None, x)):
        label = f"Class {class_id}" if class_id is not None else "No Class"
        print(f"  {label}: {class_counts[class_id]} players")


if __name__ == "__main__":
    main()
