import datetime
import importlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAdventureStatusEmbed(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock discord before import
        self.modules_patcher = patch.dict(sys.modules)
        self.modules_patcher.start()

        mock_discord = MagicMock()
        mock_discord.Color.dark_red.return_value = "dark_red"
        mock_discord.Color.dark_green.return_value = "dark_green"
        mock_discord.Color.blue.return_value = "blue"
        mock_discord.Color.gold.return_value = "gold"
        sys.modules["discord"] = mock_discord

        # Mock pymongo to prevent import error
        sys.modules["pymongo"] = MagicMock()
        sys.modules["pymongo.errors"] = MagicMock()

        # Mock other dependencies if needed
        # We need game_systems.world_time which is imported inside the module usually

        # Now we can import the module
        import game_systems.adventure.ui.adventure_embeds
        # RELOAD to ensure we use the fresh mocks from this setUp
        importlib.reload(game_systems.adventure.ui.adventure_embeds)

        self.AdventureEmbeds = game_systems.adventure.ui.adventure_embeds.AdventureEmbeds
        self.WorldTime = game_systems.adventure.ui.adventure_embeds.WorldTime

    def tearDown(self):
        self.modules_patcher.stop()

    def test_status_embed_in_progress(self):
        now = datetime.datetime.now()
        mock_session = {
            "location_id": "forest_clearing",
            "start_time": (now - datetime.timedelta(minutes=10)).isoformat(),
            "end_time": (now + datetime.timedelta(minutes=50)).isoformat(),
            "steps_completed": 15,
            "loot_collected": '{"item_1": 5, "exp": 100, "aurum": 50}',
            "status": "in_progress"
        }

        # Patch WorldTime.now on the imported class/module
        with patch.object(self.WorldTime, "now", return_value=now):
             embed = self.AdventureEmbeds.build_adventure_status_embed(mock_session)

        # Verify basic properties
        # 'embed' is a MagicMock because discord.Embed is mocked

        # Check add_field calls
        calls = embed.add_field.call_args_list
        assert len(calls) >= 3

        # Check call arguments
        # Call 1: Time Remaining
        args, kwargs = calls[0]
        assert "Time Remaining" in kwargs['name']

        # Call 2: Steps
        args, kwargs = calls[1]
        assert "Steps Taken" in kwargs['name']
        assert "15" in kwargs['value']

        # Call 3: Loot
        args, kwargs = calls[2]
        assert "Loot Gathered" in kwargs['name']
        assert "5" in kwargs['value'] # item_1 only

    def test_status_embed_completed(self):
        now = datetime.datetime.now()
        mock_session = {
            "location_id": "forest_clearing",
            "start_time": (now - datetime.timedelta(minutes=60)).isoformat(),
            "end_time": (now - datetime.timedelta(minutes=10)).isoformat(), # Ended 10 mins ago
            "steps_completed": 100,
            "loot_collected": "{}",
            "status": "in_progress"
        }

        with patch.object(self.WorldTime, "now", return_value=now):
             embed = self.AdventureEmbeds.build_adventure_status_embed(mock_session)

        # Verify "Complete!" is in the first field
        calls = embed.add_field.call_args_list
        args, kwargs = calls[0]
        assert "Complete!" in kwargs['value']

if __name__ == "__main__":
    unittest.main()
