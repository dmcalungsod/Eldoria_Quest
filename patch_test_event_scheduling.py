import re

with open("tests/test_event_scheduling_logic.py") as f:
    content = f.read()

# Replace the patch approach
new_test = """
    @patch("game_systems.core.world_time.WorldTime")
    @patch("random.random")
    def test_mystic_merchant_starts_on_roll(self, mock_random, mock_world_time):
        # 1. Setup
        self.cog.system.get_current_event.return_value = None
        mock_world_time.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_random.return_value = 0.01
        self.cog.system.start_event.return_value = True

        import cogs.event_cog
        # Mock announce_to_guilds directly on the module we imported
        with patch.object(cogs.event_cog, 'announce_to_guilds', new_callable=AsyncMock) as mock_announce:
            # 2. Run
            asyncio.run(self.cog.check_event_cycle())

            # 3. Verify
            self.cog.system.start_event.assert_called_with("mystic_merchant", 24)
            mock_announce.assert_called()
            args, _ = mock_announce.call_args
            self.assertIn("Mystic", args[1])
"""

content = re.sub(r'    @patch\("cogs\.utils\.announcer\.announce_to_guilds", new_callable=AsyncMock\)\s+@patch\("game_systems\.core\.world_time\.WorldTime"\)\s+@patch\("random\.random"\)\s+def test_mystic_merchant_starts_on_roll[\s\S]*?self\.assertIn\("Mystic", args\[1\]\)', new_test.strip(), content)

with open("tests/test_event_scheduling_logic.py", "w") as f:
    f.write(content)
