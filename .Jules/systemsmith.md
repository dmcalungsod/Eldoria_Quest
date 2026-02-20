## 2024-05-22 — Quest Update Desync

**Learning:** `AdventureRewards` was updating quest progress based on *potential* drops rather than *actual* drops, allowing players to complete collection quests without obtaining items.
**Action:** Always verify that reward processing logic operates on the *result* of RNG checks, not the input probabilities. Use explicit `actual_drops` lists.
