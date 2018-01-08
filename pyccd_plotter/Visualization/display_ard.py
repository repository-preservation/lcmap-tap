"""Open the ARD image selected in the GUI and display it in a new QWidget using matplotlib"""

import os
from matplotlib import pyplot as plt
import numpy as np

from osgeo import gdal

from pyccd_plotter.Visualization.rescale import Rescale

def make_rgb(infile, gui, bands):
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

def make_figure(infile, gui, bands=(3,2,1)):
    """

    :param rgb:
    :return:
    """
    rgb = make_rgb(infile, gui, bands)

    # fig, ax = plt.subplots(figsize=(18,18), dpi=200, squeeze=False)
    fig = plt.figure(figsize=(18,18), dpi=200)

    ax = plt.Axes(fig, [0.,0.,1.,1.])

    ax.set_axis_off()

    fig.add_axes(ax)

    ax.imshow(rgb)

    return fig