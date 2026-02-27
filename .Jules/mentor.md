## 2026-02-27 — [Mentor: Auto-Adventure Onboarding]

**Learning:** New players lacked guidance regarding the recently implemented Auto-Adventure System (Expeditions), which is a core feature. They need an introduction immediately after completing or skipping the combat tutorial.
**Action:** In `cogs/onboarding_cog.py`, updated `transition_to_guild_lobby` to add an "🗺️ Expeditions" field to the Guild Lobby embed. This message seamlessly introduces the time-based exploration mechanic and directs them to their profile, adhering to the One UI Policy by editing the existing message.
