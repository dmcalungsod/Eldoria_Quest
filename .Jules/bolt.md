## 2024-05-23 — Mixed Updates in MongoDB

**Learning:** MongoDB allows mixing `$set` and `$inc` operators in a single `update_one` call, provided they target different fields.
**Action:** Use `update_player_mixed` pattern when updating absolute values (like HP) and relative values (like Vestige) simultaneously to save a round-trip.
