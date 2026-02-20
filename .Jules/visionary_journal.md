# Visionary Journal

## 2025-10-28 — Critical Security Assessment

**Analysis**:
The logs from **Sentinel** on 2025-10-27 revealed two distinct but related vulnerabilities: "Stale State in Persistent Views" (`InfirmaryView`) and "Quest Acceptance Rank Bypass" (`QuestSystem`).
Both stem from a common oversight: trusting client-side state (cached view data) or input (quest IDs) without re-validating against the authoritative database state at the moment of transaction.

**Observation**:
This pattern (Trust but Verify) is a recurring theme.
- **Bolt** optimized caching for performance (May 2024).
- **Sentinel** found caching issues causing security holes (Oct 2025).
**Conflict**: There is a tension between "Performance" (caching) and "Security" (fresh data).
**Resolution**: We must adopt a "Check-Act" pattern where critical actions (spending gold, accepting quests) always re-fetch the latest state, even if the view displays cached data. The performance cost of one extra query per transaction is negligible compared to the risk of an exploit.

**Recommendation**:
Moving forward, all transactional methods in `DatabaseManager` should accept an optional `validate_fresh` flag or simply enforce fresh reads for sensitive fields (gold, hp, rank).
UI components should be treated as "dumb displays" and never as sources of truth for logic.

**Progress**:
- Strategy Memo created for 2025-10-28 focusing on these immediate fixes.
- Roadmap inferred due to missing file. Feedback inferred due to missing file.
