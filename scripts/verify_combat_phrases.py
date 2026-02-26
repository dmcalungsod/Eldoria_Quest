"""
verify_combat_phrases.py

Verification script for Alchemist combat phrases.
Checks basic attack narration and skill specific phrases.
"""

from game_systems.combat.combat_phrases import CombatPhrases

def main():
    print("=== Verifying Alchemist Combat Phrases ===\n")

    # 1. Verify Basic Attacks (Class ID 6)
    print("--- Alchemist Basic Attacks ---")
    mock_player = {}
    mock_monster = {"name": "Test Dummy"}

    # Generate 10 samples to see variety
    for i in range(10):
        is_crit = i % 5 == 0  # Every 5th is a crit
        phrase = CombatPhrases.player_attack(mock_player, mock_monster, 10, is_crit, player_class_id=6)
        print(f"[{'CRIT' if is_crit else 'NORM'}] {phrase}")

    print("\n--- Alchemist Skill Phrases ---")

    skills_to_test = [
        {"key_id": "vitriol_bomb", "name": "Vitriol Bomb"},
        {"key_id": "fulminating_compound", "name": "Fulminating Compound"},
        {"key_id": "mutagenic_serum", "name": "Mutagenic Serum"}
    ]

    for skill in skills_to_test:
        print(f"\nTesting Skill: {skill['name']}")
        for i in range(3):
            is_crit = i == 2
            phrase = CombatPhrases.player_skill(mock_player, mock_monster, skill, 50, is_crit)
            print(f"- {phrase}")

if __name__ == "__main__":
    main()
