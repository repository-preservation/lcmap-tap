
import os

# Get the path to the home directory for the current user and create an 'lcmap_tap' subfolder
HOME = os.path.join('K:\90daytemp', r'TAP_Tool_files')

if not os.path.exists(HOME):
    os.makedirs(HOME)

__version__ = '1.2.0'
