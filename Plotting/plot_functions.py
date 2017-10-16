
"""Define various functions to make life easier (ideally)"""
import numpy as np

def test_for_zero(num):
    """
    Test input for 0 values
    :param num: <numpy.ndarray>
    :return mask: <numpy.ndarray> A boolean-type mask, 1 for valid, 0 for ignore
    """
    mask = np.zeros_like(num, dtype=np.bool)

    mask[num != 0.0] = True

    return mask


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
    sqrt = test_for_negative((2.0 * NIR + 1.0) ** 2.0 - 8.0 * (NIR - R))

    return (2.0 * NIR + 1.0 - (sqrt ** 0.5)) / 2.0


def ndvi(R, NIR):
    """
    Normalized Difference Vegetation Index
    (NIR - R) / (NIR + R)
    :param R:
    :param NIR:
    :return:
    """
    mask = test_for_zero(NIR + R)

    result = np.zeros_like(R, dtype=np.float32)

    result[mask] = (NIR[mask] - R[mask]) / (NIR[mask] + R[mask])

    return result


def evi(B, R, NIR, G=2.5, L=1.0, C1=6, C2=7.5):
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
    mask = test_for_zero(NIR + C1 * R - C2 * B + L)
    result = np.zeros_like(R, dtype=np.float32)

    result[mask] = G * ((NIR[mask] - R[mask]) / (NIR[mask] + C1 * R[mask] - C2 * B[mask] + L))

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
    mask = test_for_zero(NIR + R + L)
    result = np.zeros_like(R, dtype=np.float32)

    result[mask] = ((NIR[mask] - R[mask]) / (NIR[mask] +R[mask] + L)) * (1 + L)

    return result


def ndmi(NIR, SWIR1):
    """
    Normalized Difference Moisture Index
    (NIR - SWIR1) / (NIR + SWIR1)
    :param NIR:
    :param SWIR1:
    :return:
    """
    mask = test_for_zero(NIR + SWIR1)
    result = np.zeros_like(NIR, dtype=np.float32)

    result[mask] = (NIR[mask] - SWIR1[mask]) / (NIR[mask] + SWIR1[mask])

    return result


def nbr(NIR, SWIR2):
    """
    Normalized Burn Ratio
    (NIR - SWIR2) / (NIR + SWIR2)
    :param NIR:
    :param SWIR2:
    :return:
    """
    mask = test_for_zero(NIR + SWIR2)
    result = np.zeros_like(NIR, dtype=np.float32)

    result[mask] = (NIR[mask] - SWIR2[mask]) / (NIR[mask] + SWIR2[mask])

    return result


def nbr2(SWIR1, SWIR2):
    """
    Normalized Burn Ratio 2
    (SWIR1 - SWIR2) / (SWIR1 + SWIR2)
    :param SWIR1:
    :param SWIR2:
    :return:
    """
    mask = test_for_zero(SWIR1 + SWIR2)
    result = np.zeros_like(SWIR1, dtype=np.float32)

    result[mask] = (SWIR1[mask] - SWIR2[mask]) / (SWIR1[mask] + SWIR2[mask])

    return result
