# Palette's UX Journal

## 2024-10-26 - Visualizing Vital Stats
**Learning:** Text-based vital stats (HP: 100/100) are hard to parse quickly in high-stakes situations like combat. Visual bars (HP: `█████░░░░░` 50/100) provide immediate "at-a-glance" status updates, reducing cognitive load.
**Action:** When displaying numeric ranges (HP, MP, XP, Durability) that affect decision-making, always accompany them with a visual progress bar or indicator.

## 2025-05-18 - Consistent Progress Bars
**Learning:** Reusing the same visual language (block characters `█`/`░`) for progress bars across different screens (Combat vs Profile) builds familiarity and reduces learning curve.
**Action:** Use the shared utility `cogs.ui_helpers.make_progress_bar` to ensure consistent visualization styles across the app.
