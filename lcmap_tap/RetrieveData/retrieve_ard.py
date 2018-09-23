"""Read a chip of ARD using lcmap-merlin"""

from lcmap_tap.RetrieveData import GeoCoordinate, item_lookup
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData.merlin_cfg import make_cfg
from lcmap_tap.logger import log, exc_handler
import os
import sys
import time
# import yaml
import glob
import merlin
from collections import OrderedDict
# from itertools import chain
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QThread, QCoreApplication

# TODAY = dt.datetime.now().strftime("%Y-%m-%d")

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


class Worker(QObject):
    result = pyqtSignal(object)

    # finished = pyqtSignal(int)

    def __init__(self, geo, start, stop, cfg):
        super().__init__()

        log.debug("Worker started")

        self.geo = geo
        self.start = start
        self.stop = stop
        self.cfg = cfg

    @pyqtSlot()
    def call_merlin(self):
        # thread_name = QThread.currentThread().objectName()
        #
        thread_id = int(QThread.currentThreadId())

        log.debug("THREAD ID: %s" % thread_id)

        log.debug("Grabbing merlin timeseries")

        data = merlin.create(x=int(self.geo.coord.x),
                             y=int(self.geo.coord.y),
                             acquired="{}/{}".format(self.start, self.stop),
                             cfg=self.cfg)

        self.result.emit(data)


class ARDData(QObject):
    """Use lcmap-merlin to retrieve a time-series ARD for a chip"""

    def __init__(self, geo, url, items, cache, controls, start='1982-01-01', stop='2017-12-31'):
        """

        Args:
            geo (GeoInfo): Instance of the GeoInfo class
            url (str): Chipmunk URL
            items (list): List of bands selected for plotting
            cache (dict): Contents of the cache file
            controls (MainControls)
            start (str): The start date (YYYY-MM-DD) of the time series
            stop (str): The stop date (YYYY-MM-DD) of the time series

        """
        super().__init__()

        self.controls = controls

        self.cache = cache

        self.geo = geo

        self.chip_x = geo.chip_coord.x
        self.chip_y = geo.chip_coord.y

        self.key = f'{self.chip_x}_{self.chip_y}'

        self.items = [i for item in items for i in item_lookup[item]]

        self.cached, self.required = self.check_cache(key=self.key, cache=self.cache, items=self.items)

        if len(self.required) > 0:
            # url = yaml.load(open(config, 'r'))['merlin']

            cfg = make_cfg(items=self.required, url=url)

            self.controls.qt_handler.set_active(True)

            self.worker = Worker(geo, start, stop, cfg)

            self.thread = QThread()

            self.worker.moveToThread(self.thread)

            self.worker.result.connect(self.get_timeseries)

            self.thread.started.connect(self.worker.call_merlin)

            self.thread.start()

            while self.thread.isRunning():
                QCoreApplication.processEvents()

            self.controls.qt_handler.set_active(False)

        if len(self.cached) > 0:
            cached_pixel_ard = self.get_sequence(timeseries=tuple(self.cache[self.key].items()),
                                                 pixel_coord=self.geo.pixel_coord)

            try:
                self.pixel_ard.update(cached_pixel_ard)

            except AttributeError:
                self.pixel_ard = cached_pixel_ard

            del cached_pixel_ard

    @pyqtSlot(object)
    def get_timeseries(self, ts):
        """

        """
        self.timeseries = ts

        pixel_ard = self.get_sequence(timeseries=self.timeseries,
                                      pixel_coord=self.geo.pixel_coord)

        self.cache = self.update_cache(key=self.key, cache=self.cache, required=self.required,
                                       timeseries=self.timeseries)

        try:
            self.pixel_ard.update(pixel_ard)

        except AttributeError:
            self.pixel_ard = pixel_ard

        # Return to the main plotting routine
        self.controls.plot()

        return None

    @staticmethod
    def get_sequence(timeseries: tuple, pixel_coord: GeoCoordinate) -> dict:
        """
        Find the matching time series rod from the chip of results using pixel upper left coordinate

        Args:
            timeseries: Series of tuples, a tuple (i.e. Tuple[n]) corresponds to the nth pixel in the chip
                        Tuple[n][0] (tuple): Chip and Pixel coordinates
                                             [0, 1]: Chip UL coordinates
                                             [2, 3]: Pixel UL coordinates
                        Tuple[n][1] (dict): Band values (e.g. 'reds': array([, vals]))
                                            Dates (e.g. 'dates': [736688, ...]
            pixel_coord: The upper left coordinate of the pixel in projected meters

        Returns:
            Spectral data organized by ubid along with Pixel QA and dates

        """
        #  x is an item in timeseries; x[0] is the tuple of coordinates for that timeseries item.
        gen = filter(lambda x: x[0][2] == pixel_coord.x and x[0][3] == pixel_coord.y, timeseries)

        return next(gen, None)[1]

    @staticmethod
    def check_cache(key, cache, items):
        """
        Check the contents of the cache file for pre-existing data to avoid making redundant chipmunk requests

        Args:
            key (Tuple[int, int]): The chip upper-left coordinates
            cache (dict): Pre-loaded ARD, could be empty dict if cache file didn't exist
            items (list): ubids for the requested bands and indices

        Returns:
            Tuple[list, list]
                [0]: List of ubids that will be requested using merlin
                [1]: List of ubids that exist in the cache

        """
        if key in cache.keys():
            # list of ubids that we need to request with merlin
            required = [i for i in items if i not in cache[key]['bands']]

            # list of ubids that were previously requested from merlin and exist in the cache
            cached = [i for i in cache[key]['bands'] if i in items or i is 'qas']

        else:
            required = items

            cached = list()

        # remove duplicates (e.g. 'qas')
        required = list(set(required))

        log.info("Required: %s" % required)
        log.info("Cached: %s " % cached)

        return cached, required

    @staticmethod
    def update_cache(key, cache, required, timeseries):
        """
        Update the cache data to include the additional chipmunk requests

        Args:
            key (str): The chip coordinates
            cache (dict): The cached ARD chip data
            required (list): The ubids requested from chipmunk
            timeseries (tuple): Contains series of tuples - the timeseries of ARD for a chip

        Returns:
            dict: The same format as the input cache dictionary

        """
        ts = OrderedDict({t[0]: t[1] for t in timeseries})

        if key not in cache.keys():
            cache[key] = ts

        else:
            for k in ts.keys():
                try:
                    cache[key][k].update(ts[k])

                except KeyError:
                    cache[key][k] = ts[k]

        if 'bands' not in cache[key].keys():
            cache[key]['bands'] = required

        else:
            # Update the 'bands' list to include the newly requested chipmunk ubids
            cache[key]['bands'] = list(set(cache[key]['bands'] + required))

        return cache
