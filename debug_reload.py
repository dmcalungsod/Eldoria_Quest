
import sys
import os

# Add path
sys.path.insert(0, os.getcwd())

# Create __init__.py if missing (I did this already)
from game_systems.adventure.ui import exploration_view
print(f"Type of exploration_view: {type(exploration_view)}")
print(f"exploration_view: {exploration_view}")

import importlib
importlib.reload(exploration_view)
print("Reload success")
