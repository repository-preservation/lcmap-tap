"""Prepare data for plotting"""

from lcmap_tap.logger import exc_handler, log
from lcmap_tap.Plotting import plot_functions
from lcmap_tap.RetrieveData.retrieve_ccd import CCDReader
from lcmap_tap.RetrieveData.retrieve_classes import SegmentClasses

import sys
import numpy as np
import datetime as dt
from collections import OrderedDict
from typing import Union

sys.excepthook = exc_handler

index_functions = {'ndvi': {'func': plot_functions.ndvi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                   'msavi': {'func': plot_functions.msavi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                   'evi': {'func': plot_functions.evi, 'bands': ('blues', 'reds', 'nirs'), 'inds': (0, 2, 3)},
                   'savi': {'func': plot_functions.savi, 'bands': ('reds', 'nirs'), 'inds': (2, 3)},
                   'ndmi': {'func': plot_functions.ndmi, 'bands': ('nirs', 'swir1s'), 'inds': (3, 4)},
                   'nbr': {'func': plot_functions.nbr, 'bands': ('nirs', 'swir2s'), 'inds': (3, 5)},
                   'nbr2': {'func': plot_functions.nbr2, 'bands': ('swir1s', 'swir2s'), 'inds': (4, 5)}
                   }


class PlotSpecs:
    """
    Generate and retain the data required for plotting

    """
    bands = ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal')

    def __init__(self, ard: dict, change: CCDReader, segs: SegmentClasses, items: list,
                 begin: dt.date = dt.date(year=1982, month=1, day=1),
                 end: dt.date = dt.date(year=2015, month=12, day=31)):
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

        self.items = items

        self.ard = self.make_arrays(ard)

        self.dates = self.ard['dates']

        try:
            self.results = change.results

            self.ccd_mask = np.array(self.results['processing_mask'], dtype=np.bool)

        except AttributeError:
            self.results = None

            self.ccd_mask = []

        try:
            self.segment_classes = segs.results

        except AttributeError:
            self.segment_classes = None

        self.date_mask = self.mask_daterange(dates=self.dates,
                                             start=begin,
                                             stop=end)

        self.dates_in = self.ard['dates'][self.date_mask]

        self.dates_out = self.ard['dates'][~self.date_mask]

        self.qa_mask = np.isin(self.ard['qas'], [66, 68, 322, 324])

        self.fill_mask = np.isin(self.ard['qas'], [n for n in np.unique(self.ard['qas']) if n != 1])

        self.fill_in = self.fill_mask[self.date_mask]
        self.fill_out = self.fill_mask[~self.date_mask]

        # # self.total_mask = np.logical_and(self.ccd_mask, self.fill_in)
        # self.total_mask = np.logical_and(self.qa_mask[date_mask], self.fill_in)

        # Check for presence of thermals, rescale if present
        if 'thermals' in self.ard.keys():
            self.rescale_thermal()

        self.index_to_observations()

        if self.results is not None:
            self.predicted_values, \
            self.prediction_dates, \
            self.break_dates, \
            self.start_dates, \
            self.end_dates = self.get_modelled_specs(self.results)

        else:
            self.predicted_values = []
            self.prediction_dates = []
            self.break_dates = []
            self.start_dates = []
            self.end_dates = []

        self.index_lookup, self.band_lookup, self.all_lookup = self.get_lookups(results=self.results,
                                                                                predicted_values=self.predicted_values)

    def get_modelled_specs(self, results):
        band_info = {b: {'coefs': [], 'inter': [], 'pred': []} for b in self.bands}

        predicted_values = []
        prediction_dates = []
        break_dates = []
        start_dates = []
        end_dates = []

        for num, result in enumerate(results['change_models']):
            days = np.arange(result['start_day'], result['end_day'] + 1)

            break_dates.append(result['break_day'])

            start_dates.append(result['start_day'])

            end_dates.append(result['end_day'])

            for b in self.bands:
                band_info[b]['inter'] = result[b]['intercept']

                band_info[b]['coefs'] = result[b]['coefficients']

                band_info[b]['pred'] = self.predicts(days, result[b]['coefficients'], result[b]['intercept'])

                prediction_dates.append(days)

                predicted_values.append(band_info[b]['pred'])

        return predicted_values, prediction_dates, break_dates, start_dates, end_dates

    def get_lookups(self, results, predicted_values):
        # Calculate indices from observed values

        # Calculate indices from the results' change models
        # The change models are stored by order of model, then
        # band number.  For example, the band values for the first change model are represented by indices 0-5,
        # the second model by indices 6-11, and so on.
        index_modeled = self.get_modeled_index(ard=self.ard, results=results, predicted_values=predicted_values)

        index_lookup = OrderedDict([('NDVI', ('ndvi', 'ndvi-modeled')),
                                    ('MSAVI', ('msavi', 'msavi-modeled')),
                                    ('EVI', ('evi', 'evi-modeled')),
                                    ('SAVI', ('savi', 'savi-modeled')),
                                    ('NDMI', ('ndmi', 'ndmi-modeled')),
                                    ('NBR', ('nbr', 'nbr-modeled')),
                                    ('NBR-2', ('nbr2', 'nbr2-modeled'))])

        index_lookup = [(key, (self.ard[index_lookup[key][0]],
                               index_modeled[index_lookup[key][1]]))
                        for key in index_lookup.keys()
                        if index_lookup[key][0] in self.ard.keys()]

        index_lookup = OrderedDict(index_lookup)

        lookup = OrderedDict([("Blue", ('blues', 0)),
                              ("Green", ('greens', 1)),
                              ("Red", ('reds', 2)),
                              ("NIR", ('nirs', 3)),
                              ("SWIR-1", ('swir1s', 4)),
                              ("SWIR-2", ('swir2s', 5)),
                              ("Thermal", ('thermals', 6))])

        band_lookup = [(key, (self.ard[lookup[key][0]],
                              self.get_predicts(num=lookup[key][1], bands=self.bands,
                                                predicted_values=predicted_values, results=results)))
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

        band_lookup = OrderedDict(band_lookup)

        # Combine these two dictionaries
        # self.all_lookup = {**self.band_lookup, **self.index_lookup}
        all_lookup = plot_functions.merge_dicts(band_lookup, index_lookup)

        return index_lookup, band_lookup, all_lookup

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

    @staticmethod
    def get_predicts(num: Union[int, list], bands: tuple, predicted_values: list, results: dict) -> list:
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

        try:
            _predicts = [predicted_values[m * len(bands) + n] for n in num
                         for m in range(len(results["change_models"]))]

        except (IndexError, TypeError) as e:
            log.warning('Exception %s' % e)

            _predicts = []

        return _predicts

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

    def rescale_thermal(self):
        """
        Fix the scaling of the Brightness Temperature, if it was selected for plotting

        """
        temp_thermal = np.copy(self.ard['thermals'])

        temp_thermal[self.fill_mask] = temp_thermal[self.fill_mask] * 10 - 27315

        self.ard['thermals'] = np.copy(temp_thermal)

        return None

    def index_to_observations(self):
        """
        Add index calculated observations to the timeseries pixel rod

        Returns:

        """
        indices = ['NDVI', 'MSAVI', 'EVI', 'SAVI', 'NDMI', 'NBR', 'NBR-2']

        selected_indices = [i for i in indices if i in self.items or 'All Indices' in self.items]

        for i in selected_indices:
            key = i.lower().replace('-', '')

            call = index_functions[key]['func']

            args = tuple([self.ard[band] for band in index_functions[key]['bands']])

            self.ard[key] = call(*args)

        return None

    @staticmethod
    def get_modeled_index(ard, results, predicted_values):
        """
        Calculate the model-predicted index curves

        Returns:

        """
        bands = ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal')
        indices = ('ndvi', 'msavi', 'evi', 'savi', 'ndmi', 'nbr', 'nbr2')

        modeled = dict()

        for key in ard.keys():
            if key in indices:
                new_key = f'{key}-modeled'

                modeled[new_key] = list()

                call = index_functions[key]['func']

                inds = index_functions[key]['inds']

                try:
                    for m in range(len(results['change_models'])):
                        args = tuple([predicted_values[m * len(bands) + ind] for ind in inds])

                        modeled[new_key].append(call(*args))

                except AttributeError:
                    modeled[new_key].append([])

        return modeled
