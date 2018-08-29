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

    def __init__(self, widget):
        """
        Create a custom logging handler for outputting the log to a QWidget

        Args:
            widget (PyQt.QWidget): The widget that will display the log output

        """
        super().__init__()

        # active (bool): Only display the log if True, default is False
        self.active = False

        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.setLevel(logging.DEBUG)

        log.addHandler(self)

        self.log_display = widget

    def set_active(self, active: bool=False):
        self.active = active

    def emit(self, record):
        if self.active:
            msg = self.format(record)

            self.log_display.appendPlainText(msg)


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
