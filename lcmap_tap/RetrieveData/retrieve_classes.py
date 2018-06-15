"""Find the class segments for the current time series"""

from lcmap_tap.logger import log
from lcmap_tap.RetrieveData.retrieve_geo import GeoCoordinate, RowColumn
from lcmap_tap.RetrieveData.retrieve_ccd import CCDReader
import os
import sys
import pickle
import numpy as np
from typing import List


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


class SegmentClasses:
    """Find and retain the classification results for the current time series"""

    def __init__(self, chip_coord: GeoCoordinate, class_dir: str, rc: RowColumn, tile: str):
        """

        Args:
            chip_coord: The upper left coordinate of the chip in projected meters
            class_dir: Absolute path to the directory containing classification results stored as pickle files
            rc: Row and column of the pixel within the chip array
            tile: String-formatted H-V tile name

        """
        self.results = self.extract_results(class_file=CCDReader.find_file(
            file_ls=[os.path.join(class_dir, f) for f in os.listdir(class_dir)],
            string="{tile}_{x}_{y}_class.p".format(tile=tile,
                                                   x=chip_coord.x,
                                                   y=chip_coord.y)),
            rc=rc)

    @staticmethod
    def extract_results(class_file: str, rc: RowColumn) -> List[dict]:
        """
        Load the data from the pickle file, slice out the location-specific data

        Args:
            class_file: Absolute path to the input class file
            rc: Row and column of the pixel within the chip array

        Returns:
            A list containing the classification results for the time series at a given row-column location

        """
        results = np.reshape(pickle.load(open(class_file, "rb")), (100, 100))

        return results[rc.row, rc.column]
