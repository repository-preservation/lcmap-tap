
import os
from pathlib import Path

# Get the path to the home directory for the current user and create an 'lcmap_tap' subfolder
HOME = os.path.join(str(Path.home()), 'lcmap_tap')

if not os.path.exists(HOME):
    os.makedirs(HOME)

__version__ = '1.1.0-research'
