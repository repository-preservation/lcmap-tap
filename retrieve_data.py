import datetime as dt
import json
import os
import re
import sys
from collections import namedtuple
import numpy as np

from Plotting import plot_functions


class CCDReader:
    # Define some helper methods and data structures

    GeoExtent = namedtuple("GeoExtent", ["x_min", "y_max", "x_max", "y_min"])
    GeoAffine = namedtuple("GeoAffine", ["ul_x", "x_res", "rot_1", "ul_y", "rot_2", "y_res"])
    GeoCoordinate = namedtuple("GeoCoordinate", ["x", "y"])
    RowColumn = namedtuple("RowColumn", ["row", "column"])
    RowColumnExtent = namedtuple("RowColumnExtent", ["start_row", "start_col", "end_row", "end_col"])

    def __init__(self, h, v, arc_coords, cache_dir, json_dir, output_dir, masked_on=True, model_on=True):

        # ****Setup file locations****
        self.OutputDir = output_dir

        if not os.path.exists(self.OutputDir):
            os.makedirs(self.OutputDir)

        self.CACHE_INV = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir)]

        self.JSON_INV = [os.path.join(json_dir, f) for f in os.listdir(json_dir)]

        # ****Setup geospatial and temporal information****
        self.CONUS_EXTENT = self.GeoExtent(x_min=-2565585,
                                           y_min=14805,
                                           x_max=2384415,
                                           y_max=3314805)

        self.H = h
        self.V = v

        self.EXTENT, self.PIXEL_AFFINE = self.geospatial_hv(self.H, self.V, self.CONUS_EXTENT)

        self.CHIP_AFFINE = self.GeoAffine(ul_x=self.PIXEL_AFFINE.ul_x, x_res=3000, rot_1=0, ul_y=self.PIXEL_AFFINE.ul_y,
                                          rot_2=0,
                                          y_res=-3000)

        self.arc_paste = arc_coords

        self.coord = self.arcpaste_to_coord(self.arc_paste)

        self.results = self.extract_jsoncurve(self.coord)

        self.data, self.dates = self.extract_cachepoint(self.coord, self.results['processing_mask'])

        # self.BEGIN_DATE = dt.date(year=1982, month=1, day=1)
        # self.END_DATE = dt.date(year=2015, month=12, day=31)
        self.BEGIN_DATE = dt.datetime.fromordinal(self.dates[0])
        self.END_DATE = dt.datetime.fromordinal(self.dates[len(self.results["processing_mask"]) - 1])

        self.date_mask = self.mask_daterange(self.dates)

        self.dates_in = self.dates[self.date_mask]
        self.dates_out = self.dates[~self.date_mask]

        self.data_in = self.data[self.date_mask]
        self.data_out = self.data[~self.date_mask]

        self.test_data()

        self.qa = self.data[-1]
        self.qa_mask = np.ones_like(self.qa, dtype=np.bool)
        self.qa_mask[self.qa == 1] = False

        self.qa_in = self.qa_mask[self.date_mask]
        self.qa_out = self.qa_mask[~self.date_mask]

        self.mask = np.array(self.results['processing_mask'], dtype=bool)

        self.total_mask = np.logical_and(self.mask, self.qa_mask)

        # Fix the scaling of the Brightness Temperature
        # self.data_in[6][self.data_in[6] != -9999] = self.data_in[6][self.data_in[6] != -9999] * 10 - 27315
        # self.data_out[6][self.data_out[6] != -9999] = self.data_out[6][self.data_out[6] != -9999] * 10 - 27315
        self.temp_thermal = np.copy(self.data[6])
        self.temp_thermal[self.qa_mask] = self.temp_thermal[self.qa_mask] * 10 - 27315
        self.data[6] = np.copy(self.temp_thermal)

        self.bands = ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal')
        self.indices = ('ndvi', 'msavi', 'evi', 'savi', 'ndmi', 'nbr', 'nbr2')

        self.band_info = {b: {'coefs': [], 'inter': [], 'pred': []} for b in self.bands}

        # self.mask = np.ones_like(self.dates_in, dtype=bool)

        # self.mask[: len(self.results['processing_mask'])] = self.results['processing_mask']

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

                # intercept = result[b]['intercept']
                # coef = result[b]['coefficients']

                self.prediction_dates.append(days)
                self.predicted_values.append(self.band_info[b]['pred'])

        self.model_on = model_on

        self.masked_on = masked_on

        # Calculate indices from observed values
        self.EVI = plot_functions.evi(B=self.data[0], NIR=self.data[3], R=self.data[2])

        self.NDVI = plot_functions.ndvi(R=self.data[2], NIR=self.data[3])

        self.MSAVI = plot_functions.msavi(R=self.data[2], NIR=self.data[3])

        self.SAVI = plot_functions.savi(R=self.data[2], NIR=self.data[3])

        self.NDMI = plot_functions.ndmi(NIR=self.data[3], SWIR1=self.data[4])

        self.NBR = plot_functions.nbr(NIR=self.data[3], SWIR2=self.data[5])

        self.NBR2 = plot_functions.nbr2(SWIR1=self.data[4], SWIR2=self.data[5])

        # Calculate indices from model predicted values
        # TODO update get_predicts to take in a list and use for the indices predicted values

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

        self.index_lookup = {"ndvi": (self.NDVI, self.NDVI_),
                             "msavi": (self.MSAVI, self.MSAVI_),
                             "evi": (self.EVI, self.EVI_),
                             "savi": (self.SAVI, self.SAVI_),
                             "ndmi": (self.NDMI, self.NDMI_),
                             "nbr": (self.NBR, self.NBR_),
                             "nbr2": (self.NBR2, self.NBR2_)}

        self.band_lookup = {"blue": (self.data[0], self.get_predicts(0)),
                            "green": (self.data[1], self.get_predicts(1)),
                            "red": (self.data[2], self.get_predicts(2)),
                            "nir": (self.data[3], self.get_predicts(3)),
                            "swir-1": (self.data[4], self.get_predicts(4)),
                            "swir-2": (self.data[5], self.get_predicts(5)),
                            "thermal": (self.data[6], self.get_predicts(6))}

        self.all_lookup = {**self.index_lookup, **self.band_lookup}

    def geospatial_hv(self, h, v, loc):
        """
        :param h: 
        :param v: 
        :param loc: 
        :return: 
        """

        xmin = loc.x_min + h * 5000 * 30
        xmax = loc.x_min + h * 5000 * 30 + 5000 * 30
        ymax = loc.y_max - v * 5000 * 30
        ymin = loc.y_max - v * 5000 * 30 - 5000 * 30

        return (self.GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin),
                self.GeoAffine(ul_x=xmin, x_res=30, rot_1=0, ul_y=ymax, rot_2=0, y_res=-30))

    def geo_to_rowcol(self, affine, coord):
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

        return self.RowColumn(row=int(row),
                              column=int(col))

    def rowcol_to_geo(self, affine, rowcol):
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

        return self.GeoCoordinate(x=x, y=y)

    def load_cache(self, file):
        """
        Load the cache file and split the data into the image IDs and values
        :param file: 
        :return: 
        """

        data = np.load(file)

        return data["Y"], data["image_IDs"]

    def find_file(self, file_ls, string):
        """
        Return the first str in a list of strings that contains 'string'.
        :param file_ls: 
        :param string: 
        :return: 
        """

        gen = filter(lambda x: string in x, file_ls)

        return next(gen, None)

    def imageid_date(self, image_ids):
        """
        Extract the ordinal day from the ARD image name.
        :param image_ids: 
        :return: 
        """

        return np.array([dt.datetime.strptime(d[15:23], "%Y%m%d").toordinal()
                         for d in image_ids])

    def mask_daterange_edit(self, dates):
        """
        Create a mask for values outside of the global BEGIN_DATE and END_DATE.
        :param dates: 
        :return: 
        """

        mask_in = np.zeros_like(dates, dtype=bool)
        mask_out = np.copy(mask_in)

        mask_in[(dates > self.BEGIN_DATE.toordinal()) & (dates < self.END_DATE.toordinal())] = 1
        mask_out[(dates <= self.BEGIN_DATE.toordinal()) | (dates >= self.END_DATE.toordinal())] = 1

        return mask_in, mask_out

    def mask_daterange(self, dates):
        """
        Create a mask for values outside of the global BEGIN_DATE and END_DATE.
        :param dates:
        :return:
        """

        return np.logical_and(dates >= self.BEGIN_DATE.toordinal(), dates <= self.END_DATE.toordinal())

    def find_chipcurve(self, results_chip, coord):
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

    def extract_cachepoint(self, coord, results):
        """
        Extract the spectral values from the cache file
        :param coord:
        :param results:
        :return:
        """

        rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, coord)

        data, image_ids = self.load_cache(self.find_file(self.CACHE_INV, f"r{rowcol.row}"))

        dates = self.imageid_date(image_ids)

        return data[:, :, rowcol.column], dates

    def extract_cachepoint_edit(self, coord, results):

        """
        Extract the spectral values from the cache file and remove duplicate dates.
        :param results: 
        :param coord: 
        :return: 
        """

        rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, coord)

        data, image_ids = self.load_cache(self.find_file(self.CACHE_INV, "r{}".format(rowcol.row)))

        dates = self.imageid_date(image_ids)

        dates_, indices = np.unique(dates, return_index=True)

        data_ = data[:, indices]

        mask_in, mask_out = self.mask_daterange_edit(dates_)

        # Check if the len of the processing mask equals the len of dates with duplicates removed
        # For most cases the length of the internal processing mask should be equal to the
        # number of observations within the BEGIN and END date range
        if len(results) == len(dates_[mask_in]):

            print("The length of the pyccd internal processing mask ({}) is consistent with the number of observations"
                  " in the cache files ({}) with duplicate dates removed".format(len(results),
                                                                                 len(dates_[mask_in])))

            # mask_in, mask_out = mask_daterange(dates_)

            return data_[:, mask_in, rowcol.column], dates_[mask_in], \
                   data_[:, mask_out, rowcol.column], dates_[mask_out]

        elif len(results) != len(dates_[mask_in]):

            mask_in, mask_out = self.mask_daterange(dates)

            if len(results) == len(dates[mask_in]):

                print("The length of the pyccd internal processing mask ({}) is consistent with the "
                      "number of observations in the cache files ({}) if duplicate dates are not "
                      "removed".format(len(results), len(dates[mask_in])))

                return data[:, mask_in, rowcol.column], dates[mask_in], \
                       data[:, mask_out, rowcol.column], dates[mask_out]

            else:

                print("The length of the pyccd internal processing mask ({}) is inconsistent with"
                      " the number of observations provided in the cache files ({})".format(len(results),
                                                                                            len(dates[mask_in])))

                sys.exit(1)

        return None

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

        if result.get("result_ok") is True:
            return json.loads(result["result"])

    def predicts(self, days, coef, intercept):
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

    def arcpaste_to_coord(self, string):
        """

        :param string: 
        :return: 
        """

        pieces = string.split()

        return self.GeoCoordinate(x=float(re.sub(",", "", pieces[0])),
                                  y=float(re.sub(",", "", pieces[1])))

    def test_data(self):

        if len(self.dates_in) == len(self.results["processing_mask"]):
            print("The number of observations is consistent with the length of the PyCCD internal processing mask.\n"
                  "No changes to the input observations are necessary.")

            return None

        if len(np.unique(self.dates_in)) == len(self.results["processing_mask"]):
            print("There is a duplicate date occurrence in observations.  Removing duplicate occurrences makes the "
                  "number of observations consistent with the length of the PyCCD internal processing mask.")

            self.dates_in, ind = np.unique(self.dates_in, return_index=True)
            self.data_in = self.data_in[:, ind]

            return None

    def get_predicts(self, num):

        return [self.predicted_values[m * len(self.bands) + num] for m in range(len(self.results["change_models"]))]
