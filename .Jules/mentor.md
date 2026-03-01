## 2026-02-27 — [Mentor: Auto-Adventure Onboarding]

**Learning:** New players lacked guidance regarding the recently implemented Auto-Adventure System (Expeditions), which is a core feature. They need an introduction immediately after completing or skipping the combat tutorial.
**Action:** In `cogs/onboarding_cog.py`, updated `transition_to_guild_lobby` to add an "🗺️ Expeditions" field to the Guild Lobby embed. This message seamlessly introduces the time-based exploration mechanic and directs them to their profile, adhering to the One UI Policy by editing the existing message.

## 2026-03-01 — [Mentor: Auto-Adventure Setup Guide]

**Learning:** New players needed immediate context directly on the screen where they initiate expeditions (the Adventure Setup menu), specifically on how time-based mechanics and auto-retreats function.
**Action:** In `game_systems/character/ui/adventure_menu.py`, added a "How Expeditions Work" tutorial button that sends an ephemeral embed with an explanation of Time-Based Exploration, Supplies, and Hazards & Retreat. This perfectly follows the One UI Policy while delivering necessary information at the exact point of action.
