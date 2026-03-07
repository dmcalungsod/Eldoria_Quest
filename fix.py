with open("tests/test_codex_unlocks.py", "r") as f:
    content = f.read()

# Add a dummy comment to re-trigger CI again
content += "\n# Trigger CI to bypass Codacy 503 error 2\n"

with open("tests/test_codex_unlocks.py", "w") as f:
    f.write(content)
