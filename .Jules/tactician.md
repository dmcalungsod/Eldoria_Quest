## 2024-05-23 — Combat Action System

**Learning:** Implementing player choices (Defend, Flee) in a previously auto-resolved combat system requires careful routing. Simply replacing the "Battle" button with action buttons ("Attack", "Defend") breaks the implicit auto-combat for trivial fights.
**Action:** Implemented a hybrid routing in `AdventureSession.simulate_step`: Explicit "Attack" actions check the auto-combat condition (weak monster + high HP) to trigger the existing fast-forward logic, while "Defend" and "Flee" always force a single manual turn. This preserves QoL for grinding while enabling tactical depth for tough fights.

**Learning:** When mocking `discord.ui.View` for unit tests, ensured that mock classes implement methods expected by the view logic (e.g., `clear_items`), as strict typing or newer library versions might assume their presence.

## 2024-05-24 — Enemy Telegraph System

**Learning:** Monsters with high power skills (>= 1.5) felt unfair without telegraphs. Implemented a 50% chance for skills >= 1.5 power to telegraph their intent first.
**Action:** `CombatEngine` now supports "telegraph" and "execute_charge" actions, persisting state in `active_monster` to enable multi-turn combat logic.

## 2026-02-28 — Deterministic Auto-Combat Abstraction

**Learning:** Designing an abstraction formula to replace turn-based simulation requires creating "expected values" for variable mechanics (like crits, accuracy, and skill triggers). By taking average base power and multiplying by expected multipliers (e.g., 1 + crit_chance*(crit_mult-1)), we can derive a stable "DPS" value. Flooring chip damage and putting a ceiling on turns-to-kill prevents infinite math loops in extreme defense cases.
**Action:** Implemented `AutoCombatFormula.resolve_clash` taking into account stats, stances, and weather modifiers for background expedition resolution without invoking `CombatEngine` iteratively.
