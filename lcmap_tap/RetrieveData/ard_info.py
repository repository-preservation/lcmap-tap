"""Sensor-dependent band specifications and other information related to the ARD stack"""

import os
import re
import datetime


band_specs = {
    "LC08": {
        "SR": {"1": "SRB2",
               "2": "SRB3",
               "3": "SRB4",
               "4": "SRB5",
               "5": "SRB6",
               "6": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"10": "BTB10",
               "11": "BTB11"}
    },
    "LE07": {
        "SR": {"1": "SRB1",
               "2": "SRB2",
               "3": "SRB3",
               "4": "SRB4",
               "5": "SRB5",
               "7": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"6": "BTB6"}
    },
    "LT05": {
        "SR": {"1": "SRB1",
               "2": "SRB2",
               "3": "SRB3",
               "4": "SRB4",
               "5": "SRB5",
               "7": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"6": "BTB6"}
    },
    "LT04": {
        "SR": {"1": "SRB1",
               "2": "SRB2",
               "3": "SRB3",
               "4": "SRB4",
               "5": "SRB5",
               "7": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"6": "BTB6"}
    },
}


class ARDInfo:
    def __init__(self, root: str, h: str, v: str):
        """
        :param h: H designator
        :param v: V designator
        :param root: The full path to the input root directory (Directory containing all tile sub-folders)
        """
        self.root = root

        self.h = str(h)

        self.v = str(v)

        self.subdir = self.get_subdir()

        self.tile_name = os.path.basename(self.subdir)

        self.tarfiles = self.get_filelist()

        self.tarfiles.sort()

        self.scene_ids = self.get_sceneid_list()

        self.scene_ids.sort()

        self.num_scenes = len(self.scene_ids)

        self.lookup = self.tarfile_lookup()

        self.vsipaths = self.get_vsipath_list()

    def get_subdir(self) -> str:
        """
        Return the full path to the tile subdirectory
        :return:
        """
        if len(self.h) == 1:
            self.h = "0" + self.h

        if len(self.v) == 1:
            self.v = "0" + self.v

        return self.root + os.sep + "h{}v{}".format(self.h, self.v)

    def get_filelist(self, ext: str = ".tar") -> list:
        """
        Return a list of all files with the given extension in root indir
        :param ext: File extension, ".tar" by default
        :return:
        """
        return [os.path.join(self.subdir, f) for f in os.listdir(self.subdir) if f.endswith("_SR{}".format(ext))]

    @staticmethod
    def get_sceneid(in_file: str) -> str:
        """
        Get the scene ID for the input file
        :param in_file: Full path to the tar file
        :return:
        """
        return re.search(r"\w{2}\d{2}_\w{2}_\d{6}_\d{8}", os.path.basename(in_file)).group()

    def get_sceneid_list(self):
        """
        Return a list of all the unique scene IDs in the tile sub-folder
        :return:
        """
        return [self.get_sceneid(f) for f in self.tarfiles]

    def tarfile_lookup(self, prods: tuple=("SR", "BT")):
        """
        Return a dict of scene ID: tarfiles
        :return:
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
        :param scene_id: The scene identifier
        :return:
        """
        return re.search(r"\w{2}\d{2}", scene_id).group()

    @staticmethod
    def get_bands(sensor: str) -> dict:
        """
        Return a dict of sensor-specific band designations for retrieving the appropriate .tif file
        :param sensor:
        :return:
        """
        return band_specs[sensor]

    @staticmethod
    def get_vsipath(in_tar: str, band: str) -> str:
        """
        Return the virtual file paths for the current tarball
        :param in_tar: The full path to the scene tarball
        :param band: The sensor specific bands
        :return:
        """
        return "/vsitar/{}".format(in_tar) + os.sep + os.path.basename(in_tar)[:40] + "_{}.tif".format(band)

    def get_vsipath_list(self) -> dict:
        """
        Return a dict containing all of the vsi paths, ready to open when needed
        :return:
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
