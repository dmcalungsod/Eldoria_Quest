# Sentinel's Journal

## 2025-02-18 — Application Command Authorization Bypass Risk

**Vulnerability:** The `@commands.is_owner()` decorator from `discord.ext.commands` was applied to an `@app_commands.command`. While some libraries support this, mixing `ext.commands` checks with `app_commands` can lead to scenarios where the check is not properly registered or enforced by the interaction system, potentially allowing unauthorized users to execute admin commands.

**Learning:** `app_commands` rely on the interaction tree for checks. Traditional `ext.commands` decorators might not integrate seamlessly with the slash command system's error handling pipeline, or might be ignored if the command is not a hybrid command.

**Prevention:** Always use explicit checks within the command body (e.g., `if not await bot.is_owner(user): return`) or use dedicated `app_commands.checks` decorators. Defense in depth (manual check + decorator) is preferred for critical administrative functions.
