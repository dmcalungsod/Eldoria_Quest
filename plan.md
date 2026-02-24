# Repository Organization Plan

## Overview
This document outlines the strategy to organize the Eldoria Quest repository to align with the structure defined in `README.md` and enforce clean coding practices. It introduces a new autonomous agent, the **Custodian**, responsible for maintaining this structure.

## New Agent: Custodian
- **Role**: Repository Organization & Structure Enforcement.
- **Schedule**: Weekly (Sundays).
- **Responsibilities**:
  - Scan the root directory for loose files (scripts, temporary logs, etc.) and move them to appropriate folders.
  - Verify that `game_systems/` modules are categorized correctly.
  - Ensure `README.md` reflects the actual file structure.
  - Maintain the cleanliness of `cogs/` by moving helper utilities to `cogs/utils/`.

## Proposed Changes

### 1. Root Directory Cleanup
The root directory should only contain essential project configuration and documentation entry points.

- **Move Scripts**:
  - `verify_all.py` -> `scripts/verify_all.py`
  - `build.sh` -> `scripts/build.sh`
  - `dummy_reqs.txt` -> `tests/dummy_reqs.txt`

- **Move Documentation**:
  - `Improvements.md` -> `docs/Improvements.md`
  - `NEW_ISSUES.md` -> `docs/NEW_ISSUES.md`
  - *Note*: `README.md` and `AGENTS.MD` remain in the root.

### 2. Game Systems Organization
Organize loose modules in `game_systems/` into logical subdirectories.

- **Core Systems**:
  - Create `game_systems/core/`
  - Move `game_systems/world_time.py` -> `game_systems/core/world_time.py`

- **Player Systems**:
  - Move `game_systems/achievement_system.py` -> `game_systems/player/achievement_system.py`

### 3. Cogs Cleanup
Separate cog logic from utility helpers.

- **Utilities**:
  - Create `cogs/utils/`
  - Move `cogs/ui_helpers.py` -> `cogs/utils/ui_helpers.py`
  - *Action*: Update all imports in `cogs/*.py` from `.ui_helpers` to `.utils.ui_helpers`.

## execution Strategy
1.  **Create Directories**: `scripts/`, `docs/`, `game_systems/core/`, `cogs/utils/`.
2.  **Move Files**: Execute the moves listed above.
3.  **Update Imports**:
    - Update `scripts/verify_all.py` to adjust `sys.path` or imports.
    - Update imports in files referencing `world_time.py`, `achievement_system.py`, and `ui_helpers.py`.
4.  **Verify**: Run tests and verify the bot starts correctly.
