"""Clip and rescale a passed numpy array"""


import os
import numpy as np


class Rescale:
    def __init__(self, src_file, array, qa, lower_percentile=5, upper_percentile=95):
        self.lower_percentile = lower_percentile

        self.upper_percentile = upper_percentile

        self.src_file = src_file

        self.array = array

        self.qa = qa

        self.get_masks()

        if not np.any(self.mask_clear == True):
            self.limits = self.get_percentiles(qa=self.mask_fill)

        else:
            self.limits = self.get_percentiles(qa=self.mask_clear)

        self.clipped = self.clip_array()

        self.rescaled = self.rescale_array()

    def get_masks(self):
        """

        :param infile:
        :param qa:
        :return:
        """
        basename = os.path.basename(self.src_file)

        sensor = basename[0] + basename[3]

        self.mask_clear = np.zeros_like(self.qa, dtype=np.bool)

        self.mask_fill = np.copy(self.mask_clear)

        if sensor == "L8":
            # PIXELQA 322, 324 are clear land/water obs. with low confidence cloud and low confidence cirrus
            self.mask_clear[self.qa == 322] = True
            self.mask_clear[self.qa == 324] = True

        else:
            # PIXELQA 66, 68 are clear land/water obs. with low confidence cloud
            self.mask_clear[self.qa == 66] = True
            self.mask_clear[self.qa == 68] = True
            # print(mask_clear)

        self.mask_fill[self.qa != 1] = True

        return None

    def get_percentiles(self, qa):
        """

        :return:
        """
        return [np.percentile(self.array[qa], self.lower_percentile),
                np.percentile(self.array[qa], self.upper_percentile)]

    def clip_array(self):
        """

        :param array:
        :param array:
        :param limits:
        :return:
        """

        clipped = np.zeros_like(self.array)

        np.clip(a=self.array, a_min=self.limits[0], a_max=self.limits[1], out=clipped)

        return clipped

    def rescale_array(self, out_min=1.0, out_max=255.0):
        """

        :param array:
        :param qa:
        :param out_min:
        :param out_max:
        :return:
        """
        out_data = np.zeros_like(self.clipped, dtype=np.int32)

        out_data[self.mask_fill] = ((self.clipped[self.mask_fill] - np.min(self.clipped[self.mask_fill])) *
                                    (out_max - out_min) / (np.max(self.clipped[self.mask_fill]) -
                                                           np.min(self.clipped[self.mask_fill]))
                                    )

        return out_data
