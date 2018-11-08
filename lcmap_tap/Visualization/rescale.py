"""Clip and rescale a passed numpy array"""

import sys
import numpy as np
from lcmap_tap.logger import exc_handler

sys.excepthook = exc_handler


class Rescale:
    def __init__(self, array, qa, lower_percentile=1, upper_percentile=99):
        self.lower_percentile = lower_percentile

        self.upper_percentile = upper_percentile

        self.array = array

        self.qa = qa

        self.mask_clear, self.mask_fill = self.get_masks(self.qa)

        if not np.any(self.mask_clear is True):
            self.limits = self.get_percentiles(self.array, self.mask_fill,
                                               self.lower_percentile, self.upper_percentile)

        else:
            self.limits = self.get_percentiles(self.array, self.mask_clear,
                                               self.lower_percentile, self.upper_percentile)

        self.clipped = self.clip_array(self.array, self.limits)

        self.rescaled = self.rescale_array(self.clipped, self.mask_fill)

    @staticmethod
    def get_masks(qa):
        """
        Create separate masks for the clear observations and fill values

        Args:
            qa (np.ndarray): The input PIXELQA values

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                [0] - The clear observation mask
                [1] - Fill mask

        """
        return (np.isin(element=qa, test_elements=[66, 68, 322, 324]),  # mask_clear
                ~np.isin(element=qa, test_elements=[1]))  # mask_fill

    @staticmethod
    def get_percentiles(data, truth_mask, lower_percentile, upper_percentile):
        """
        Return the upper and lower percentiles for the input data and use a mask to ignore specific values

        Args:
            data (np.ndarray): The original data array
            truth_mask (np.ndarray): A bytes array, 1 corresponds to True
            lower_percentile
            upper_percentile

        Returns:
            List[int, int]

        """
        return [np.percentile(data[truth_mask], lower_percentile),
                np.percentile(data[truth_mask], upper_percentile)]

    @staticmethod
    def clip_array(data, limits):
        """
        Clip the data values to an upper and lower limit

        Args:
            data (np.ndarray): The input data array
            limits (List[float, float]: The upper and lower limits to use

        Returns:
            np.ndarray

        """
        clipped = np.zeros_like(data)

        np.clip(a=data, a_min=limits[0], a_max=limits[1], out=clipped)

        return clipped

    @staticmethod
    def rescale_array(data, fill_mask, out_min=1.0, out_max=255.0):
        """
        Take an input array and rescale it to a range of values fitting in 8 bits by default

        Args:
            data (np.ndarray): The input data array
            fill_mask (np.ndarray): The fill-value mask
            out_min (float): Minimum bounding value, default is 1.0
            out_max (float): Maximum bounding value, default is 255.0

        Returns:
            np.ndarray

        """
        out_data = np.zeros_like(data, dtype=np.int32)

        out_data[fill_mask] = (
                (data[fill_mask] - np.min(data[fill_mask])) * (out_max - out_min)
                /
                (np.max(data[fill_mask]) - np.min(data[fill_mask]))
        )

        return out_data
