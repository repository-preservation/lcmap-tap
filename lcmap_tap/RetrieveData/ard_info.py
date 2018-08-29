"""Sensor-dependent band specifications and other information related to the ARD stack.  Used to construct
useful data structures that house sceneIDs mapped to tar files and the bands contained within"""

import os
import sys
import re
from lcmap_tap.logger import exc_handler
from lcmap_tap.RetrieveData import band_specs

sys.excepthook = exc_handler


class ARDInfo:
    def __init__(self, root: str, h: str, v: str):
        """

        Args:
            root: The full path to the tile
            h: The tile horizontal designator
            v: The tile vertical designator
        """

        self.root = root

        self.h = str(h)

        self.v = str(v)

        self.tile_name = os.path.basename(self.root)

        self.tarfiles = self.get_filelist()

        self.tarfiles.sort()

        self.scene_ids = self.get_sceneid_list()

        self.scene_ids.sort()

        self.num_scenes = len(self.scene_ids)

        self.lookup = self.tarfile_lookup()

        self.vsipaths = self.get_vsipath_list()

    def get_subdir(self) -> str:
        """
        Return the full path to the tile sub-directory

        Returns:
            The string containing the full path to a tile's sub-directory

        """
        if len(self.h) == 1:
            self.h = "0" + self.h

        if len(self.v) == 1:
            self.v = "0" + self.v

        return self.root + os.sep + "h{}v{}".format(self.h, self.v)

    def get_filelist(self, ext: str = ".tar") -> list:
        """
        Return a list of all files with the given extension in the self.root directory

        Args:
            ext: A file extension to look for, the default is ".tar"

        Returns:
            A list containing all files in self.root with the given extension

        """
        return [os.path.join(self.root, f) for f in os.listdir(self.root) if f.endswith("_SR{}".format(ext))]

    @staticmethod
    def get_sceneid(in_file: str) -> str:
        """
        Get the scene ID for the input tarfile

        Args:
            in_file: Full path to the input tarfile

        Returns:
            The scene ID taken from the input file name that matches a given regular expression

        """
        return re.search(r"\w{2}\d{2}_\w{2}_\d{6}_\d{8}", os.path.basename(in_file)).group()

    def get_sceneid_list(self):
        """
        Return a list containing the unique scene IDs in the tile sub-folder

        Returns:
            A list of the scene IDs based on the list of input tarfiles

        """
        return [self.get_sceneid(f) for f in self.tarfiles]

    def tarfile_lookup(self, prods: tuple = ("SR", "BT")):
        """
        Return a dictionary that maps each scene ID to the full path of the product tarfiles
        specified by the tuple 'prod'.  Default products are 'SR' and 'BT'.

        Args:
            prods: The target products to point to

        Returns:
            tarz: The dictionary whose keys are scene ID's mapped to the corresponding scene tarballs
            for specific products, which are in turn mapped to strings containing the full path of the products

        """
        tarz = dict()

        for scene, tar in zip(self.scene_ids, self.tarfiles):

            tarz[scene] = dict()

            for prod in prods:
                tarz[scene][prod] = dict()

                tarz[scene][prod] = os.path.split(tar)[0] + os.sep + os.path.basename(tar)[:40] + "_" + prod + ".tar"

        return tarz

    @staticmethod
    def get_sensor(scene_id: str) -> str:
        """
        Determine sensor from the input filename

        Args:
            scene_id: The scene ID

        Returns:
            The string that matches the regular expression used to find the sensor name

        """
        return re.search(r"\w{2}\d{2}", scene_id).group()

    @staticmethod
    def get_bands(sensor: str) -> dict:
        """
        Return a dict of sensor-specific band designations for retrieving the appropriate .tif file; taken from the
        out-scope dict 'band_specs'

        Args:
            sensor: The sensor name, used as a key in the band_specs dictionary

        Returns:
            A dictionary with the sensor-specific strings used to point to appropriate bands within the tarball

        """
        return band_specs[sensor]

    @staticmethod
    def get_vsipath(in_tar: str, band: str) -> str:
        """
        Return the virtual file path for the current tarball and band which is used by GDAL to open as a virtual
        file path

        Args:
            in_tar: Full path to the scene's tarfile
            band: The sensor specific band

        Returns:
            The full path to the band stored in the tarfile

        """
        return os.path.join("/vsitar/{}".format(in_tar), "{}_{}.tif".format(os.path.basename(in_tar)[:40], band))

    def get_vsipath_list(self) -> dict:
        """
        Return a dict containing all of the vsi paths so they can be accessed as needed

        Returns:
            A dictionary whose key-value pairs are scene IDs mapped to the corresponding .tif files stored in those
            scenes' tarfiles

        """
        paths = dict()

        for scene in self.scene_ids:
            prods = self.get_bands(self.get_sensor(scene))

            paths[scene] = list()

            for prod in prods:
                tarfile = self.lookup[scene][prod]

                for band in prods[prod]:
                    paths[scene].append(self.get_vsipath(tarfile, prods[prod][band]))

        return paths
