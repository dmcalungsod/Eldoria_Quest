# Repo Auditor Journal

## 2026-02-23 - Initial Audit

### Effective Tools
- **Bandit**: Identified weak randomness (B311) which is common in game logic but good to flag. Also found `subprocess` usage.
- **Flake8**: Very noisy with `E501` (line length), but useful for spotting potential syntax/style issues if filtered.
- **Radon**: Excellent for pinpointing complex functions (`CombatEngine.run_combat_turn`).
- **Vulture**: Successfully identified unused variables in tests and main logic.

### Recurring Patterns
- **Complexity**: Core game loops (combat, adventure steps) tend to grow into large, monolithic functions (God Objects/Methods).
- **Test Gaps**: UI interactions (Discord Views/Modals) are hard to test and thus have very low coverage compared to data models.
- **Style**: Line length limits are frequently exceeded, likely due to narrative text strings.

### Limitations
- **False Positives**: Bandit flags `random` usage which is intended for gameplay, not cryptography.
- **Context Awareness**: Static analysis cannot easily verify logical flow across async Discord interactions (e.g., "ONE UI" violations).

### Suggestions
- **Pre-commit Hooks**: Add `flake8` and `black`/`ruff` to prevent style regression.
- **CI**: Integrate `radon` to fail builds if complexity exceeds a threshold (e.g., C or D).
