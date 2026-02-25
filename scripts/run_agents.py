"""
scripts/run_agents.py

Executes the agent workflow by injecting the current date into agent prompts.
This script is intended to be run by the GitHub Actions workflow `run_agents.yml`.

Usage: python3 scripts/run_agents.py [AGENT_NAME]
If AGENT_NAME is not provided, runs all configured agents.
"""

import os
import sys
import datetime

# Configuration
PROMPTS_DIR = ".Jules/agent_prompts"
LOGS_DIR = ".Jules/agent_logs"

def get_current_date():
    """Retrieves the current date from environment or system clock."""
    env_date = os.environ.get("CURRENT_DATE")
    if env_date:
        return env_date
    return datetime.datetime.now().strftime("%Y-%m-%d")

def load_prompt(agent_name):
    """Loads the prompt for the specified agent."""
    prompt_path = os.path.join(PROMPTS_DIR, f"{agent_name}.md")
    if not os.path.exists(prompt_path):
        # Fallback to system prompt if specific prompt missing?
        # Or maybe just system prompt + role specific instruction?
        # For now, just return None if specific prompt missing.
        print(f"⚠️  No specific prompt found for {agent_name} at {prompt_path}")
        return None

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def inject_date(content, date_str):
    """Replaces {{CURRENT_DATE}} with the provided date string."""
    return content.replace("{{CURRENT_DATE}}", date_str)

def run_agent(agent_name, date_str):
    """
    Simulates running an agent.
    In a real implementation, this would call the LLM API with the prompt.
    """
    print(f"🚀  Preparing run for agent: {agent_name} on {date_str}...")

    prompt_content = load_prompt(agent_name)
    if not prompt_content:
        # Fallback: Load system prompt + agent name
        system_prompt = load_prompt("system_prompt")
        if system_prompt:
             prompt_content = system_prompt + f"\n\n## Role: {agent_name.capitalize()}\n(Generic prompt)"
        else:
            print(f"❌  System prompt missing! Cannot run {agent_name}.")
            return

    final_prompt = inject_date(prompt_content, date_str)

    # Write "prepared" prompt to a file for the external agent system to pick up
    output_filename = f"{date_str}_{agent_name}_prepared.md"
    output_path = os.path.join(LOGS_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_prompt)

    print(f"✅  Agent {agent_name} prepared with date {date_str}. Output saved to {output_path}")
    print(f"📝  Prompt Preview (first 100 chars):\n{final_prompt[:100]}...")
    print("-" * 40)

def main():
    current_date = get_current_date()
    print(f"📅  Initializing Agent Run for Date: {current_date}")

    # Check if a specific agent was requested
    if len(sys.argv) > 1:
        agents_to_run = [sys.argv[1]]
    else:
        # Default list of agents (could be dynamic based on AGENTS.md, but hardcoded for now)
        agents_to_run = ["foreman", "architect"]
        # Add more if prompts exist
        for filename in os.listdir(PROMPTS_DIR):
            if filename.endswith(".md") and filename != "system_prompt.md":
                agent_name = filename[:-3]
                if agent_name not in agents_to_run:
                    agents_to_run.append(agent_name)

    if not os.path.exists(PROMPTS_DIR):
        print(f"❌  Prompts directory not found: {PROMPTS_DIR}")
        sys.exit(1)

    for agent in agents_to_run:
        run_agent(agent, current_date)

    print("🎉  All agents processed.")

if __name__ == "__main__":
    main()
