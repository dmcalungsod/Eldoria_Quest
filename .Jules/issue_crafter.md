# 🐞 Issue Crafter Journal

## 2026-02-27
**Summary:**
- Scanned recent agent logs (2026-02-23 to 2026-02-26) and project plans.
- Identified 8 key issues requiring tracking.
- Created `NEW_ISSUES.md` with detailed descriptions.

**Created Issues:**
1.  **[Feature] Auto-Adventure: Loot Table & Drop Rate Tuning** (Task 2.2)
2.  **[Feature] Auto-Adventure: Fatigue System** (Task 2.3)
3.  **[Feature] Auto-Adventure: Travel Supplies (Rations & Torches)** (Task 3.3)
4.  **[Test] Auto-Adventure: Stress Test Scheduler** (Task 4.1)
5.  **[Test] Auto-Adventure: Exploit Verification** (Task 4.2)
6.  **[Feature] The Eldoria Codex System**
7.  **[Feature] Alchemist Class Implementation**
8.  **[UX] Implement One UI Policy**

**Notes:**
- The Auto-Adventure project is progressing well (Phase 2/3), but these issues are critical for the final polish.
- The Codex System is a major new feature that will address player feedback for "More Lore".

## 2026-03-02
**Summary:**
- Scanned recent agent logs (2026-02-27), audit reports (2026-03-01), and design documents.
- Identified 5 new issues: 1 major feature expansion, 1 critical security vulnerability, and 3 high-priority technical debt items.
- Appended issues #9-#13 to `NEW_ISSUES.md`.

**Created Issues:**
9.  **[Feature] Warrior Skill Tree Expansion** (Source: Architect Design)
10. **[Security] Critical pip Vulnerability** (Source: Repo Auditor)
11. **[Tech Debt] Refactor CombatEngine.run_combat_turn** (Source: Repo Auditor)
12. **[Tech Debt] Refactor AdventureEvents.regeneration** (Source: Repo Auditor)
13. **[Tech Debt] Refactor AdventureSession.simulate_step** (Source: Repo Auditor)

**Notes:**
- The Warrior Skill Tree expansion is ready for implementation by GameForge and Tactician.
- The pip vulnerability is critical and should be addressed immediately by Sentinel.
- Technical debt in core systems (Combat, Adventure) is reaching critical levels (Complexity F) and requires refactoring by SystemSmith.

## 2026-03-04
**Summary:**
- Scanned recent agent logs (2026-03-03) and project plans.
- Verified that the "Frostfall Expanse ID Conflict" (106-110) was resolved (Frostfall now uses 111-115).
- Identified 3 new issues related to event content, QA, and balance monitoring.
- Appended issues #14-#16 to `NEW_ISSUES.md`.

**Created Issues:**
14. **[Content] Frostfall Expedition Announcement** (Source: EventHerald)
15. **[QA] Verify Frostfall Drop Rates** (Source: EventHerald)
16. **[Balance] Monitor Deepgrove Roots Progression** (Source: Equilibrium)

**Notes:**
- Namewright has finalized Alchemist and Supply names; implementation tasks are covered by existing issues #7 (Alchemist) and #3 (Supplies).
- The Frostfall Expedition event is implemented, pending announcement and drop rate verification.
- Deepgrove Roots balance changes (nerfing Feral Stag) are live; monitoring is required to ensure smooth progression.
