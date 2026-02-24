"""Parse .Jules/ markdown files and create GitHub Issues via the gh CLI."""

import json
import os
import re
import subprocess
import sys

JULES_DIR = ".Jules"

AGENT_MAP = {
    "foreman_plan.md": ("Foreman", "foreman,task,auto-generated"),
    "foreman.md": ("Foreman", "foreman,task,auto-generated"),
    "architect.md": ("Architect", "architect,design,auto-generated"),
    "bughunter.md": ("BugHunter", "bug,auto-generated"),
    "sentinel.md": ("Sentinel", "security,auto-generated"),
    "repo_auditor.md": ("RepoAuditor", "audit,technical-debt,auto-generated"),
    "gamebalancer.md": ("GameBalancer", "balance,auto-generated"),
    "depthswarden.md": ("DepthsWarden", "content,auto-generated"),
    "visionary.md": ("Visionary", "strategy,auto-generated"),
    "questweaver.md": None,  # skip
}

MIN_TASK_LENGTH = 15
MAX_TITLE_LENGTH = 80

LABEL_COLORS = {
    "foreman": "0075ca",
    "task": "e4e669",
    "auto-generated": "ededed",
    "architect": "1d76db",
    "design": "c2e0c6",
    "bug": "d73a4a",
    "security": "e11d48",
    "audit": "f9d0c4",
    "technical-debt": "fef2c0",
    "balance": "bfd4f2",
    "content": "d4c5f9",
    "strategy": "0e8a16",
    "jules-agent": "cccccc",
}


def get_agent_info(filepath: str):
    """Return (agent_name, labels_csv) for a .Jules file, or None to skip."""
    fname = os.path.basename(filepath)
    parts = filepath.replace("\\", "/").split("/")

    # agent_logs/ directory → Foreman
    if "agent_logs" in parts:
        return ("Foreman", "foreman,task,auto-generated")

    # architect_designs/ directory → Architect
    if "architect_designs" in parts:
        return ("Architect", "architect,design,auto-generated")

    if fname in AGENT_MAP:
        return AGENT_MAP[fname]  # may be None (skip)

    # Generic fallback
    agent_name = os.path.splitext(fname)[0].replace("_", " ").title().replace(" ", "")
    return (agent_name, "jules-agent,auto-generated")


def parse_tasks(content: str, filepath: str):
    """Return list of (task_text, section) tuples parsed from markdown content."""
    tasks = []
    lines = content.splitlines()
    section = "general"

    SECTION_HEADERS = {
        r"^##\s+🚧\s+New Assignments": "new_assignments",
        r"^\*\*Next Steps:\*\*": "next_steps",
        r"^###\s+Suggestions": "suggestions",
        r"^##\s+🎯\s+Recommended Focus": "recommended_focus",
        r"^##\s+🚧\s+Blockers": "blockers",
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect section changes
        for pattern, sec_name in SECTION_HEADERS.items():
            if re.match(pattern, line.strip()):
                section = sec_name
                i += 1
                break
        else:
            # Parse task lines based on current section
            task = None

            # 1. Unchecked checkboxes (any section)
            m = re.match(r"^-\s+\[ \]\s+(.+)$", line)
            if m:
                task = (m.group(1).strip(), "unchecked_task")

            # 2. New Assignments bullets
            elif section == "new_assignments":
                m = re.match(r"^[-*]\s+\*\*@\w+:\*\*\s+(.+)$", line)
                if m:
                    task = (m.group(1).strip(), "new_assignment")

            # 3. Next Steps bullets
            elif section == "next_steps":
                m = re.match(r"^[-*]\s+(.+)$", line)
                if m:
                    task = (m.group(1).strip(), "next_step")

            # 4. Suggestions bullets
            elif section == "suggestions":
                m = re.match(r"^[-*]\s+(.+)$", line)
                if m:
                    task = (m.group(1).strip(), "suggestion")

            # 5. Recommended Focus numbered list
            elif section == "recommended_focus":
                m = re.match(r"^\d+\.\s+\*\*\w+\*\*:\s+(.+)$", line)
                if m:
                    task = (m.group(1).strip(), "recommended_focus")

            # 6. Blockers
            elif section == "blockers":
                m = re.match(r"^[-*]\s+(.+)$", line)
                if m:
                    task = (m.group(1).strip(), "blocker")

            if task:
                tasks.append(task)
            i += 1

    return tasks


def filter_tasks(tasks):
    """Remove noise tasks."""
    filtered = []
    for text, section in tasks:
        if len(text) < MIN_TASK_LENGTH:
            continue
        if any(kw in text for kw in ("Completed", "Complete", "✅")):
            continue
        if re.match(r"^\[x\]", text, re.IGNORECASE):
            continue
        filtered.append((text, section))
    return filtered


def fetch_existing_issue_titles(repo: str) -> set:
    """Fetch all open issue titles from the repo into a set."""
    titles: set = set()
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", "open", "--limit", "1000", "--json", "title"],
            capture_output=True,
            text=True,
            check=True,
        )
        issues = json.loads(result.stdout or "[]")
        titles = {i.get("title", "") for i in issues}
    except subprocess.CalledProcessError as exc:
        print(f"⚠️  Could not fetch existing issues: {exc.stderr.strip()}", file=sys.stderr)
    return titles


