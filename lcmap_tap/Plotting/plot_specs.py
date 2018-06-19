"""Prepare data for plotting"""

from lcmap_tap.logger import log
import sys
import numpy as np
import datetime as dt


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


class PlottingData:
    """
    Generate and retain the data required for plotting

    """
    def __init__(self, obs: dict, change: dict,
                 begin: dt.date=dt.date(year=1982, month=1, day=1), end: dt.date=dt.date(2015, month=12, day=31)):
        """

        Args:
            obs: The ARD observations for a given point
            change: PyCCD results for a given point
            begin: Beginning day of PyCCD
            end: Ending day of PyCCD

        """
        date_mask = self.mask_daterange(dates=obs['dates'],
                                        start=begin,
                                        stop=end)

        self.dates_in = obs['dates'][date_mask]

        self.dates_out = obs['dates'][~date_mask]

        self.ccd_mask = np.array(change['processing_mask'], dtype=np.bool)

        self.qa_mask = np.isin(obs['qas'], [66, 68, 322, 324])


    @staticmethod
    def take_array(array: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Return a portion of an input array

        Args:
            array: The original input array
            mask: The array used to mask the input array

        Returns:
            The unmasked portion of the array

        """
        return array[mask]


    @staticmethod
    def mask_daterange(dates, start, stop):
        """
        Create a mask for values outside of the global BEGIN_DATE and END_DATE.
        :param dates:
        :return:
        """
        return np.logical_and(dates >= start.toordinal(), dates < stop.toordinal())
