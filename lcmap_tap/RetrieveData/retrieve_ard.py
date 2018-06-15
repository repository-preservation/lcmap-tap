"""Read a chip of ARD using lcmap-merlin"""

from lcmap_tap.RetrieveData.retrieve_data import GeoCoordinate
from lcmap_tap.logger import log
import sys
import time
import yaml
import merlin

try:
    MERLIN = yaml.load(open('URL.yaml', 'r'))['merlin']

    log.info("lcmap-merlin url=%s" % MERLIN)

except FileNotFoundError:
    MERLIN = None


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


class ARDData:
    """Use lcmap-merlin to retrieve a time-series ARD for a chip"""

    def __init__(self, coord: GeoCoordinate, pixel_coord: GeoCoordinate,
                 start: str='1982-01-01', stop: str='2017-12-31'):
        """

        Args:
            coord: The X and Y coordinates of the target point in projected meters
            pixel_coord: The upper left coordinate of the pixel in projected meters
            start: The start date (YYYY-MM-DD) of the time series
            stop: The stop date (YYYY-MM-DD) of the time series

        """
        t0 = get_time()

        self.timeseries = merlin.create(x=coord.x,
                                        y=coord.y,
                                        acquired="{}/{}".format(start, stop),
                                        cfg=merlin.cfg.get(profile="chipmunk-ard",
                                                           env={"CHIPMUNK_URL": MERLIN}))
        t1 = get_time()

        log.info("Time series retrieved in %s seconds" % (t1 - t0))

        self.pixel_ard = self.get_sequence(timeseries=self.timeseries,
                                           pixel_coord=pixel_coord)

    @staticmethod
    def get_sequence(timeseries: tuple, pixel_coord: GeoCoordinate) -> dict:
        """
        Find the matching time series rod from the chip of results using pixel upper left coordinate

        Args:
            timeseries: Series of tuples, [0] = tuple of coordinates, [1] = dict of ARD data and dates
            pixel_coord: The upper left coordinate of the pixel in projected meters

        Returns:
            Dict, keys are band designations and dates for the time series

        """
        gen = filter(lambda x: x[0][2] == pixel_coord.x and x[0][3] == pixel_coord.y, timeseries)

        return next(gen, None)[1]
