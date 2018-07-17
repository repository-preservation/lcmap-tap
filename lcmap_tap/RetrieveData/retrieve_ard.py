"""Read a chip of ARD using lcmap-merlin"""

from lcmap_tap.RetrieveData.retrieve_data import GeoCoordinate
from lcmap_tap.logger import log, HOME
import os
import sys
import time
import yaml
import pickle
import glob
import datetime as dt
import merlin

TODAY = dt.datetime.now().strftime("%Y-%m-%d")

# TODO: only retrieve the bands specified by user for plotting


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions
    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:

    """
    log.critical("Exception: ", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = exc_handler


def get_time():
    """
    Return the current time

    Returns:

    """
    return time.time()


def get_image_ids(path: str) -> list:
    """
    Return a list of image IDs based on the contents of the ARD tarballs folder

    Args:
        path:

    Returns:

    """
    file_list = glob.glob(path + os.sep + "*SR*")

    return sorted([os.path.splitext(os.path.basename(f))[0] for f in file_list])


class ARDData:
    """Use lcmap-merlin to retrieve a time-series ARD for a chip"""

    def __init__(self, coord: GeoCoordinate, pixel_coord: GeoCoordinate, config: str,
                 home: str=HOME,
                 start: str='1982-01-01', stop: str=TODAY):
        """

        Args:
            coord: The X and Y coordinates of the target point in projected meters
            pixel_coord: The upper left coordinate of the pixel in projected meters
            config: Absolute path to a .yaml configuration file
            home: Absolute path to a working directory that would contain serialized ARD, default is User's home dir
            start: The start date (YYYY-MM-DD) of the time series
            stop: The stop date (YYYY-MM-DD) of the time series

        """
        MERLIN = yaml.load(open(config, 'r'))['merlin']

        p_file = os.path.join(home, "ard_{x}_{y}.p".format(x=pixel_coord.x,
                                                           y=pixel_coord.y))

        if not os.path.exists(p_file):

            t0 = get_time()

            cfg = merlin.cfg.get(profile="chipmunk-ard",
                                 env={"CHIPMUNK_URL": MERLIN})

            self.timeseries = merlin.create(x=int(coord.x),
                                            y=int(coord.y),
                                            acquired="{}/{}".format(start, stop),
                                            cfg=cfg)
            t1 = get_time()

            log.info("Time series retrieved in %s seconds" % (t1 - t0))

            self.pixel_ard = self.get_sequence(timeseries=self.timeseries,
                                               pixel_coord=pixel_coord)

            with open(p_file, "wb") as f:
                pickle.dump(self.pixel_ard, f)

                log.info("Dumped ARD data to pickle file %s" % p_file)

        else:
            with open(p_file, "rb") as f:
                self.pixel_ard = pickle.load(f)

            log.info("Read ARD data from pre-existing pickle file %s" % p_file)

    @staticmethod
    def get_sequence(timeseries: tuple, pixel_coord: GeoCoordinate) -> dict:
        """
        Find the matching time series rod from the chip of results using pixel upper left coordinate

        Args:
            timeseries: Series of tuples, [0] = tuple of coordinates, [1] = dict of ARD data and dates
            pixel_coord: The upper left coordinate of the pixel in projected meters

        Returns:
            Dict whose keys are band designations and dates for the time series

        """
        gen = filter(lambda x: x[0][2] == pixel_coord.x and x[0][3] == pixel_coord.y, timeseries)

        return next(gen, None)[1]
