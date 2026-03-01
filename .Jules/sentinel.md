# Sentinel's Journal

## 2026-03-01 — Hardcoded Vulnerable pip Version (CVE-2026-1703)

**Vulnerability:** The build scripts (`scripts/build.sh`) and CI configurations (`.circleci/config.yml`) had a hardcoded installation of a known vulnerable `pip` version (`pip==24.0` in CI/Build, although `25.3` was detected by tests and caused them to fail). The vulnerability (CVE-2026-1703) could allow arbitrary code execution during package installation.

**Learning:** Hardcoding dependency versions in build scripts and CI pipelines without regular security reviews can lock the project into a vulnerable state, even if the application's own `requirements.txt` is secure. The test suite correctly identified the vulnerability, but the CI/CD pipeline was repeatedly reinstalling a vulnerable version.

**Prevention:** Ensure that package managers and foundational tools are updated regularly as part of the security maintenance routine. When pinning versions for reproducible builds, prioritize security patches and monitor CVE databases for the pinned versions. Test environments should also reflect the production environment as closely as possible to prevent "it works on my machine" security false negatives.

## 2025-02-18 — Application Command Authorization Bypass Risk

**Vulnerability:** The `@commands.is_owner()` decorator from `discord.ext.commands` was applied to an `@app_commands.command`. While some libraries support this, mixing `ext.commands` checks with `app_commands` can lead to scenarios where the check is not properly registered or enforced by the interaction system, potentially allowing unauthorized users to execute admin commands.

**Learning:** `app_commands` rely on the interaction tree for checks. Traditional `ext.commands` decorators might not integrate seamlessly with the slash command system's error handling pipeline, or might be ignored if the command is not a hybrid command.

**Prevention:** Always use explicit checks within the command body (e.g., `if not await bot.is_owner(user): return`) or use dedicated `app_commands.checks` decorators. Defense in depth (manual check + decorator) is preferred for critical administrative functions.
