"""Retrieve PyCCD attributes and results for the pixel coordinates"""

from lcmap_tap.RetrieveData import GeoCoordinate
from lcmap_tap.logger import log, exc_handler
import os
import sys
import json

sys.excepthook = exc_handler


class CCDReader:
    """
    Find and read the JSON containing PyCCD output for the target pixel coordinates
    """

    def __init__(self, tile: str, chip_coord: GeoCoordinate, pixel_coord: GeoCoordinate, json_dir: str):
        """

        Args:
            tile: The string-formatted H-V tile name
            chip_coord: The upper left coordinate of the chip in projected meters
            pixel_coord: The upper left coordinate of the pixel in projected meters
            json_dir: Absolute path to tile-specific PyCCD results stored in JSON files

        Returns:

        """
        log.debug(f'SEARCHING - dir - {json_dir}')

        log.debug(f'SEARCHING - file - {tile}_{chip_coord.x}_{chip_coord.y}.json')

        try:
            self.json_file = self.find_file(file_ls=[os.path.join(json_dir, f) for f in os.listdir(json_dir)],
                                            string="{tile}_{x}_{y}.json".format(tile=tile,
                                                                                x=chip_coord.x,
                                                                                y=chip_coord.y))
        except Exception:
            log.exception("ERROR - retrieving pyccd results failed")

            self.results = [{}]

        if self.json_file is not None:
            self.results = self.check_dates(
                self.extract_jsoncurve(pixel_info=self.pixel_ccd_info(results_chip=self.json_file,
                                                                      coord=pixel_coord)))

        else:
            log.warning("No PyCCD results exist for tile %s" % tile)

            self.results = [{}]

    @staticmethod
    def find_file(file_ls, string) -> str:
        """
        Find the matching file from a list of files

        Args:
            file_ls: List of files to search
            string: The identifying feature of a filename to search for

        Returns:
            The absolute path to the matching file

        """
        gen = filter(lambda x: string.casefold() in x.casefold(), file_ls)

        return next(gen, None)

    @staticmethod
    def chip_results(results_chip: str) -> dict:
        """
        Method for loading and returning the contents of a JSON file that contains a chip of change results.

        Args:
            results_chip: The full path to a JSON file

        Returns:
            Information from a JSON file stored in a dict structure

        """
        return json.load(open(results_chip, 'r'))

    @staticmethod
    def pixel_ccd_info(results_chip: str, coord: GeoCoordinate) -> dict:
        """
        Find the CCD output for a specific pixel from within the chip by matching the pixel coordinates

        Args:
            results_chip: Absolute path to the input JSON file
            coord: Upper left coordinate of the target pixel in projected meters

        Returns:
            All of the information stored in the target JSON file for the specific pixel coordinate

        """
        results = json.load(open(results_chip, "r"))

        gen = filter(lambda x: coord.x == x["x"] and coord.y == x["y"], results)

        return next(gen, None)

    @staticmethod
    def extract_jsoncurve(pixel_info: dict) -> dict:
        """
        Load the PyCCD results for the target pixel

        Args:
            pixel_info:

        Returns:
            The data structure containing the PyCCD results

        """
        return json.loads(pixel_info["result"])

    @staticmethod
    def check_dates(results: dict) -> dict:
        """
        In cases where the entire time series does not contain a break day, simply make it be equal to the model's
        end day.

        """
        for ind, model in enumerate(results['change_models']):
            if model['break_day'] < 1:
                model['break_day'] = model['end_day']

        return results
