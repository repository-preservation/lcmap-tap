
import sys
import numpy as np
from osgeo import gdal

from lcmap_tap.logger import exc_handler
from lcmap_tap.Visualization.tc_bgw_coeffs import coeffs

sys.excepthook = exc_handler


def do_calc(vals: dict, bands: list):
    """
    Perform TC calculation

    Args:
        vals: A dict mapping coefficient to band for a given sensor
        bands: List of numpy arrays containing the ARD band reflectance data

    Returns:

    """
    mask = np.zeros_like(bands[-1], dtype=np.bool)

    mask[bands[-1] != 1] = True

    out_array = np.zeros_like(bands[-1], dtype=np.float)

    out_array[mask] = vals["1"] * bands[0][mask] * 0.0001 + vals["2"] * bands[1][mask] * 0.0001 + \
                      vals["3"] * bands[2][mask] * 0.0001 + vals["4"] * bands[3][mask] * 0.0001 + \
                      vals["5"] * bands[4][mask] * 0.0001 + vals["6"] * bands[5][mask] * 0.0001

    # out_array[mask] = vals["1"] * bands[0][mask] + vals["2"] * bands[1][mask] + \
    #                   vals["3"] * bands[2][mask] + vals["4"] * bands[3][mask] + \
    #                   vals["5"] * bands[4][mask] + vals["6"] * bands[5][mask]

    out_array = out_array * 10000.

    return out_array


def get_tc_bands(sensor, files):
    """

    Args:
        sensor:

    Returns:

    """
    bands = list()

    for f in files:
        bands.append(gdal.Open(f, gdal.GA_ReadOnly).ReadAsArray())

    bright_coeffs = coeffs["brightness"][sensor]

    green_coeffs = coeffs["greenness"][sensor]

    wet_coeffs = coeffs["wetness"][sensor]

    bright_img = do_calc(bright_coeffs, bands)

    green_img = do_calc(green_coeffs, bands)

    wet_img = do_calc(wet_coeffs, bands)

    return bright_img, green_img, wet_img
