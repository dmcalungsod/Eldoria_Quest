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

## 2026-03-01 — Implementing the Silence Mechanic

**Learning:** When implementing transient combat state effects in the Eldoria Quest engine (like the Silence mechanic, which mirrors the Stun mechanic), it is critical to not only process and return the state from the `CombatEngine`, but to manually propagate that state back into the `player_stats` object in `adventure_session.py`. Because the Discord bot is stateless between turns, failure to explicitly map `self.active_monster["player_silenced"]` into `context["player_stats"].is_silenced` will result in the state immediately dropping on the next turn. Additionally, any new binary flags for state must be manually added to mock player objects in all relevant test files.
**Action:** Always verify the full lifecycle of a status effect: `Status Applied (Engine) -> Saved (Session/Database) -> Re-Injected (Next Turn Context) -> Enforced (Engine) -> Consumed`.

## 2026-03-04 — Auto-Combat Integration

**Learning:** Auto-adventure combat logic bypasses the turn-by-turn simulation loop in favor of a deterministic formula (`AutoCombatFormula`). New passive mechanics like `kill_heal_percent` and `self_damage_percent` must be translated into raw DPS/mitigation adjustments within this formula to ensure players using auto-adventures still benefit from their class features.
**Action:** When adding new combat mechanics, always verify if they need an equivalent approximation in `game_systems/combat/auto_combat_formula.py`.
