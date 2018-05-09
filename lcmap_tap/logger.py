import logging
import sys
import time


def get_time():
    """
    Return the current time stamp

    Returns:
        A formatted string containing the current date and time

    """
    return time.strftime("%Y%m%d-%I%M%S")


log = logging.getLogger()
stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("C:/users/dzelenak/workspace/lcmap_tap_{}.log".format(get_time()))
formatter = logging.Formatter('%(asctime)s %(processName)s: %(message)s')

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

log.addHandler(stream_handler)
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
