# Eldoria Quest Agents

This document describes the autonomous agents that maintain and evolve Eldoria Quest. Each agent runs on a schedule, reads/writes logs in `.Jules/agent_logs/`, and contributes to the project's continuous improvement.

## 📁 Key Files for Coordination

- **Agent Logs**: `.Jules/agent_logs/YYYY-MM-DD.md` – daily records of each agent's work.
- **Foreman Plan**: `.Jules/foreman_plan.md` – milestone tracking and task assignments.
- **Visionary Memo**: `.Jules/visionary.md` – strategic priorities and focus areas.
- **Player Feedback**: `.Jules/feedback.md` – collected player reports and suggestions.
- **Roadmap**: `.Jules/roadmap.md` – long‑term goals.

## 🧠 Memory Note

Jules AI now has memory. Before starting work each day, all agents must read the latest daily agent log, the Foreman plan, and the Visionary memo to understand yesterday's completions, today's assignments, blocking tasks, and overall priorities. After completing their task, agents append their entry to the daily log with their focus, changes made, files modified, and any next steps or coordination needs for other agents. Tag other agents in log entries (e.g., `@SystemSmith`) when their work affects them or you need input.

---

## 🤖 Active Agents (Daily)

| Agent | Schedule (GMT+8) | Primary Role |
|-------|------------------|--------------|
| **Foreman** | 12:00 AM | Project management & milestone tracking |
| **GameBalancer** | 12:30 AM | Economy & progression balance |
| **SystemSmith** | 01:00 AM | Architecture & systems refinement |
| **BugHunter** | 01:30 AM | Quality assurance & bug fixes |
| **ChronicleKeeper** | 02:00 AM | Achievements & titles |
| **Grimwarden** | 02:30 AM | Realism & survival tone |
| **Tactician** | 03:00 AM | Combat mechanics & class skills |
| **DataSteward** | 03:30 AM | Data management & validation |
| **StoryWeaver** | 04:00 AM | Narrative & immersion |
| **Worldsmith** | 04:30 AM | Dynamic world systems (day/night, weather) |
| **Lorekeeper** | 05:00 AM | World canon & consistency |
| **Mentor** | 05:30 AM | Player onboarding & tutorials |
| **Namewright** | 06:00 AM | Naming & lore‑friendly titles |
| **GameForge** | 09:00 AM | Content creation (monsters, items, quests) |
| **Bolt** | 09:30 AM | Performance optimization |
| **DepthsWarden** | 10:00 AM | Dungeon floors & factions |
| **ProgressionBalancer** | 11:00 AM | Rank advancement & progression |
| **EventHerald** | 11:30 AM | World & guild events |
| **Palette** | 12:00 PM | UX & accessibility |
| **Sentinel** | 01:00 PM | Security & exploit prevention |
| **SkillWeaver** | 01:30 PM | Class skill formulas & implementation |
| **Carrier** | 03:00 PM | Inventory capacity & stat integration |
| **Architect** | 05:00 PM | Class & expansion design (blueprints) |
| **Equilibrium** | 05:30 PM | Formula & exploit balance |
| **BugHunter (2)** | 06:00 PM | Additional QA capacity |
| **Artisan** | 07:00 PM | Crafting systems |
| **Equipper** | 07:30 PM | Equipment & gear system |
| **Regression Hunter** | 08:00 PM | Regression testing & test suite maintenance |
| **Realmwright** | 08:30 PM | World expansion (new regions) |
| **Questweaver** | 09:00 PM | Storyline & dialogue design |
| **Issue Crafter** | 09:30 PM | Issue creation from logs & feedback |
| **Timeweaver** | 10:00 PM | Auto‑adventure overhaul design & oversight |
| **Codex Keeper** | One Time | Bestiary & lore compendium design & oversight |
| **Party System Designer** | TBA | Multiplayer features design & oversight |
| **Guild Halls Architect** | TBA | Player housing design & oversight |

## 📆 Weekly / Monthly Agents

| Agent | Schedule | Role |
|-------|----------|------|
| **Repo Auditor** | Weekly on Sunday | Comprehensive codebase inspection |
| **Visionary** | Weekly on Sunday | Strategic planning & coordination |
| **Chronicler** | Monthly on 1st | Monthly update summaries & webhook posting |

## 📝 Journal Files

Each agent maintains a personal journal in `.Jules/<agent_name>.md` for critical learnings. These are not daily logs but capture insights, patterns, and lessons that inform future work.

---

## 🔄 Coordination Protocol

- **Foreman** (when active) breaks down major projects into tasks and assigns them to agents via daily logs.
- **Visionary** sets weekly priorities and resolves conflicts.
- All agents must check the latest logs before starting and log their own work afterward.
- Agents tag each other using `@mention` in logs to signal dependencies or request reviews.

This ecosystem ensures that Eldoria Quest evolves coherently, with every change tracked and every agent aligned to the project's goals.

## ⏰ Temporal Integrity

To ensure all agent operations are anchored to the real-world timeline:
- **Date Injection**: The `Run Agents` workflow (`.github/workflows/run_agents.yml`) injects the `CURRENT_DATE` environment variable (in GMT+8) into every agent run.
- **Truth Anchor**: The file `.Jules/TODAY.md` is updated daily by the workflow to reflect the current authorized date. Agents may read this file to confirm the date.
- **Validation**: The `Validate Logs` workflow ensures no files in `.Jules/agent_logs/` are future-dated.
- **CLI Support**: The `scripts/run_agents.py` tool must be used to execute agents. It accepts a `--prompt` argument and replaces the `{{CURRENT_DATE}}` placeholder with the system date before execution.
- **Prepared Prompts**: Prepared prompt files are temporarily stored in `.Jules/agent_prompts/prepared/` (gitignored) rather than cluttering the logs directory.

### Integration Guide

If you are running agents via a custom script or command line, pipe the prompt through `scripts/run_agents.py` to inject the correct date:

```bash
PROMPT=$(python3 scripts/run_agents.py --agent Foreman --prompt "Your prompt..." --stdout)
# Then use $PROMPT with your LLM tool
```
