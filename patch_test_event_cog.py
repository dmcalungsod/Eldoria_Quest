import re

with open("tests/test_event_cog.py") as f:
    content = f.read()

new_content = re.sub(r'            # Test private method _announce\n            await self\.cog\._announce\("Hello World"\)', '            from cogs.utils.announcer import announce_to_guilds\n            await announce_to_guilds(self.bot, "Hello World")', content)

with open("tests/test_event_cog.py", "w") as f:
    f.write(new_content)