def ensure_labels(labels_csv: str, repo: str):
    """Create labels if they don't exist."""
    for label in labels_csv.split(","):
        label = label.strip()
        color = LABEL_COLORS.get(label, "cccccc")
        proc = subprocess.run(
            ["gh", "label", "create", label, "--color", color, "--force", "--repo", repo],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"  ⚠️  Label create failed for '{label}': {proc.stderr.strip()}", file=sys.stderr)


def create_issue(title: str, body: str, labels_csv: str, repo: str) -> bool:
    """Create a GitHub Issue. Return True on success."""
    label_args = []
    for label in labels_csv.split(","):
        label_args += ["--label", label.strip()]
    try:
        subprocess.run(
            ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body, "--assignee", "google-labs-jules"] + label_args,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  ⚠️  Failed to create issue '{title}': {exc.stderr.strip()}", file=sys.stderr)
        return False


def get_changed_files(event_name: str):
    """Return list of changed .Jules .md file paths."""
    if event_name == "workflow_dispatch":
        result = []
        for root, _dirs, files in os.walk(JULES_DIR):
            for fname in files:
                if fname.endswith(".md"):
                    result.append(os.path.join(root, fname))
        return result

    # push event: use git diff
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in proc.stdout.splitlines() if f.startswith(JULES_DIR + "/") and f.endswith(".md")]
    except subprocess.CalledProcessError:
        return []


def main():
    repo = os.environ.get("REPO", "")
    event_name = os.environ.get("EVENT_NAME", "push")
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")

    if not repo:
        print("REPO environment variable not set.", file=sys.stderr)
        sys.exit(1)

    changed_files = get_changed_files(event_name)
    print(f"📂 Files to process: {changed_files}")

    existing_titles = fetch_existing_issue_titles(repo)

    total_created = 0
    total_skipped = 0
    summary_lines = ["### 📋 MD-to-Issues Summary", ""]

    for filepath in changed_files:
        agent_info = get_agent_info(filepath)
        if agent_info is None:
            print(f"  ⏭️  Skipping {filepath} (questweaver — no issues)")
            summary_lines.append(f"- ⏭️ Skipped `{filepath}` (questweaver)")
            continue

        agent_name, labels_csv = agent_info

        if not os.path.isfile(filepath):
            continue

        with open(filepath, encoding="utf-8") as fh:
            content = fh.read()

        raw_tasks = parse_tasks(content, filepath)
        tasks = filter_tasks(raw_tasks)

        if not tasks:
            summary_lines.append(f"- ℹ️ `{filepath}` — no actionable tasks found")
            continue

        ensure_labels(labels_csv, repo)

        file_url = f"https://github.com/{repo}/blob/main/{filepath.replace(os.sep, '/')}"

        for task_text, section in tasks:
            truncated = task_text[:MAX_TITLE_LENGTH]
            title = f"[{agent_name}] {truncated}"

            if title in existing_titles:
                print(f"  ⏩ Already exists: {title}")
                total_skipped += 1
                summary_lines.append(f"  - ⏩ Already exists: `{title}`")
                continue

            body = (
                f"**Task:** {task_text}\n\n"
                f"**Source file:** [{filepath}]({file_url})\n\n"
                f"**Section:** `{section}`\n\n"
                f"**Agent:** {agent_name}\n\n"
                "_This issue was auto-generated by the MD-to-Issues workflow. "
                "Consider assigning it to Copilot for implementation._"
            )

            success = create_issue(title, body, labels_csv, repo)
            if success:
                print(f"  ✅ Created: {title}")
                existing_titles.add(title)
                total_created += 1
                summary_lines.append(f"  - ✅ Created: `{title}`")
            else:
                total_skipped += 1

    summary_lines += [
        "",
        f"**Total issues created:** {total_created}",
        f"**Total skipped/failed:** {total_skipped}",
    ]

    if step_summary_path:
        with open(step_summary_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(summary_lines) + "\n")

    print(f"\n✅ Done. Created: {total_created}, Skipped: {total_skipped}")


if __name__ == "__main__":
    main()
