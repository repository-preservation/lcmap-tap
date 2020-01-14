import os
from pathlib import Path

# Get the path to the home directory for the current user and create an 'lcmap_tap' subfolder
HOME_BASE_DIR = str(Path.home())

if HOME_BASE_DIR.startswith("C:"):
    # If this is a local Windows file system, use the Documents directory
    HOME = os.path.join(HOME_BASE_DIR, r"Documents", r"TAP_Tool_files")
else:
    HOME = os.path.join(HOME_BASE_DIR, r"TAP_Tool_files")

if not os.path.exists(HOME):
    os.makedirs(HOME)

__version__ = "1.2.1"
