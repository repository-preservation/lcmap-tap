"""Create a logger"""

import os
import logging
import sys
import time
from lcmap_tap import HOME


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


class QtHandler(logging.Handler):
    qlog = logging.getLogger()

    def __init__(self, widget):
        super().__init__()

        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.setLevel(logging.DEBUG)

        self.qlog.addHandler(self)

        self.qlog_display = widget

        self.qlog_display.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)

        self.qlog_display.appendPlainText(msg)


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
