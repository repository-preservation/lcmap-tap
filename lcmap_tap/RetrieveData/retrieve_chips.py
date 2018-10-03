"""Grab some chips to make a pretty picture"""

from lcmap_tap.logger import exc_handler
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData.retrieve_ard import ARDData
from lcmap_tap.RetrieveData import GeoAffine, GeoCoordinate
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

        self.start, self.stop = self.get_acquired_dates(self.date)

        self.cfg = make_cfg(self.items, url)

        # 3000 = 30m pixel x 100m chip-length
        self.grid = {
            'n': {'geo': GeoInfo(str(x), str(y + 3000))},

            'c': {'geo': GeoInfo(str(x), str(y))},

            's': {'geo': GeoInfo(str(x), str(y - 3000))},

            'nw': {'geo': GeoInfo(str(x - 3000), str(y + 3000))},

            'w': {'geo': GeoInfo(str(x - 3000), str(y))},

            'sw': {'geo': GeoInfo(str(x - 3000), str(y - 3000))},

            'ne': {'geo': GeoInfo(str(x + 3000), str(y + 3000))},

            'e': {'geo': GeoInfo(str(x + 3000), str(y))},

            'se': {'geo': GeoInfo(str(x + 3000), str(y - 3000))}
        }

        self.params = self.get_params()

        self.retrieve_data()

        self.pool.close()

        self.pool.join()

        self.grid_timeseries_index()

        self.assemble_chips()

        self.check_indices()

        self.qa = self.mosaic(self.grid, 'qas')

        self.rgb = np.dstack((self.rescale_array(self.mosaic(self.grid, self.r_channel[0]),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(self.grid, self.g_channel[0]),
                                                 self.qa, lower, upper),

                              self.rescale_array(self.mosaic(self.grid, self.b_channel[0]),
                                                 self.qa, lower, upper))).astype(np.uint8)

        self.pixel_image_affine = GeoAffine(ul_x=self.grid['nw']['geo'].chip_coord.x,
                                            x_res=30,
                                            rot_1=0,
                                            ul_y=self.grid['nw']['geo'].chip_coord.y,
                                            rot_2=0,
                                            y_res=-30)

        self.pixel_rowcol = GeoInfo.geo_to_rowcol(self.pixel_image_affine, GeoCoordinate(x, y))

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

                    # Calculate the index
                    self.grid[loc]['chip'][i] = call(*args)

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
        self.grid[args[4]]['data'] = merlin.create(x=args[0].coord.x,
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
            lower (float): Lower percentage clipping threshold (default=1)
            upper (float): Upper percentage clipping threshold (default=99)

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
                       'qas': {'ubid': 'qas', 'dtype': np.int16},}

        array = np.zeros((300, 300), dtype=ubid_lookup[ubid]['dtype'])

        array[0:100, 0:100] = grid['nw']['chip'][ubid_lookup[ubid]['ubid']]
        array[100:200, 0:100] = grid['w']['chip'][ubid_lookup[ubid]['ubid']]
        array[200:, 0:100] = grid['sw']['chip'][ubid_lookup[ubid]['ubid']]

        array[0:100, 100:200] = grid['n']['chip'][ubid_lookup[ubid]['ubid']]
        array[100:200, 100:200] = grid['c']['chip'][ubid_lookup[ubid]['ubid']]
        array[200:, 100:200] = grid['s']['chip'][ubid_lookup[ubid]['ubid']]

        array[0:100, 200:] = grid['ne']['chip'][ubid_lookup[ubid]['ubid']]
        array[100:200, 200:] = grid['e']['chip'][ubid_lookup[ubid]['ubid']]
        array[200:, 200:] = grid['se']['chip'][ubid_lookup[ubid]['ubid']]

        return array

    def grid_timeseries_index(self):
        """
        A wrapper to get the index within a timeseries for each grid-location in regards to a target date

        """
        temp = ARDData.get_sequence(self.grid['c']['data'], self.tile_geo.pixel_coord)

        ind = self.get_index(temp['dates'], self.date)

        for loc, item in self.grid.items():
            # temp = ARDData.get_sequence(timeseries=self.grid[loc]['data'], pixel_coord=self.tile_geo.pixel_coord)

            # self.grid[loc]['ind'] = self.get_index(array=self.grid[loc]['data'][0][1]['dates'],
            #                                        qa=self.grid[loc]['data'][0][1]['qas'],
            #                                        date=self.date)

            # self.grid[loc]['ind'] = self.get_index(array=temp['dates'],
            #                                        qa=temp['qas'],
            #                                        date=self.date)

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
