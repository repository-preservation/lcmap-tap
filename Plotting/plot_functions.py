
"""Define various functions to make life easier (ideally)"""
import numpy as np
from collections import OrderedDict


def merge_dicts(*dict_args):
    """
    Make shallow copies and merge dicts into a new dict
    Backwards compatible method of doing this compared to the {**dict1, **dict2} available >= python 3.5
    :param dict_args:
    :return:
    """
    result = OrderedDict()
    for dictionary in dict_args:
        result.update(dictionary)

    return result

def test_for_zero(num):
    """
    Test input for 0 values
    :param num: <numpy.ndarray>
    :return mask: <numpy.ndarray> A boolean-type mask, 1 for valid, 0 for ignore
    """
    num[num == 0.0] = 0.001

    return num


def test_for_negative(num):
    """
    Test input for negative values
    :param num: <numpy.ndarray> The results to test
    :return num: <numpy.ndarray> Negative values replaced with value 0.0
    """
    num[num < 0.0] = 0.0

    return num


def msavi(R, NIR):
    """
    Modified Soil Adjusted Vegetation Index
    (2.0 * NIR + 1.0 - ((2.0 * NIR + 1.0) ** 2.0 - 8.0 * (NIR - R)) ** 0.5) / 2.0
    :param R:
    :param NIR:
    :return:
    """
    sqrt = (2.0 * (NIR * 0.0001) + 1.0) ** 2.0 - 8.0 * ((NIR * 0.0001) - (R * 0.0001))

    sqrt = test_for_negative(sqrt)

    result = (2.0 * (NIR * 0.0001) + 1.0 - (sqrt ** 0.5)) / 2.0

    return result


def ndvi(R, NIR):
    """
    Normalized Difference Vegetation Index
    (NIR - R) / (NIR + R)
    :param R:
    :param NIR:
    :return:
    """
    den = NIR + R

    den = test_for_zero(den)

    result = (NIR - R) / den

    return result


def evi(B, R, NIR, G=2.5, L=1.0, C1=6.0, C2=7.5):
    """
    Enhanced Vegetation Index
    G * ((NIR - R) / (NIR + C1 * R - C2 * B + L))
    :param B:
    :param R:
    :param NIR:
    :param G: <float> Constant
    :param L: <float> Constant
    :param C1: <float> Constant
    :param C2: <float> Constant
    :return:
    """
    den = (NIR * 0.0001) + C1 * (R * 0.0001) - C2 * (B * 0.0001) + L

    den = test_for_zero(den)

    result = G * (((NIR * 0.0001) - (R * 0.0001)) / den)

    return result


def savi(R, NIR, L=0.5):
    """
    Soil Adjusted Vegetation Index
    ((NIR - R) / (NIR + R + L)) * (1 + L)
    :param R:
    :param NIR:
    :param L:
    :return:
    """
    den = (NIR * 0.0001) + (R * 0.0001) + L

    den = test_for_zero(den)

    result = (((NIR * 0.0001) - (R * 0.0001)) / den) * (1 + L)

    return result


def ndmi(NIR, SWIR1):
    """
    Normalized Difference Moisture Index
    (NIR - SWIR1) / (NIR + SWIR1)
    :param NIR:
    :param SWIR1:
    :return:
    """
    den = NIR + SWIR1

    den = test_for_zero(den)

    result = (NIR - SWIR1) / den

    return result


def nbr(NIR, SWIR2):
    """
    Normalized Burn Ratio
    (NIR - SWIR2) / (NIR + SWIR2)
    :param NIR:
    :param SWIR2:
    :return:
    """
    den = NIR + SWIR2

    den = test_for_zero(den)

    result = (NIR - SWIR2) / den

    return result


def nbr2(SWIR1, SWIR2):
    """
    Normalized Burn Ratio 2
    (SWIR1 - SWIR2) / (SWIR1 + SWIR2)
    :param SWIR1:
    :param SWIR2:
    :return:
    """
    den = SWIR1 + SWIR2

    den = test_for_zero(den)

    result = (SWIR1 - SWIR2) / den

    return result
