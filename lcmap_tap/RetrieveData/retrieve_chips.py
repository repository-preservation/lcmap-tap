"""Grab some chips to make a pretty picture"""

from lcmap_tap.logger import exc_handler, log
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData.retrieve_ard import ARDData
from lcmap_tap.RetrieveData import GeoCoordinate
from lcmap_tap.RetrieveData.merlin_cfg import make_cfg
import lcmap_tap.Analysis.data_tools as tools
from lcmap_tap.Visualization.rescale import Rescale
from lcmap_tap.Plotting import plot_functions

import sys
import numpy as np
import datetime as dt
from multiprocessing.dummy import Pool as ThreadPool
import merlin
from itertools import chain

sys.excepthook = exc_handler


class Chips:
    index_functions = {'NDVI': {'func': plot_functions.ndvi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                       'MSAVI': {'func': plot_functions.msavi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                       'EVI': {'func': plot_functions.evi, 'bands': ('blues', 'reds', 'nirs'), 'inds': (0, 2, 3)},
                       'SAVI': {'func': plot_functions.savi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                       'NDMI': {'func': plot_functions.ndmi, 'bands': ('nirs', 'swir1s'), 'inds': (3, 4)},
                       'NBR-1': {'func': plot_functions.nbr, 'bands': ('nirs', 'swir2s'), 'inds': (3, 5)},
                       'NBR-2': {'func': plot_functions.nbr2, 'bands': ('swir1s', 'swir2s'), 'inds': (4, 5)}
                       }

    def __init__(self, x, y, date, url,
                 r_channel, g_channel, b_channel,
                 n=9, lower=0, upper=100, **params):
        """

        Args:
            x (coordinate_like): The point of reference x-coordinate
            y (coordinate_like): The point of reference y-coordinate
            date (dt.datetime): The target date
            url (str): The Chipmunk URL
            n (int): Number of chips in mosaic, default is 9
            r_channel (Tuple[str, List[str]): UBID to use for the red color channel (default is 'reds')
            g_channel (Tuple[str, List[str]): UBID to use for the green color channel (default is 'greens')
            b_channel (Tuple[str, List[str]): UBID to use for the blue color channel (default is 'blues')
            lower (float): Lower percentage clipping threshold
            upper (float): Upper percentage clipping threshold

        """
        self.pool = ThreadPool(n)

        self.r_channel = r_channel
        self.g_channel = g_channel
        self.b_channel = b_channel

        self.tile_geo = GeoInfo(str(x), str(y))

        self.items = list(chain(*[self.r_channel[1], self.g_channel[1], self.b_channel[1], ['qas']]))

        self.date = date

        self.start, self.stop = self.get_acquired_dates(self.date, 0)

        self.cfg = make_cfg(self.items, url)

        # A list of upper left chip coordinates to identify which chips to request
        self.coords_snap = tools.zoomout(*tools.align(x, y, url))

        self.coords = tools.zoomout(int(x), int(y))

        self.ul = GeoInfo.find_ul(self.coords)

        self.affine = GeoInfo.get_affine(self.ul.x, self.ul.y)

        self.grid = {c_ul: {'x': c[0],
                            'y': c[1],
                            'x_ul': c_ul[0],
                            'y_ul': c_ul[1],
                            'data': [],
                            'ind': 0
                            } for c_ul, c in zip(self.coords_snap, self.coords)}

        self.params = self.get_params()

        self.retrieve_data()

        self.pool.close()

        self.pool.join()

        self.grid_timeseries_index()

        self.assemble_chips()

        self.check_indices()

        # Note: This is the UL coord of the upper left chip in the mosaic
        self.mosaic_coord_ul = GeoInfo.find_ul(self.coords)

        # Note: This is the UL coord of the lower right chip in the mosaic
        self.mosaic_coord_lr = GeoInfo.find_lr(self.coords)

        self.qa = self.mosaic(grid=self.grid, ubid='qas', ul=self.mosaic_coord_ul, lr=self.mosaic_coord_lr)

        self.rgb = np.dstack((self.rescale_array(self.mosaic(grid=self.grid, ubid=self.r_channel[0],
                                                             ul=self.mosaic_coord_ul, lr=self.mosaic_coord_lr),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(grid=self.grid, ubid=self.g_channel[0],
                                                             ul=self.mosaic_coord_ul, lr=self.mosaic_coord_lr),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(grid=self.grid, ubid=self.b_channel[0],
                                                             ul=self.mosaic_coord_ul, lr=self.mosaic_coord_lr),
                                                 self.qa, lower, upper))).astype(np.uint8)

        self.pixel_rowcol = GeoInfo.geo_to_rowcol(self.affine, GeoCoordinate(x, y))

    def check_indices(self):
        """
        Check to see if an index was selected, if so, calculate it

        """
        selected_items = [self.r_channel[0], self.g_channel[0], self.b_channel[0]]

        indices = self.index_functions.keys()

        for i in selected_items:
            if i in indices:
                call = self.index_functions[i]['func']

                for loc, item in self.grid.items():
                    args = tuple([self.grid[loc]['chip'][band] for band in self.index_functions[i]['bands']])

                    # Calculate the index and add it to the dictionary referenced by 'chip'
                    self.grid[loc]['chip'][i] = call(*args)

    def get_params(self):
        """
        Get an iterable containing the parameters for each chip to request via merlin

        """
        return [{'x': info['x'],
                 'y': info['y'],
                 'start': self.start,
                 'stop': self.stop,
                 'cfg': self.cfg,
                 'id': key}
                for key, info in self.grid.items()]

    def retrieve_data(self):
        """

        """
        self.pool.map(self.merlin_call, self.params)

    def merlin_call(self, params):
        """

        """
        # self.grid[args[4]]['data'] = merlin.create(x=args[0].coord.x,
        #                                             y=args[0].coord.y,
        #                                             acquired=f'{args[1]}/{args[2]}',
        #                                             cfg=args[3])

        self.grid[params['id']]['data'] = merlin.create(x=params['x'],
                                                        y=params['y'],
                                                        acquired=f"{params['start']}/{params['stop']}",
                                                        cfg=params['cfg'])

    def assemble_chips(self):
        """

        """
        for loc in self.grid.keys():
            self.grid[loc]['chip'] = tools.assemble(self.grid[loc]['data'], self.grid[loc]['ind'], self.items)

    @staticmethod
    def rescale_array(array, qa, lower=1, upper=99):
        """
        Taking an input array, clip its values using a lower and upper percentage threshold, then rescale the array
        values to 0-255.

        Args:
            array (np.ndarray): The input data
            qa (np.ndarray): The QA array used to ignore cloud/shadow/fill
            lower (float): Lower percentage clipping threshold (default=1)
            upper (float): Upper percentage clipping threshold (default=99)

        Returns:
            np.ndarray

        """
        return Rescale(array, qa, lower, upper).rescaled

    @staticmethod
    def mosaic(grid, ubid, ul, lr):
        """
        Place values from each chip into a larger array

        Args:
            grid (dict): The data structure containing chip arrays
            ubid (str): The band identifier
            ul (GeoCoordinate): The upper left coordinate of the upper left chip in the mosaic
            lr (GeoCoordinate): The upper left coordinate of the lower right chip in the mosaic

        Returns:
            np.ndarray

        """
        ubid_lookup = {'Red': {'ubid': 'reds', 'dtype': np.int16},
                       'Green': {'ubid': 'greens', 'dtype': np.int16},
                       'Blue': {'ubid': 'blues', 'dtype': np.int16},
                       'NIR': {'ubid': 'nirs', 'dtype': np.int16},
                       'SWIR-1': {'ubid': 'swir1s', 'dtype': np.int16},
                       'SWIR-2': {'ubid': 'swir2s', 'dtype': np.int16},
                       'Thermal': {'ubid': 'thermals', 'dtype': np.int16},
                       'NDVI': {'ubid': 'NDVI', 'dtype': np.float64},
                       'MSAVI': {'ubid': 'MSAVI', 'dtype': np.float64},
                       'SAVI': {'ubid': 'SAVI', 'dtype': np.float64},
                       'EVI': {'ubid': 'EVI', 'dtype': np.float64},
                       'NDMI': {'ubid': 'NDMI', 'dtype': np.float64},
                       'NBR-1': {'ubid': 'NBR-1', 'dtype': np.float64},
                       'NBR-2': {'ubid': 'NBR-2', 'dtype': np.float64},
                       'qas': {'ubid': 'qas', 'dtype': np.int16}, }

        array = np.zeros(shape=tools.findrowscols(ul, lr))

        for chip in grid.keys():
            coord = GeoCoordinate(x=grid[chip]['x'], y=grid[chip]['y'])

            row, column = GeoInfo.geo_to_rowcol(GeoInfo.get_affine(ul.x, ul.y), coord)

            array[row: row + 100, column: column + 100] = grid[chip]['chip'][ubid_lookup[ubid]['ubid']]

        return array

    def grid_timeseries_index(self):
        """
        A wrapper to get the index within a timeseries for each grid-location in regards to a target date

        """
        log.debug("coords_snap: %s" % str(self.coords_snap[0]))

        log.debug("tile_geo pixel_coord_ul: %s" % str(self.tile_geo.pixel_coord_ul))

        temp = ARDData.get_sequence(timeseries=self.grid[self.tile_geo.chip_coord_ul]['data'],
                                    pixel_coord=self.tile_geo.pixel_coord_ul)

        ind = self.get_index(temp['dates'], self.date)

        for loc, item in self.grid.items():
            self.grid[loc]['ind'] = ind

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
