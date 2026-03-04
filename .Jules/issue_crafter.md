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


## 2026-02-28
**Summary:**
- Scanned recent agent logs (2026-02-28) and audit reports (2026-02-28).
- Identified 6 new issues: 2 content expansions, 1 security vulnerability, 2 tech debt items, and 1 UX violation.
- Appended issues #9-#14 to tracking.

**Created Issues:**
9.  **[Feature] Implement The Wailing Chasm Region Mechanics & Content** (Source: Realmwright)
10. **[Content] Implement "The Blind Choir's Requiem" Questline** (Source: Questweaver)
11. **[UX] Fix ONE UI Policy Violations in Quest Hub and Tournament** (Source: Repo Auditor)
12. **[Security] Fix urlopen security risk in post_update.py** (Source: Repo Auditor)
13. **[Tech Debt] Refactor High Complexity UI methods in Shop and Infirmary** (Source: Repo Auditor)
14. **[Test] Improve Test Coverage for Cogs and Adventure Menu** (Source: Repo Auditor)

**Notes:**
- The Wailing Chasm introduces new light/sanity mechanics that Grimwarden will need to implement.
- The Blind Choir questline requires coordination across multiple agents (GameForge, Equipper, ChronicleKeeper, StoryWeaver) to add the new monsters, items, and achievements.
- ONE UI policy violations and High Complexity UI methods should be refactored to clean up tech debt.

## 2026-03-01
**Summary:**
- Scanned recent agent logs (2026-03-01), the Visionary memo (2026-03-01), and the Audit report (2026-03-01).
- Identified 7 new issues spanning game balance, feature expansion, bug fixes, and technical debt.
- Appended issues #17-#23 to `NEW_ISSUES.md`.

**Created Issues:**
17. **[Balance] Economy Imbalance in Adventure Locations** (Source: Analyst/Visionary)
18. **[Feature] Implement The Silent City of Ouros Region Mechanics & Content** (Source: Realmwright)
19. **[Bug] Fix "buff_data" typo in skills_data.py** (Source: Visionary)
20. **[Bug] Missing Monsters for "The Blind Choir's Requiem"** (Source: Visionary)
21. **[Bug] Missing schema fields in Frostfall Expanse locations** (Source: Visionary)
22. **[Tech Debt] Refactor High Cyclomatic Complexity in Core/UI methods** (Source: Repo Auditor)
23. **[Tech Debt] Remove Dead Code (Unused Variables)** (Source: Repo Auditor)

**Notes:**
- Economy balance issues from Analyst's EV modeling are critical for Phase 2 tuning and have been assigned to GameBalancer.
- The Realmwright added The Silent City of Ouros, which requires work from GameForge, Tactician, and DepthsWarden.
- Three critical bugs were highlighted in the Nexus report via Visionary, including the "buff_data" typo in skills_data.py which breaks the combat engine, and missing dependencies for The Blind Choir quest.
- Repo Auditor identified high cyclomatic complexity and unused variables which add technical debt to the codebase.

## 2026-03-02 (Second Update)
**Summary:**
- Scanned Repo Auditor logs (`.Jules/audit_report_2026-03-02.md`).
- Identified 2 new issues related to medium-severity security warnings and dead code technical debt.
- Appended issues to `NEW_ISSUES.md`.

**Created Issues:**
14. **[Security] Fix Medium B310 vulnerability in post_update.py** (Source: Repo Auditor)
15. **[Tech Debt] Clean up Dead Code from Vulture Findings** (Source: Repo Auditor)

**Notes:**
- The B310 vulnerability is an actionable security issue assigned to Sentinel.
- Dead code identified by Vulture requires cleanup by SystemSmith and BugHunter.

## 2026-03-08
**Summary:**
- Scanned recent agent logs (2026-03-02, 2026-03-03, 2026-03-08) and design documents (expansion_guild_halls.md, region_ironhaven.md).
- Identified 3 new issues requiring tracking: 2 major feature expansions and 1 testing bug.
- Created `NEW_ISSUES.md` with detailed descriptions.

**Created Issues:**
29. **[Feature] Implement Guild Halls Expansion** (Source: Architect)
30. **[Feature] Implement Ironhaven Region Mechanics & Content** (Source: Realmwright)
31. **[Bug] Fix missing discord mock in test_guild_advisor.py** (Source: Jules)

**Notes:**
- Guild Halls expansion requires major economy balancing and database integration.
- Ironhaven region introduces Cold and Altitude survival mechanics which require input from multiple agents, specifically Grimwarden.
- A minor bug in `test_guild_advisor.py` was caught by Jules during a lint pass and requires a proper mock.
