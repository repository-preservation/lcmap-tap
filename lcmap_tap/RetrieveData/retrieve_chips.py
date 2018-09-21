"""Grab some chips to make a pretty picture"""

from lcmap_tap.logger import exc_handler
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData import GeoAffine, GeoCoordinate
from lcmap_tap.RetrieveData.merlin_cfg import make_cfg
import lcmap_tap.Analysis.data_tools as tools
from lcmap_tap.Visualization.rescale import Rescale

import sys
import numpy as np
import datetime as dt
from multiprocessing.dummy import Pool as ThreadPool
import merlin

sys.excepthook = exc_handler


class Chips:
    def __init__(self, x, y, date, url,
                 n=9, r_channel='reds', g_channel='greens', b_channel='blues',
                 lower=1, upper=99):
        """

        Args:
            x (coordinate_like): The point of reference x-coordinate
            y (coordinate_like): The point of reference y-coordinate
            date (dt.datetime): The target date
                        url (str): The Chipmunk URL

            n (int): Number of chips in mosaic, default is 9
            r_channel (str): UBID to use for the red color channel (default is 'reds')
            g_channel (str): UBID to use for the green color channel (default is 'greens')
            b_channel (str): UBID to use for the blue color channel (default is 'blues')
            lower (int): Lower percentage clipping threshold
            upper (int): Upper percentage clipping threshold

        """
        self.pool = ThreadPool(n)

        self.items = (r_channel, g_channel, b_channel, 'qas')

        self.date = date

        self.start, self.stop = self.get_acquired_dates(self.date)

        self.cfg = make_cfg(self.items, url)

        # 3000 = 30m pixel x 100m chip-length
        self.grid = {
            'n': {'geo': GeoInfo(str(x), str(y + 3000)), 'ind': 0, 'data': []},

            'c': {'geo': GeoInfo(str(x), str(y)), 'ind': 0, 'data': []},

            's': {'geo': GeoInfo(str(x), str(y - 3000)), 'ind': 0, 'data': []},

            'nw': {'geo': GeoInfo(str(x - 3000), str(y + 3000)), 'ind': 0, 'data': []},

            'w': {'geo': GeoInfo(str(x - 3000), str(y)), 'ind': 0, 'data': []},

            'sw': {'geo': GeoInfo(str(x - 3000), str(y - 3000)), 'ind': 0, 'data': []},

            'ne': {'geo': GeoInfo(str(x + 3000), str(y + 3000)), 'ind': 0, 'data': []},

            'e': {'geo': GeoInfo(str(x + 3000), str(y)), 'ind': 0, 'data': []},

            'se': {'geo': GeoInfo(str(x + 3000), str(y - 3000)), 'ind': 0, 'data': []}
        }

        self.params = self.get_params()

        self.retrieve_data()

        self.pool.close()

        self.pool.join()

        self.grid_timeseries_index()

        self.assemble_chips()

        self.qa = self.mosaic(self.grid, 'qas')

        self.rgb = np.dstack((self.rescale_array(self.mosaic(self.grid, r_channel),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(self.grid, g_channel),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(self.grid, b_channel),
                                                 self.qa, lower, upper))).astype(np.uint8)

        self.pixel_image_affine = GeoAffine(ul_x=self.grid['nw']['geo'].chip_coord.x,
                                            x_res=30,
                                            rot_1=0,
                                            ul_y=self.grid['nw']['geo'].chip_coord.y,
                                            rot_2=0,
                                            y_res=-30)

        self.pixel_rowcol = GeoInfo.geo_to_rowcol(self.pixel_image_affine, GeoCoordinate(x, y))

    def get_params(self):
        """
        Get an iterable containing the parameters for each chip to request via merlin

        """
        return [(data['geo'], self.start, self.stop, self.cfg, loc) for loc, data in self.grid.items()]

    def retrieve_data(self):
        """

        """
        self.pool.map(self.merlin_call, self.params)

    def merlin_call(self, args):
        """

        """
        self.grid[args[-1]]['data'] = merlin.create(x=args[0].coord.x,
                                                    y=args[0].coord.y,
                                                    acquired=f'{args[1]}/{args[2]}',
                                                    cfg=args[3])

    def assemble_chips(self):
        """

        """
        for loc, info in self.grid.items():
            self.grid[loc]['chip'] = tools.assemble(self.grid[loc]['data'], self.grid[loc]['ind'], self.items)

    @staticmethod
    def rescale_array(array, qa, lower=1, upper=99):
        """
        Taking an input array, clip its values using a lower and upper percentage threshold, then rescale the array
        values to 0-255.

        Args:
            array (np.ndarray): The input data
            qa (np.ndarray): The QA array used to ignore cloud/shadow/fill
            lower (int): Lower percentage clipping threshold (default=1)
            upper (int): Upper percentage clipping threshold (default=99)

        Returns:
            np.ndarray

        """
        return Rescale(array, qa, lower, upper).rescaled

    @staticmethod
    def mosaic(grid, ubid):
        """
        Place values from each chip into a larger array

        Args:
            grid (dict): The data structure containing chip arrays
            ubid (str): The band identifier

        Returns:
            np.ndarray

        """
        array = np.zeros((300, 300), dtype=np.int16)

        array[0:100, 0:100] = grid['nw']['chip'][ubid]
        array[100:200, 0:100] = grid['w']['chip'][ubid]
        array[200:, 0:100] = grid['sw']['chip'][ubid]

        array[0:100, 100:200] = grid['n']['chip'][ubid]
        array[100:200, 100:200] = grid['c']['chip'][ubid]
        array[200:, 100:200] = grid['s']['chip'][ubid]

        array[0:100, 200:] = grid['ne']['chip'][ubid]
        array[100:200, 200:] = grid['e']['chip'][ubid]
        array[200:, 200:] = grid['se']['chip'][ubid]

        return array

    def grid_timeseries_index(self):
        """
        A wrapper to get the index within a timeseries for each grid-location in regards to a target date

        """
        for loc, item in self.grid.items():
            self.grid[loc]['ind'] = self.get_index(self.grid[loc]['data'][0][1]['dates'], self.date)

    @staticmethod
    def get_index(array, date):
        """
        Find the index value in the array to the nearest matching date,
        date may therefore not be a value within the array

        Args:
            array (array_like): The input data
            date (dt.datetime): The date to look for given as (Year, Month, M-day)

        Returns:
            int

        """
        date = date.toordinal()

        array = np.asarray(array)

        return (np.abs(array - date)).argmin()

    @staticmethod
    def get_acquired_dates(date, ndays=8):
        """
        Get a small date range to minimize the chipmunk request

        Args:
            date (dt.datetime): The target date
            ndays (int): The number of days calculate the date range using the target date

        Returns:
            Tuple[str, str]: The start and stop dates for a chipmunk request via merlin

        """
        return ((date - dt.timedelta(days=ndays)).strftime('%Y-%m-%d'),
                (date + dt.timedelta(days=ndays)).strftime('%Y-%m-%d'))
