with open("tests/test_event_cog.py", "r") as f:
    content = f.read()

# Let's see if there is a problem with the announcement mock.
# "The user explicitly planned to mock discord.utils.get to test _announce in test_event_cog.py."
# I'll do that to make sure it aligns with the plan!
