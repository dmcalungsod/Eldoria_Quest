# 🔍 Command Cleaner Audit Report

**Audit Date:** 2024-10-24
**Agent:** Command Cleaner

## 📋 Slash Command Registry

The following commands are currently implemented in the codebase and registered via `discord.py`'s `app_commands`.

### 🟢 Active Commands

| Command | Description | Permissions | ONE UI Compliance |
| :--- | :--- | :--- | :--- |
| `/start` | Begin your adventure (or view profile). | Public | ✅ Compliant (Entry Point) |
| `/chronicles` | View and manage earned titles. | Public | ✅ Compliant (Refactored) |
| `/tournament_status` | View active Guild Tournament status. | Public | ✅ Compliant (Info) |
| `/tournament_leaderboard` | View tournament leaderboard. | Public | ✅ Compliant (Info) |
| `/event_status` | View active World Event status. | Public | ✅ Compliant (Info) |
| `/faction list` | List available factions. | Public | ✅ Compliant (Ephemeral) |
| `/faction join` | Join a faction. | Public | ✅ Compliant (Ephemeral) |
| `/faction status` | Check faction status. | Public | ✅ Compliant (Ephemeral) |
| `/faction leave` | Leave current faction. | Public | ✅ Compliant (Ephemeral) |
| `/ping` | Check bot latency. | Public | ✅ Compliant (Utility/Ephemeral) |

### 🛡️ Admin Commands

| Command | Description | Permissions | ONE UI Compliance |
| :--- | :--- | :--- | :--- |
| `/devpanel` | Developer Controls. | Owner Only | ✅ Compliant (Ephemeral/Edit) |
| `/tournament_admin_start` | Manually start a tournament. | Administrator | ✅ Compliant (Ephemeral) |
| `/tournament_admin_end` | Manually end a tournament. | Administrator | ✅ Compliant (Ephemeral) |
| `/admin_event_start` | Manually start a world event. | Administrator | ✅ Compliant (Ephemeral) |
| `/admin_event_end` | Manually end a world event. | Administrator | ✅ Compliant (Ephemeral) |

## 🗑️ Removed / Orphaned Commands

The following commands were identified as removed or orphaned during the audit:

-   **`/adventure`**: Explicitly removed from `cogs/adventure_cog.py` to enforce ONE UI Policy. Players must now start expeditions via the Character Profile (`/start`).

## ⚠️ Notes

-   **Legacy Prefix Commands**: No legacy prefix commands (e.g., `!command`) were found in the codebase.
-   **ONE UI Policy**: All interactive commands (e.g., button flows) now strictly adhere to editing the original message. `/chronicles` was refactored to comply.
