"""
scripts/run_agents.py

Executes the agent workflow by injecting the current date into agent prompts.
This script is intended to be run by the GitHub Actions workflow `run_agents.yml`.

Usage: python3 scripts/run_agents.py --agent AGENT_NAME --prompt PROMPT_STRING [--stdout]
OR: python3 scripts/run_agents.py --agent AGENT_NAME --prompt-file PATH/TO/PROMPT [--stdout]
"""

import argparse
import datetime
import os
import sys

# Configuration
PREPARED_DIR = ".Jules/agent_prompts/prepared"


def get_current_date():
    """Retrieves the current date from environment or system clock."""
    env_date = os.environ.get("CURRENT_DATE")
    if env_date:
        return env_date
    return datetime.datetime.now().strftime("%Y-%m-%d")


def inject_date(content, date_str):
    """Replaces {{CURRENT_DATE}} with the provided date string."""
    return content.replace("{{CURRENT_DATE}}", date_str)


def run_agent(agent_name, prompt_content, date_str, stdout=False):
    """
    Simulates running an agent.
    In a real implementation, this would call the LLM API with the prompt.
    """
    final_prompt = inject_date(prompt_content, date_str)

    if stdout:
        print(final_prompt)
        return

    print(f"🚀  Preparing run for agent: {agent_name} on {date_str}...")

    # Write "prepared" prompt to a file for the external agent system to pick up
    output_filename = f"{date_str}_{agent_name}_prepared.md"
    output_path = os.path.join(PREPARED_DIR, output_filename)

    # Ensure directory exists
    os.makedirs(PREPARED_DIR, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_prompt)

    print(f"✅  Agent {agent_name} prepared with date {date_str}. Output saved to {output_path}")
    print(f"📝  Prompt Preview (first 100 chars):\n{final_prompt[:100]}...")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description="Run an Eldoria Quest agent with date injection.")
    parser.add_argument("--agent", required=True, help="Name of the agent (e.g., Foreman)")
    parser.add_argument("--prompt", help="Inline prompt string")
    parser.add_argument("--prompt-file", help="Path to a file containing the prompt")
    parser.add_argument(
        "--stdout", action="store_true", help="Print the processed prompt to stdout instead of saving to file"
    )

    args = parser.parse_args()

    current_date = get_current_date()
    if not args.stdout:
        print(f"📅  Initializing Agent Run for Date: {current_date}")

    prompt_content = ""
    if args.prompt:
        prompt_content = args.prompt
    elif args.prompt_file:
        if os.path.exists(args.prompt_file):
            with open(args.prompt_file, encoding="utf-8") as f:
                prompt_content = f.read()
        else:
            print(f"❌  Prompt file not found: {args.prompt_file}", file=sys.stderr)
            sys.exit(1)
    else:
        print("❌  Either --prompt or --prompt-file must be provided.", file=sys.stderr)
        sys.exit(1)

    run_agent(args.agent, prompt_content, current_date, stdout=args.stdout)

    if not args.stdout:
        print("🎉  Agent processing complete.")


if __name__ == "__main__":
    main()
