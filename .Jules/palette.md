# Palette's UX Journal

## 2024-10-26 - Visualizing Vital Stats
**Learning:** Text-based vital stats (HP: 100/100) are hard to parse quickly in high-stakes situations like combat. Visual bars (HP: `█████░░░░░` 50/100) provide immediate "at-a-glance" status updates, reducing cognitive load.
**Action:** When displaying numeric ranges (HP, MP, XP, Durability) that affect decision-making, always accompany them with a visual progress bar or indicator.

## 2025-05-18 - Consistent Progress Bars
**Learning:** Reusing the same visual language (block characters `█`/`░`) for progress bars across different screens (Combat vs Profile) builds familiarity and reduces learning curve.
**Action:** Use the shared utility `cogs.ui_helpers.make_progress_bar` to ensure consistent visualization styles across the app.

## 2025-05-18 - [Locked Content Discovery]
**Learning:** Hiding locked content reduces discoverability. Showing locked options with clear visual indicators (🔒) and requirement explanations (Req: Rank X) motivates users to progress.
**Action:** When restricting choices in Select Menus, use 'Soft Disabling': Keep the option, modify the label to indicate lock status, and reject the interaction with an ephemeral explanation.

## 2025-05-19 - [Affordability Feedback]
**Learning:** In strict Discord Select Menus where individual options cannot be disabled, users need immediate visual feedback on which items they can afford *before* clicking.
**Action:** Use distinct emoji (🔒 vs 🪙) and label suffixes (`[Too Expensive]`) to indicate affordability state within Select options, preventing frustrating interaction failures.

## 2025-05-23 - [Empty State Turn-In Feedback]
**Learning:** Presenting a "disabled" state (like a grayed-out dropdown) without explaining *why* the action is unavailable creates a frustrating dead end.
**Action:** When a primary action (like Quest Turn-In) is unavailable, replace the generic empty state with actionable feedback—specifically listing the *progress* of incomplete tasks so the user knows exactly what remains to be done.

## 2025-05-23 - [Context-Aware Button States]
**Learning:** In turn-based interfaces where mistakes are costly (like death), changing button style (Green -> Red) based on critical status (Low HP) provides vital, non-textual warnings.
**Action:** Use `discord.ButtonStyle.danger` to signal "Caution" on primary actions when user vitals are critical (<30%), preventing accidental progression into danger.
