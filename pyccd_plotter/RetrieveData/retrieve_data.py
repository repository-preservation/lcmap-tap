"""Retrieve data, make it accessible via attributes of the CCDReader class"""
import datetime as dt
import json
import os
import re
from collections import Counter
from collections import OrderedDict
from collections import namedtuple

import numpy as np

from pyccd_plotter.Plotting import plot_functions

# Define some helper methods and data structures
GeoExtent = namedtuple("GeoExtent", ["x_min", "y_max", "x_max", "y_min"])
GeoAffine = namedtuple("GeoAffine", ["ul_x", "x_res", "rot_1", "ul_y", "rot_2", "y_res"])
GeoCoordinate = namedtuple("GeoCoordinate", ["x", "y"])
RowColumn = namedtuple("RowColumn", ["row", "column"])
RowColumnExtent = namedtuple("RowColumnExtent", ["start_row", "start_col", "end_row", "end_col"])
CONUS_EXTENT = GeoExtent(x_min=-2565585,
                         y_min=14805,
                         x_max=2384415,
                         y_max=3314805)


class CCDReader:
    def __init__(self, h, v, arc_coords, cache_dir, json_dir):
        """

        :param h:
        :param v:
        :param arc_coords:
        :param cache_dir:
        :param json_dir:
        """
        # ****Setup file locations****
        self.H = h
        self.V = v

        self.CACHE_INV = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir)]

        self.JSON_INV = [os.path.join(json_dir, f) for f in os.listdir(json_dir)]

        # ****Setup geospatial and temporal information****

        self.EXTENT, self.PIXEL_AFFINE = self.geospatial_hv(CONUS_EXTENT)

        self.CHIP_AFFINE = GeoAffine(ul_x=self.PIXEL_AFFINE.ul_x,
                                     x_res=3000,
                                     rot_1=0,
                                     ul_y=self.PIXEL_AFFINE.ul_y,
                                     rot_2=0,
                                     y_res=-3000)

        self.coord = self.arcpaste_to_coord(arc_coords)

        self.results = self.extract_jsoncurve(self.coord)

        self.data, self.dates, self.image_ids = self.extract_cachepoint(self.coord)

        self.BEGIN_DATE = dt.date(year=1982, month=1, day=1)
        self.END_DATE = dt.date(year=2015, month=12, day=31)

        self.date_mask = self.mask_daterange(self.dates)

        self.dates_in = self.dates[self.date_mask]
        self.dates_out = self.dates[~self.date_mask]

        self.ccd_mask = np.array(self.results['processing_mask'], dtype=bool)

        self.test_data()

        self.qa = self.data[-1]

        self.fill_mask = np.ones_like(self.qa, dtype=np.bool)
        self.fill_mask[self.qa == 1] = False

        self.fill_in = self.fill_mask[self.date_mask]
        self.fill_out = self.fill_mask[~self.date_mask]

        self.total_mask = np.logical_and(self.ccd_mask, self.fill_in)

        # Fix the scaling of the Brightness Temperature
        self.temp_thermal = np.copy(self.data[6])
        self.temp_thermal[self.fill_mask] = self.temp_thermal[self.fill_mask] * 10 - 27315
        self.data[6] = np.copy(self.temp_thermal)

        self.bands = ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal')
        self.indices = ('ndvi', 'msavi', 'evi', 'savi', 'ndmi', 'nbr', 'nbr2')

        self.band_info = {b: {'coefs': [], 'inter': [], 'pred': []} for b in self.bands}

        self.predicted_values = []
        self.prediction_dates = []
        self.break_dates = []
        self.start_dates = []
        self.end_dates = []

        for num, result in enumerate(self.results['change_models']):
            days = np.arange(result['start_day'], result['end_day'] + 1)

            self.break_dates.append(result['break_day'])

            self.start_dates.append(result['start_day'])

            self.end_dates.append(result['end_day'])

            for b in self.bands:
                self.band_info[b]['inter'] = result[b]['intercept']

                self.band_info[b]['coefs'] = result[b]['coefficients']

                self.band_info[b]['pred'] = self.predicts(days, result[b]['coefficients'], result[b]['intercept'])

                self.prediction_dates.append(days)

                self.predicted_values.append(self.band_info[b]['pred'])

        #### Calculate indices from observed values ####
        self.EVI = plot_functions.evi(B=self.data[0].astype(np.float), NIR=self.data[3].astype(np.float),
                                      R=self.data[2].astype(np.float))

        self.NDVI = plot_functions.ndvi(R=self.data[2].astype(np.float), NIR=self.data[3].astype(np.float))

        self.MSAVI = plot_functions.msavi(R=self.data[2].astype(np.float), NIR=self.data[3].astype(np.float))

        self.SAVI = plot_functions.savi(R=self.data[2].astype(np.float), NIR=self.data[3].astype(np.float))

        self.NDMI = plot_functions.ndmi(NIR=self.data[3].astype(np.float), SWIR1=self.data[4].astype(np.float))

        self.NBR = plot_functions.nbr(NIR=self.data[3].astype(np.float), SWIR2=self.data[5].astype(np.float))

        self.NBR2 = plot_functions.nbr2(SWIR1=self.data[4].astype(np.float), SWIR2=self.data[5].astype(np.float))

        #### Calculate indices from the results' change models. ####
        # The change models are stored by order of model, then
        # band number.  For example, the band values for the first change model are represented by indices 0-5,
        # the second model by indices 6-11, and so on.
        self.NDVI_ = [plot_functions.ndvi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                          R=self.predicted_values[m * len(self.bands) + 2])
                      for m in range(len(self.results["change_models"]))]

        self.MSAVI_ = [plot_functions.msavi(R=self.predicted_values[m * len(self.bands) + 2],
                                            NIR=self.predicted_values[m * len(self.bands) + 3])
                       for m in range(len(self.results["change_models"]))]

        self.EVI_ = [plot_functions.evi(B=self.predicted_values[m * len(self.bands)],
                                        NIR=self.predicted_values[m * len(self.bands) + 3],
                                        R=self.predicted_values[m * len(self.bands) + 2])
                     for m in range(len(self.results["change_models"]))]

        self.SAVI_ = [plot_functions.savi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                          R=self.predicted_values[m * len(self.bands) + 2])
                      for m in range(len(self.results["change_models"]))]

        self.NDMI_ = [plot_functions.ndmi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                          SWIR1=self.predicted_values[m * len(self.bands) + 4])
                      for m in range(len(self.results["change_models"]))]

        self.NBR_ = [plot_functions.nbr(NIR=self.predicted_values[m * len(self.bands) + 3],
                                        SWIR2=self.predicted_values[m * len(self.bands) + 5])
                     for m in range(len(self.results["change_models"]))]

        self.NBR2_ = [plot_functions.nbr2(SWIR1=self.predicted_values[m * len(self.bands) + 4],
                                          SWIR2=self.predicted_values[m * len(self.bands) + 5])
                      for m in range(len(self.results["change_models"]))]

        # Use a list of tuples for passing to OrderedDict so the order of element insertion is preserved
        # The dictionaries are used to map selections from the GUI to the corresponding plot data
        self.index_lookup = [("NDVI", (self.NDVI, self.NDVI_)),
                             ("MSAVI", (self.MSAVI, self.MSAVI_)),
                             ("EVI", (self.EVI, self.EVI_)),
                             ("SAVI", (self.SAVI, self.SAVI_)),
                             ("NDMI", (self.NDMI, self.NDMI_)),
                             ("NBR", (self.NBR, self.NBR_)),
                             ("NBR-2", (self.NBR2, self.NBR2_))]

        self.index_lookup = OrderedDict(self.index_lookup)

        self.band_lookup = [("Blue", (self.data[0], self.get_predicts(0))),
                            ("Green", (self.data[1], self.get_predicts(1))),
                            ("Red", (self.data[2], self.get_predicts(2))),
                            ("NIR", (self.data[3], self.get_predicts(3))),
                            ("SWIR-1", (self.data[4], self.get_predicts(4))),
                            ("SWIR-2", (self.data[5], self.get_predicts(5))),
                            ("Thermal", (self.data[6], self.get_predicts(6)))]

        self.band_lookup = OrderedDict(self.band_lookup)

        # Combine these two dictionaries
        # self.all_lookup = {**self.band_lookup, **self.index_lookup}
        self.all_lookup = plot_functions.merge_dicts(self.band_lookup, self.index_lookup)

    def geospatial_hv(self, loc):
        """

        :param loc:
        :return:
        """
        xmin = loc.x_min + self.H * 5000 * 30
        xmax = loc.x_min + self.H * 5000 * 30 + 5000 * 30
        ymax = loc.y_max - self.V * 5000 * 30
        ymin = loc.y_max - self.V * 5000 * 30 - 5000 * 30

        return (GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin),
                GeoAffine(ul_x=xmin, x_res=30, rot_1=0, ul_y=ymax, rot_2=0, y_res=-30))

    @staticmethod
    def geo_to_rowcol(affine, coord):
        """
        Transform geo-coordinate to row/col given a reference affine

        Yline = (Ygeo - GT(3) - Xpixel*GT(4)) / GT(5)
        Xpixel = (Xgeo - GT(0) - Yline*GT(2)) / GT(1)

        :param affine:
        :param coord:
        :return:
        """

        row = (coord.y - affine.ul_y - affine.ul_x * affine.rot_2) / affine.y_res
        col = (coord.x - affine.ul_x - affine.ul_y * affine.rot_1) / affine.x_res

        return RowColumn(row=int(row), column=int(col))

    @staticmethod
    def rowcol_to_geo(affine, rowcol):
        """
        Transform a row/col into a geospatial coordinate given reference affine.

        Xgeo = GT(0) + Xpixel*GT(1) + Yline*GT(2)
        Ygeo = GT(3) + Xpixel*GT(4) + Yline*GT(5)

        :param affine: 
        :param rowcol: 
        :return: 
        """

        x = affine.ul_x + rowcol.column * affine.x_res + rowcol.row * affine.rot_1
        y = affine.ul_y + rowcol.column * affine.rot_2 + rowcol.row * affine.y_res

        return GeoCoordinate(x=x, y=y)

    @staticmethod
    def load_cache(file):
        """
        Load the cache file and split the data into the image IDs and values
        :param file:
        :return:
        """
        data = np.load(file)

        return data["Y"], data["image_IDs"]

    @staticmethod
    def find_file(file_ls, string):
        """
        Return the first str in a list of strings that contains 'string'.
        :param file_ls: 
        :param string: 
        :return: 
        """
        gen = filter(lambda x: string in x, file_ls)

        return next(gen, None)

    @staticmethod
    def imageid_date(image_ids):
        """
        Extract the ordinal day from the ARD image name.
        :param image_ids: 
        :return: 
        """
        return np.array([dt.datetime.strptime(d[15:23], "%Y%m%d").toordinal()
                         for d in image_ids])

    def mask_daterange(self, dates):
        """
        Create a mask for values outside of the global BEGIN_DATE and END_DATE.
        :param dates:
        :return:
        """
        return np.logical_and(dates >= self.BEGIN_DATE.toordinal(), dates < self.END_DATE.toordinal())

    @staticmethod
    def find_chipcurve(results_chip, coord):
        """
        Find the results for the specified coordinate.
        :param results_chip: 
        :param coord: 
        :return: 
        """

        with open(results_chip, "r") as f:
            results = json.load(f)

        gen = filter(lambda x: coord.x == x["x"] and coord.y == x["y"], results)

        return next(gen, None)

    def extract_cachepoint(self, coord):
        """
        Extract the spectral values from the cache file
        :param coord:
        :return:
        """
        rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, coord)

        data, image_ids = self.load_cache(self.find_file(self.CACHE_INV, "r{}".format(rowcol.row)))

        dates = self.imageid_date(image_ids)

        return data[:, :, rowcol.column], dates, image_ids

    def extract_jsoncurve(self, coord):
        """
        Extract the pyccd information from the json file representing a chip of results.
        """
        pixel_rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, coord)
        pixel_coord = self.rowcol_to_geo(self.PIXEL_AFFINE, pixel_rowcol)

        chip_rowcol = self.geo_to_rowcol(self.CHIP_AFFINE, coord)
        chip_coord = self.rowcol_to_geo(self.CHIP_AFFINE, chip_rowcol)

        file = self.find_file(self.JSON_INV,
                              "H{:02d}V{:02d}_{}_{}.json".format(self.H, self.V, chip_coord.x, chip_coord.y))
        result = self.find_chipcurve(file, pixel_coord)

        return json.loads(result["result"])

    @staticmethod
    def predicts(days, coef, intercept):
        """

        :param days: 
        :param coef: 
        :param intercept: 
        :return: 
        """
        return (intercept + coef[0] * days +
                coef[1] * np.cos(days * 1 * 2 * np.pi / 365.25) + coef[2] * np.sin(days * 1 * 2 * np.pi / 365.25) +
                coef[3] * np.cos(days * 2 * 2 * np.pi / 365.25) + coef[4] * np.sin(days * 2 * 2 * np.pi / 365.25) +
                coef[5] * np.cos(days * 3 * 2 * np.pi / 365.25) + coef[6] * np.sin(days * 3 * 2 * np.pi / 365.25))

    @staticmethod
    def arcpaste_to_coord(string):
        """

        :param string: 
        :return: 
        """
        pieces = string.split()

        return GeoCoordinate(x=float(re.sub(",", "", pieces[0])),
                             y=float(re.sub(",", "", pieces[1])))

    def test_data(self):
        """
        Test the dates for the presence of duplicates, and compare dates with and without duplicate counts to the number
        of elements in the PyCCD internal processing mask.

        One possible source of duplicates is equal date observations from Landsat 7 and 8.  During Landsat 8's
        ascension into orbit there was a brief period of time where the two sensors 'overlapped' to allow instrument
        calibration, so duplicate acquisitions are possible but shouldn't be present because these particular Landsat 8
        observations should have been removed from the ARD source directory.

        Another potential source of duplicate observations (i.e. dates) is when the ARD is re-ingested, it's scene ID
        may contain a different access date.

        For example:
        LE07_CU_013005_20041223_20170731_C01_V01
        LE07_CU_013005_20041223_20170801_C01_V01

        These folders contain the same Landsat 7 observation acquired on 2004-12-23 but they have different accessed
        dates.

        :return:
        """
        if len(self.dates_in) == len(self.ccd_mask):
            print("The number of observations is consistent with the length of the PyCCD internal processing mask.\n"
                  "No changes to the input observations are necessary.")

            return None

        if len(np.unique(self.dates_in)) != len(self.dates_in) and len(np.unique(self.dates_in)) == len(self.ccd_mask):
            print("There is a duplicate date occurrence in observations.  Removing duplicate occurrences makes the "
                  "number of observations consistent with the length of the PyCCD internal processing mask.")

            # Make a list of the duplicate occurrences
            dupes = [item for item, count in Counter(self.dates).items() if count > 1]

            self.dates, ind, counts = np.unique(self.dates, return_index=True, return_counts=True)

            print("Duplicate dates: \n\t{}".format([dt.datetime.fromordinal(d) for d in dupes]))

            # Slice out the duplicate observation from each band
            self.data = self.data[:, ind]

            # Regenerate the date_masks
            self.date_mask = self.mask_daterange(self.dates)

            self.dates_in = self.dates[self.date_mask]

            self.dates_out = self.dates[~self.date_mask]

            return None

        if len(self.dates_in) != len(self.ccd_mask) and len(np.unique(self.dates_in)) != len(self.ccd_mask):
            # Sometimes PyCCD uses a different end date which might cause the inconsistency in mask lengths
            self.END_DATE = dt.date(year=2016, month=1, day=1)

            # Regenerate the date_masks
            self.date_mask = self.mask_daterange(self.dates)

            self.dates_in = self.dates[self.date_mask]

            self.dates_out = self.dates[~self.date_mask]

            # Try using the inclusive date mask
            if len(self.dates_in) == len(self.ccd_mask):
                print("The number of observations is consistent with the length of the PyCCD internal processing mask\n"
                      "if the END DATE is changed to 2016-01-01.\nNo other changes are necessary.")

                return None

            # If the inclusive date mask doesn't match the processing mask, then resort to using the PIXELQA
            else:
                print("There is an unresolved inconsistency with the length of the processing mask, therefore it will "
                      "not be used.\nThe PIXELQA band will solely be used to filter observations.")

                self.ccd_mask = self.get_pqa_mask()

                return None

    def get_predicts(self, num):
        """
        Return the list of model prediction values in the time series for a particular band or bands

        :param num: int or list
        :return: list
        """

        # Check for type int, create list if true
        if isinstance(num, int):
            num = [num]

        return [self.predicted_values[m * len(self.bands) + n] for n in num
                for m in range(len(self.results["change_models"]))]

    def get_pqa_mask(self):
        """
        Generate a mask from the Pixel QA
        :return:
        """
        clr_vals = [66, 68, 322, 324]

        pixelqa_in = self.qa[self.date_mask]

        pixelqa_mask = np.zeros_like(pixelqa_in, dtype=np.bool)

        for val in clr_vals:
            pixelqa_mask[pixelqa_in == val] = True

        return pixelqa_mask
