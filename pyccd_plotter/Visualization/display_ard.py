"""Open the ARD image selected in the GUI and display it in a new QWidget using matplotlib"""

import os
from matplotlib import pyplot as plt
import numpy as np

from osgeo import gdal

from pyccd_plotter.Visualization.rescale import Rescale

def make_rgb(infile, bands, gui):
    """

    :param infile:
    :return:
    """

    src = gdal.Open(infile, gdal.GA_ReadOnly)

    if src is None:
        gui.ui.plainTextEdit_results.appendPlainText("Could not open {}".format(infile))

    R = src.GetRasterBand(bands[0]).ReadAsArray()
    G = src.GetRasterBand(bands[1]).ReadAsArray()
    B = src.GetRasterBand(bands[2]).ReadAsArray()

    QA = src.GetRasterBand(7).ReadAsArray()

    RGB = np.zeros((5000, 5000, 3), dtype=np.uint8)

    R_rescale = Rescale(src_file=infile, array=R, qa=QA)
    G_rescale = Rescale(src_file=infile, array=G, qa=QA)
    B_rescale = Rescale(src_file=infile, array=B, qa=QA)

    RGB[:,:,0] = B_rescale.rescaled
    RGB[:,:,1] = G_rescale.rescaled
    RGB[:,:,2] = R_rescale.rescaled

    return RGB

