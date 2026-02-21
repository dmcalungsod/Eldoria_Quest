# Regression Hunter Journal

## Critical Learnings

### 2024-05-23: Adventure Death Penalty
- **Area:** Adventure System / Economy
- **Risk:** High (Economy inflation if penalties fail)
- **Test:** `tests/test_adventure_death_penalty.py`
- **Pattern:** Mocking `AdventureSession` class within `game_systems.adventure.adventure_manager` allowed control over internal session state (`loot`) and behavior (`simulate_step` returning `dead=True`), avoiding complex setup of a real session.
- **Key Insight:** `AdventureManager` calculates penalties based on *current* player Aurum (database fetch) and *session* loot. Testing both requires mocking DB returns and session object state simultaneously.
