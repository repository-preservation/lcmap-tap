"""Read a chip of ARD using lcmap-merlin"""

from lcmap_tap.RetrieveData.retrieve_data import GeoInfo
from lcmap_tap.RetrieveData.retrieve_data import GeoCoordinate
from lcmap_tap.logger import log
import time
import yaml
import merlin

try:
    MERLIN = yaml.load(open('URL.yaml', 'r'))['merlin']

    log.info("lcmap-merlin url=%s" % MERLIN)

    print(MERLIN)

except FileNotFoundError:
    MERLIN = None


def get_time():
    """
    Return the current time

    Returns:

    """
    return time.time()


class ARDData:
    """Use lcmap-merlin to retrieve a time-series ARD for a chip"""

    def __init__(self, x: str, y: str, start: str='1982-01-01', stop: str='2017-12-31'):
        """

        Args:
            x: X-coordinate in projected meters
            y: Y-coordinate in projected meters
            start: The start date (YYYY-MM-DD) of the time series
            stop: The stop date (YYYY-MM-DD) of the time series

        """
        self.geo_info = GeoInfo(x, y)

        t0 = get_time()
        self.timeseries = merlin.create(x=self.geo_info.geo_coord.x,
                                        y=self.geo_info.geo_coord.y,
                                        acquired="{}/{}".format(start, stop),
                                        cfg=merlin.cfg.get(profile="chipmunk-ard",
                                                           env={"CHIPMUNK_URL": MERLIN}))
        t1 = get_time()

        log.info("Time series retrieved in %s seconds" % (t1 - t0))

        self.pixel_ard = self.get_sequence(timeseries=self.timeseries,
                                           pixel_coord=self.geo_info.pixel_coord)

    @staticmethod
    def get_sequence(timeseries: tuple, pixel_coord: GeoCoordinate) -> dict:
        """
        Find the matching time series rod from the chip of results using pixel upper left coordinate

        Args:
            timeseries: series of tuples, index 0 holds tuple of coordinates, index 1 holds dict of ARD data and dates
            pixel_coord: has attributes x and y

        Returns:
            Dict, keys are individual bands and dates for the time series

        """
        gen = filter(lambda x: x[0][2] == pixel_coord.x and x[0][3] == pixel_coord.y, timeseries)

        return next(gen, None)[1]
