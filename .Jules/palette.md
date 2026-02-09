## 2024-10-26 - Visualizing Vital Stats
**Learning:** Text-based vital stats (HP: 100/100) are hard to parse quickly in high-stakes situations like combat. Visual bars (HP: `█████░░░░░` 50/100) provide immediate "at-a-glance" status updates, reducing cognitive load.
**Action:** When displaying numeric ranges (HP, MP, XP, Durability) that affect decision-making, always accompany them with a visual progress bar or indicator.

## 2024-05-22 - Shared UI Components for Consistency
**Learning:** Reusing UI components like progress bars across different views (Profile, Status Update) creates a cohesive visual language and reduces code duplication.
**Action:** Extract common UI patterns (bars, standard embed formats) into `cogs.ui_helpers` to ensure consistency.
