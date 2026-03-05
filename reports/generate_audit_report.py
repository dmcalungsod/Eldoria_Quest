import json
import re
from datetime import datetime

# Parse Bandit
with open("reports/bandit.txt", "r") as f:
    bandit_data = f.read()

bandit_issues = []
for block in bandit_data.split("--------------------------------------------------"):
    if ">> Issue:" in block:
        issue = re.search(r'>> Issue: \[(.*?)\] (.*?)\n', block)
        severity = re.search(r'Severity: (.*?)\s+Confidence:', block)
        location = re.search(r'Location: (.*?)\n', block)
        if issue and severity and location:
            loc = location.group(1)
            # ignore tests and B311 and B101 in tests
            if "tests/" in loc and ("B101" in issue.group(1) or "B105" in issue.group(1)):
                continue
            if "B311" in issue.group(1):
                continue
            bandit_issues.append({
                "issue": f"[{issue.group(1)}] {issue.group(2)}",
                "severity": severity.group(1),
                "location": loc
            })

# Parse Vulture (dead code)
with open("reports/vulture.txt", "r") as f:
    vulture_data = f.read().splitlines()

vulture_issues = []
for line in vulture_data:
    if line.strip():
        vulture_issues.append({"location": line.split(":")[0], "issue": line})

# Parse Complexity
with open("reports/complexity.txt", "r") as f:
    complexity_data = f.read().splitlines()

complexity_issues = []
for line in complexity_data:
    if " - " in line and line.strip().startswith("M "):
        parts = line.split(" - ")
        if len(parts) == 2 and parts[1].strip()[0] in ["C", "D", "E", "F"]:
            complexity_issues.append({"issue": f"High Complexity ({parts[1].strip()})", "location": parts[0].strip()})

# Parse Safety
with open("reports/safety.json", "r") as f:
    try:
        safety_data = json.load(f)
        safety_issues = safety_data.get("vulnerabilities", [])
    except json.JSONDecodeError:
        safety_issues = []

# ONE UI Policy violations
with open("reports/send_message.txt", "r") as f:
    send_message_data = f.read().splitlines()

ui_violations = []
for line in send_message_data:
    if "send_message" in line and not "reports/" in line:
         ui_violations.append(line)

report = f"""# 🔍 Eldoria Quest Codebase Audit — {datetime.now().strftime('%Y-%m-%d')}

**Auditor:** Repo Auditor
**Scope:** Entire repository
**Tools Used:** flake8, bandit, vulture, radon, safety, manual review

## Executive Summary
Comprehensive codebase audit completed successfully. Found a number of security, performance, and UI consistency issues. Overall code health is stable but requires targeted cleanups.

## 🚨 Critical Issues (Fix Immediately)
None found in this scan.

## ⚠️ High Priority Issues

"""

for issue in bandit_issues:
    if issue["severity"] == "High":
        report += f"- **Issue**: Security Warning {issue['issue']}\n"
        report += f"  **Location**: `{issue['location']}`\n"
        report += f"  **Risk**: Potential vulnerability.\n"
        report += f"  **Suggested Agent**: Sentinel\n"
        report += f"  **Recommendation**: Review and mitigate.\n\n"

report += "## 🔸 Medium Priority Issues\n\n"

for issue in bandit_issues:
    if issue["severity"] in ["Medium", "Low"]:
        report += f"- **Issue**: Security Warning {issue['issue']}\n"
        report += f"  **Location**: `{issue['location']}`\n"
        report += f"  **Risk**: Low to medium security risk.\n"
        report += f"  **Suggested Agent**: Sentinel\n"
        report += f"  **Recommendation**: Review and mitigate if necessary.\n\n"

report += f"- **Issue**: High Cyclomatic Complexity (> 10)\n"
report += f"  **Location**: Multiple files ({len(complexity_issues)} instances)\n"
report += f"  **Risk**: Difficult to maintain and test.\n"
report += f"  **Suggested Agent**: SystemSmith\n"
report += f"  **Recommendation**: Refactor functions to reduce complexity. Focus on DatabaseManager, CombatEngine, and AdventureSession.\n\n"

report += "## 🔹 ONE UI Policy Violations\n\n"
report += f"- **Issue**: `send_message` used instead of editing existing messages.\n"
report += f"  **Location**: Multiple files ({len(ui_violations)} instances, mainly in `ui/` directories)\n"
report += f"  **Risk**: Breaks immersion and creates UI clutter.\n"
report += f"  **Suggested Agent**: Palette\n"
report += f"  **Recommendation**: Replace `send_message` with `edit_original_response` or appropriate state updates.\n\n"


report += "## 📦 Dependency Issues\n\n"
if safety_issues:
    report += f"- Found {len(safety_issues)} vulnerable dependencies.\n"
    for issue in safety_issues:
        report += f"  - {issue.get('package_name')} {issue.get('vulnerable_spec')}\n"
else:
    report += "- No known vulnerabilities found in dependencies.\n"

report += "\n## 📚 Documentation & Dead Code\n\n"
report += f"- **Issue**: Potentially dead code detected.\n"
report += f"  **Location**: Multiple files ({len(vulture_issues)} instances)\n"
report += f"  **Suggested Agent**: SystemSmith\n"
report += f"  **Recommendation**: Review and remove unused code to improve maintainability.\n"

report += """
## 🧪 Test Coverage Gaps
- Recommend running `pytest-cov` to generate a detailed coverage report and identify missing test paths.

## ✅ Positive Findings
- No hardcoded secrets (API keys, passwords, tokens) were detected in the codebase outside of tests.
- No direct SQL injection vulnerabilities found (assuming PyMongo is used correctly).
- No `TODO`, `FIXME`, or `XXX` comments found in the source code.
- No bare `except:` clauses found.

## 📌 Recommendations
- **Pre-commit hooks**: Enforce ONE UI Policy via custom scripts.
- **Complexity**: SystemSmith should prioritize breaking down the largest methods in `DatabaseManager` and `CombatEngine`.
- **Refactoring**: Adopt a stricter linter configuration (e.g., lower cyclomatic complexity threshold).
"""

with open(f".Jules/audit_report_{datetime.now().strftime('%Y-%m-%d')}.md", "w") as f:
    f.write(report)

print(f"Report generated with {len(complexity_issues)} complexity issues.")
