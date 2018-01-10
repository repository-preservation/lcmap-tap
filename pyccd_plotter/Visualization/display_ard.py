"""Read in the image ccd for a selected ARD scene, clip to an extent with the given coordinate at the center
point, clip the ccd values to a lower and upper percentile, and rescale the results to 8-bit unsigned int.
Return a matplotlib figure showing the (n x n x 3) array representing RGB"""

import os
from matplotlib import pyplot as plt
import numpy as np

from osgeo import gdal

from pyccd_plotter.Visualization.rescale import Rescale


def read_data(gui, src_file, ul_rowcol, bands, extent):
    """

    :param src_file:
    :return:
    """
    src = gdal.Open(src_file, gdal.GA_ReadOnly)

    if src is None:
        gui.ui.plainTextEdit_results.appendPlainText("Could not open {}".format(src_file))

    r = src.GetRasterBand(bands[0]).ReadAsArray()
    g = src.GetRasterBand(bands[1]).ReadAsArray()
    b = src.GetRasterBand(bands[2]).ReadAsArray()

    band_count = src.RasterCount

    if band_count == 7:
        qa = src.GetRasterBand(7).ReadAsArray()
    elif band_count == 8:
        qa = src.GetRasterBand(8).ReadAsArray()
    # TODO error handling if raster count is not 7 or 8
    else:
        qa = np.zeros_like(r)
        qa[r == -9999] = 1

    r = r[ul_rowcol.row: ul_rowcol.row + extent, ul_rowcol.column: ul_rowcol.column + extent]
    g = g[ul_rowcol.row: ul_rowcol.row + extent, ul_rowcol.column: ul_rowcol.column + extent]
    b = b[ul_rowcol.row: ul_rowcol.row + extent, ul_rowcol.column: ul_rowcol.column + extent]
    qa = qa[ul_rowcol.row: ul_rowcol.row + extent, ul_rowcol.column: ul_rowcol.column + extent]

    src = None

    return r, g, b, qa


def make_rgb(infile, r, g, b, qa, extent):
    """

    :param infile:
    :param r:
    :param g:
    :param b:
    :param qa:
    :param extent:
    :return:
    """

    rgb = np.zeros((extent, extent, 3), dtype=np.uint8)

    r_rescale = Rescale(src_file=infile, array=r, qa=qa)
    g_rescale = Rescale(src_file=infile, array=g, qa=qa)
    b_rescale = Rescale(src_file=infile, array=b, qa=qa)

    rgb[:,:,0] = b_rescale.rescaled
    rgb[:,:,1] = g_rescale.rescaled
    rgb[:,:,2] = r_rescale.rescaled

    return rgb


def make_figure(gui, infile, ccd, bands=(3,2,1), extent=500):
    """

    :param rgb:
    :return:
    """
    pixel_rowcol = ccd.geo_to_rowcol(affine=ccd.PIXEL_AFFINE, coord=ccd.coord)

    ul_rowcol = ccd.RowColumn(row=pixel_rowcol.row - int(extent / 2.),
                               column = pixel_rowcol.column - int(extent / 2.))

    r, g, b, qa = read_data(gui=gui, src_file=infile, ul_rowcol=ul_rowcol, extent=extent, bands=bands)

    rgb = make_rgb(infile=infile, r=r, g=g, b=b, qa=qa, extent=extent)

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(9,9), dpi=100, facecolor="k", squeeze=False)

    ax[0,0].set_xticks([])
    ax[0,0].set_yticks([])

    ax[0,0].scatter(x=int(extent / 2), y=int(extent / 2), marker='x', s=24, c='white', alpha=0.5)

    ax[0,0].imshow(rgb)

    fig.tight_layout()

    return fig, rgb