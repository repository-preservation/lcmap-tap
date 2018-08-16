"""Prepare data for plotting"""

from lcmap_tap.logger import log
from lcmap_tap.Plotting import plot_functions
import sys
import numpy as np
import datetime as dt
from collections import OrderedDict
from typing import Union, List


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


class PlotSpecs:
    """
    Generate and retain the data required for plotting

    """
    def __init__(self, ard: dict, change: dict, segs: List[dict],
                 begin: dt.date=dt.date(year=1982, month=1, day=1),
                 end: dt.date=dt.date(year=2015, month=12, day=31)):
        """

        Args:
            ard: The ARD observations for a given point (ARDData.pixel_ard)
            change: PyCCD results for a given point (CCDReader.results)
            segs: Classification results (SegmentClasses.results)
            begin: Beginning day of PyCCD
            end: Ending day of PyCCD

        """
        self.begin = begin
        self.end = end

        self.ard = self.make_arrays(ard)

        self.dates = self.ard['dates']

        self.results = change

        self.date_mask = self.mask_daterange(dates=self.dates,
                                             start=begin,
                                             stop=end)

        self.dates_in = self.ard['dates'][self.date_mask]

        self.dates_out = self.ard['dates'][~self.date_mask]

        self.ccd_mask = np.array(change['processing_mask'], dtype=np.bool)

        self.qa_mask = np.isin(self.ard['qas'], [66, 68, 322, 324])

        self.fill_mask = np.isin(self.ard['qas'], [n for n in np.unique(self.ard['qas']) if n != 1])

        self.fill_in = self.fill_mask[self.date_mask]
        self.fill_out = self.fill_mask[~self.date_mask]

        # # self.total_mask = np.logical_and(self.ccd_mask, self.fill_in)
        # self.total_mask = np.logical_and(self.qa_mask[date_mask], self.fill_in)

        try:
            # Fix the scaling of the Brightness Temperature
            temp_thermal = np.copy(self.ard['thermals'])
            temp_thermal[self.fill_mask] = temp_thermal[self.fill_mask] * 10 - 27315
            self.ard['thermals'] = np.copy(temp_thermal)

        except KeyError:  # Thermal was not selected for plotting and isn't present
            pass

        # This naming convention was chosen so as to match that which is used in merlin chipmunk
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

        # Calculate indices from observed values

        # Calculate indices from the results' change models
        # The change models are stored by order of model, then
        # band number.  For example, the band values for the first change model are represented by indices 0-5,
        # the second model by indices 6-11, and so on.

        try:
            self.EVI = plot_functions.evi(B=self.ard['blues'].astype(np.float),
                                          NIR=self.ard['nirs'].astype(np.float),
                                          R=self.ard['reds'].astype(np.float))

            self.EVI_ = [plot_functions.evi(B=self.predicted_values[m * len(self.bands)],
                                            NIR=self.predicted_values[m * len(self.bands) + 3],
                                            R=self.predicted_values[m * len(self.bands) + 2])
                         for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.EVI = None

            self.EVI_ = None

        try:
            self.NDVI = plot_functions.ndvi(R=self.ard['reds'].astype(np.float),
                                            NIR=self.ard['nirs'].astype(np.float))

            self.NDVI_ = [plot_functions.ndvi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                              R=self.predicted_values[m * len(self.bands) + 2])
                          for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.NDVI = None

            self.NDVI_ = None

        try:
            self.MSAVI = plot_functions.msavi(R=self.ard['reds'].astype(np.float),
                                              NIR=self.ard['nirs'].astype(np.float))

            self.MSAVI_ = [plot_functions.msavi(R=self.predicted_values[m * len(self.bands) + 2],
                                                NIR=self.predicted_values[m * len(self.bands) + 3])
                           for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.MSAVI = None

            self.MSAVI_ = None

        try:
            self.SAVI = plot_functions.savi(R=self.ard['reds'].astype(np.float),
                                            NIR=self.ard['nirs'].astype(np.float))

            self.SAVI_ = [plot_functions.savi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                              R=self.predicted_values[m * len(self.bands) + 2])
                          for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.SAVI = None

            self.SAVI_ = None

        try:
            self.NDMI = plot_functions.ndmi(NIR=self.ard['nirs'].astype(np.float),
                                            SWIR1=self.ard['swir1s'].astype(np.float))

            self.NDMI_ = [plot_functions.ndmi(NIR=self.predicted_values[m * len(self.bands) + 3],
                                              SWIR1=self.predicted_values[m * len(self.bands) + 4])
                          for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.NDMI = None

            self.NDMI_ = None

        try:
            self.NBR = plot_functions.nbr(NIR=self.ard['nirs'].astype(np.float),
                                          SWIR2=self.ard['swir2s'].astype(np.float))

            self.NBR_ = [plot_functions.nbr(NIR=self.predicted_values[m * len(self.bands) + 3],
                                            SWIR2=self.predicted_values[m * len(self.bands) + 5])
                         for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.NBR = None

            self.NBR_ = None

        try:
            self.NBR2 = plot_functions.nbr2(SWIR1=self.ard['swir1s'].astype(np.float),
                                            SWIR2=self.ard['swir2s'].astype(np.float))

            self.NBR2_ = [plot_functions.nbr2(SWIR1=self.predicted_values[m * len(self.bands) + 4],
                                              SWIR2=self.predicted_values[m * len(self.bands) + 5])
                          for m in range(len(self.results["change_models"]))]

        except KeyError:
            self.NBR2 = None

            self.NBR2_ = None

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

        lookup = OrderedDict([("Blue", ('blues', 0)),
                              ("Green", ('greens', 1)),
                              ("Red", ('reds', 2)),
                              ("NIR", ('nirs', 3)),
                              ("SWIR-1", ('swir1s', 4)),
                              ("SWIR-2", ('swir2s', 5)),
                              ("Thermal", ('thermals', 6))])

        self.band_lookup = [(key, (self.ard[lookup[key][0]],
                                   self.get_predicts(lookup[key][1])))
                             for key in lookup.keys()
                             if lookup[key][0] in self.ard.keys()]

        # Example of how the band_lookup is structured:
        # self.band_lookup = [("Blue", (self.ard['blues'], self.get_predicts(0))),
        #                     ("Green", (self.ard['greens'], self.get_predicts(1))),
        #                     ("Red", (self.ard['reds'], self.get_predicts(2))),
        #                     ("NIR", (self.ard['nirs'], self.get_predicts(3))),
        #                     ("SWIR-1", (self.ard['swir1s'], self.get_predicts(4))),
        #                     ("SWIR-2", (self.ard['swir2s'], self.get_predicts(5))),
        #                     ("Thermal", (self.ard['thermals'], self.get_predicts(6)))]

        self.band_lookup = OrderedDict(self.band_lookup)

        # Combine these two dictionaries
        # self.all_lookup = {**self.band_lookup, **self.index_lookup}
        self.all_lookup = plot_functions.merge_dicts(self.band_lookup, self.index_lookup)

        self.segment_classes = segs

    @staticmethod
    def mask_daterange(dates: np.array, start: dt.date, stop: dt.date) -> np.array:
        """
        Create a mask for values outside of the global BEGIN_DATE and END_DATE

        Args:
            dates: List or array of dates to check against
            start: Begin date stored as a datetime.date object
            stop: End date stored as a datetime.date object

        Returns:
            Array containing the locations of the truth condition

        """
        return np.logical_and(dates >= start.toordinal(), dates < stop.toordinal())

    @staticmethod
    def predicts(days, coef, intercept):
        """
        Calculate change segment curves

        Args:
            days:
            coef:
            intercept:

        Returns:

        """
        return (intercept + coef[0] * days +
                coef[1] * np.cos(days * 1 * 2 * np.pi / 365.25) + coef[2] * np.sin(days * 1 * 2 * np.pi / 365.25) +
                coef[3] * np.cos(days * 2 * 2 * np.pi / 365.25) + coef[4] * np.sin(days * 2 * 2 * np.pi / 365.25) +
                coef[5] * np.cos(days * 3 * 2 * np.pi / 365.25) + coef[6] * np.sin(days * 3 * 2 * np.pi / 365.25))

    def get_predicts(self, num: Union[int, list]) -> list:
        """
        Return the model prediction values in the time series for a particular band or bands

        Args:
            num:

        Returns:
            A list of segment models

        """
        # Check for type int, create list if true
        if isinstance(num, int):
            num = [num]

        return [self.predicted_values[m * len(self.bands) + n] for n in num
                for m in range(len(self.results["change_models"]))]

    @staticmethod
    def make_arrays(in_dict: dict) -> dict:
        """
        Convert a dict of lists into arrays
        Args:
            in_dict:

        Returns:

        """
        for key in in_dict.keys():
            if isinstance(in_dict[key], list):
                in_dict[key] = np.array(in_dict[key])

        return in_dict
