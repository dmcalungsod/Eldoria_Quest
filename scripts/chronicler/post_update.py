#!/usr/bin/env python3
import os
import json
import urllib.request
import re
import sys

# Configuration
WEBHOOK_VAR = "EQ_UPDATE_WEBHOOK"
UPDATE_FILE = "monthly_updates/2026-02_february_chronicle.md"

def load_file(filepath):
    """Loads the markdown file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def parse_markdown_to_embed(content):
    """Parses a specifically formatted markdown file into a Discord embed."""
    lines = content.strip().split('\n')

    embed = {
        "color": 0x5a2e2e,  # Dark Red / Fantasy Theme
        "fields": [],
    }

    # Extract Title (First H1)
    if lines and lines[0].startswith("# "):
        embed["title"] = lines[0][2:].strip()
        lines = lines[1:]

    # Extract Subtitle and Description (Everything until first '---')
    description_lines = []

    # Skip leading empty lines
    while lines and not lines[0].strip():
        lines.pop(0)

    while lines:
        line = lines.pop(0).strip()
        if line == "---":
            break
        description_lines.append(line)

    embed["description"] = "\n".join(description_lines).strip()

    # Process Sections (Split by '---')
    remaining_text = "\n".join(lines)
    # Split by separator (allowing for surrounding whitespace)
    chunks = re.split(r'\n\s*---\s*\n', remaining_text)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        chunk_lines = chunk.split('\n')

        # Check if it's a footer (heuristic: starts with "Until next month")
        if chunk.lower().startswith("until next month"):
            embed["footer"] = {"text": chunk.replace("\n", " ")}
            continue

        # Check for header
        field_name = ""
        field_value = ""

        if chunk_lines[0].startswith("## "):
            field_name = chunk_lines[0][3:].strip()
            field_value = "\n".join(chunk_lines[1:]).strip()
        else:
            # Fallback if no ## header
            field_name = "Update"
            field_value = chunk

        if field_name and field_value:
            # Discord field value limit is 1024 chars
            if len(field_value) > 1024:
                field_value = field_value[:1021] + "..."

            embed["fields"].append({
                "name": field_name,
                "value": field_value,
                "inline": False
            })

    return embed

def send_webhook(webhook_url, embed):
    """Sends the embed to the Discord webhook."""
    payload = {
        "username": "Guild Chronicler",
        "avatar_url": "https://i.imgur.com/4M34hi2.png",
        "embeds": [embed]
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=data, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'GuildChronicler/1.0'
    })

    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 204]:
                print("✅ Successfully sent update via webhook.")
            else:
                print(f"⚠️ Webhook responded with status: {response.status}")
                print(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error sending webhook: {e}")

def main():
    webhook_url = os.environ.get(WEBHOOK_VAR)

    if not webhook_url:
        print(f"❌ Error: Environment variable '{WEBHOOK_VAR}' is not set.")
        sys.exit(1)

    content = load_file(UPDATE_FILE)
    if not content:
        sys.exit(1)

    print(f"📖 Parsing update file: {UPDATE_FILE}...")
    embed = parse_markdown_to_embed(content)

    print(f"🚀 Sending update to Discord...")
    send_webhook(webhook_url, embed)

if __name__ == "__main__":
    main()
