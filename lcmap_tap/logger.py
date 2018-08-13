"""Create a logger"""

import os
import logging
import sys
import time
from pathlib import Path


# Get the path to the home directory for the current user and create an 'lcmap_tap' subfolder
HOME = os.path.join(str(Path.home()), 'lcmap_tap')

__version__ = '0.3.2'

if not os.path.exists(HOME):
    os.makedirs(HOME)


def get_time():
    """
    Return the current time stamp

    Returns:
        A formatted string containing the current date and time

    """
    return time.strftime("%Y%m%d-%I%M%S")


log = logging.getLogger()

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(os.path.join(HOME, "lcmap_tap_{}.log".format(get_time())))
stderr_handler = logging.StreamHandler(sys.stderr)

formatter = logging.Formatter('%(asctime)s %(levelname)s %(processName)s: %(message)s')

stdout_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

log.addHandler(stdout_handler)
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions
    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:

    """
    log.critical("Uncaught Exception: ", exc_info=(exc_type, exc_value, exc_traceback))
