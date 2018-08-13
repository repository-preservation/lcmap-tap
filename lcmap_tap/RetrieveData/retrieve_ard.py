"""Read a chip of ARD using lcmap-merlin"""

from lcmap_tap.RetrieveData import GeoCoordinate, item_lookup
from lcmap_tap.RetrieveData.merlin_cfg import make_cfg
from lcmap_tap.logger import log, HOME
import os
import sys
import time
import yaml
import pickle
import glob
import datetime as dt
import merlin
from collections import OrderedDict
from itertools import chain

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


def names(items: list):
    """
    Return a list of characters representing a selection of bands

    Args:
        items: The selected bands for plotting

    Returns:
        list: Name aliases to use

    """
    lookup = OrderedDict([('Blue', ['b']),
                         ('Green', ['g']),
                         ('Red', ['r']),
                         ('NIR', ['n']),
                         ('SWIR-1', ['s1']),
                         ('SWIR-2', ['s2']),
                         ('Thermal', ['t']),
                          ('NDVI', ['r', 'n']),
                          ('MSAVI', ['r', 'n']),
                          ('EVI', ['b', 'r', 'n']),
                          ('SAVI', ['r', 'n']),
                          ('NDMI', ['n', 's1']),
                          ('NBR', ['n', 's2']),
                          ('NBR-2', ['s1', 's2']),
                          ('All Spectral Bands and Indices', ['b', 'g', 'r', 'n', 's1', 's2', 't']),
                          ('All Spectral Bands', ['b', 'g', 'r', 'n', 's1', 's2', 't']),
                          ('All Indices', ['b', 'r', 'n', 's1', 's2'])])

    return list(OrderedDict.fromkeys(list(chain(*[lookup[key] for key in lookup.keys() if key in items]))))


class ARDData:
    """Use lcmap-merlin to retrieve a time-series ARD for a chip"""

    def __init__(self, coord: GeoCoordinate, pixel_coord: GeoCoordinate, config: str, items: list, cache: dict,
                 home: str=HOME,
                 start: str='1982-01-01', stop: str=TODAY):
        """

        Args:
            coord: The X and Y coordinates of the target point in projected meters
            pixel_coord: The upper left coordinate of the pixel in projected meters
            config: Absolute path to a .yaml configuration file
            items: List of bands selected for plotting
            home: Absolute path to a working directory that would contain serialized ARD, default is User's home dir
            start: The start date (YYYY-MM-DD) of the time series
            stop: The stop date (YYYY-MM-DD) of the time series

        """
        self.cache = cache

        self.x = pixel_coord.x
        self.y = pixel_coord.y

        key = (self.x, self.y)

        self.items = [i for item in items for i in item_lookup[item]]

        self.exists, self.required = self.check_cache()

        if len(self.required) > 0:
            url = yaml.load(open(config, 'r'))['merlin']

            t0 = get_time()

            cfg = make_cfg(items=self.required, url=url)

            self.timeseries = merlin.create(x=int(coord.x),
                                            y=int(coord.y),
                                            acquired="{}/{}".format(start, stop),
                                            cfg=cfg)

            t1 = get_time()

            log.info("Time series retrieved in %s seconds" % (t1 - t0))

            self.pixel_ard = self.get_sequence(timeseries=self.timeseries,
                                               pixel_coord=pixel_coord)

            self.pixel_ard.update(self.exists)

        else:
            self.pixel_ard = self.exists

        try:
            self.cache[key].update(self.pixel_ard)

        except (KeyError, ValueError):
            self.cache[key] = self.pixel_ard

        self.cache[key].update({'pulled': dt.datetime.now()})

    @staticmethod
    def get_sequence(timeseries: tuple, pixel_coord: GeoCoordinate) -> dict:
        """
        Find the matching time series rod from the chip of results using pixel upper left coordinate

        Args:
            timeseries: Series of tuples, a tuple (i.e. Tuple[n]) corresponds to the nth pixel in the chip
                        Tuple[n][0] (tuple): Pixel coordinates
                        Tuple[n][1] (dict): Band values (e.g. 'reds': array([, vals]))
                                            Dates (e.g. 'dates': [736688, ...]
            pixel_coord: The upper left coordinate of the pixel in projected meters

        Returns:
            Dict whose keys are band designations and dates for the time series

        """
        gen = filter(lambda x: x[0][2] == pixel_coord.x and x[0][3] == pixel_coord.y, timeseries)

        return next(gen, None)[1]

    def check_cache(self):
        """
        Check the contents of the cache file for pre-existing data to avoid making redundant chipmunk requests

        Returns:
            Tuple[dict, list]
                dict:
                    [item (str)]: A chipmunk label for a particular spectral band (e.g. 'reds')
                                  Maps to the contents of the cached data for a particular band and coordinate
                list: A list of chipmunk labels that will be requested (e.g. 'reds')

        """
        exists = dict()  # Dict of existing data

        required = list()  # List of items to call merlin for

        if (self.x, self.y) in self.cache.keys():
            # Make sure to grab the dates
            exists['dates'] = (self.cache[(self.x, self.y)]['dates'])

            for item in self.items:
                if item in self.cache[(self.x, self.y)].keys():
                    exists[item] = (self.cache[(self.x, self.y)][item])

                else:
                    required.append(item)

            required = list(set(required))

        else:
            # No data retrieved yet from merlin at this coordinate
            required = list(set([item for item in self.items]))

        return exists, required
