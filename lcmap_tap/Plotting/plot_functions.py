"""Define various functions to make life easier (ideally)"""

import numpy as np
from numpy import ndarray
from collections import OrderedDict


def merge_dicts(*dict_args) -> OrderedDict:
    """
    Make shallow copies and merge dicts into a new dict.  This is a backwards compatible method of doing this compared
    to the {**dict1, **dict2} available >= python 3.5
    Args:
        *dict_args: The input dictionaries to combine

    Returns:
        result: The combined input dictionaries with order preserved

    """
    result = OrderedDict()

    for dictionary in dict_args:
        result.update(dictionary)

    return result


def test_for_zero(num: ndarray) -> ndarray:
    """
    Return a mask to avoid division by zero
    Args:
        num: The input array

    Returns:
        mask: The output boolean array

    """
    mask = np.zeros_like(num, dtype=np.bool)

    mask[num != 0.] = 1

    return mask


def test_for_negative(num: ndarray) -> ndarray:
    """
    Return a mask to avoid taking the square root of a negative number
    Args:
        num: The input array

    Returns:
        mask: The output boolean array

    """
    mask = np.zeros_like(num, dtype=bool)

    mask[num >= 0.0] = 1

    return mask


def ndvi(R: ndarray, NIR: ndarray) -> ndarray:
    """
    Normalized Difference Vegetation Index
    (NIR - R) / (NIR + R)

    Args:
        R: The input red visible band
        NIR: The input NIR band

    Returns:
        result: The calculated NDVI

    """
    R_ = R * 0.0001

    NIR_ = NIR * 0.0001

    num = np.subtract(NIR_, R_)

    den = np.add(NIR_, R_)

    mask = test_for_zero(den)

    result = np.zeros_like(den, dtype=np.float64)

    result[mask] = num[mask] / den[mask]

    return result


def msavi(R: ndarray, NIR: ndarray) -> ndarray:
    """
    Modified Soil Adjusted Vegetation Index
    (2.0 * NIR + 1.0 - ((2.0 * NIR + 1.0) ** 2.0 - 8.0 * (NIR - R)) ** 0.5) / 2.0

    Args:
        R: The input red visible band
        NIR: The input NIR band

    Returns:
        result: The calculated MSAVI

    """
    R_ = R * 0.0001

    NIR_ = NIR * 0.0001

    sqrt = ((2.0 * NIR_) + 1.0) ** 2.0 - (8.0 * (NIR_ - R_))

    mask = test_for_negative(sqrt)

    result = np.zeros_like(R, dtype=np.float64)

    result[mask] = ((2.0 * NIR_[mask]) + 1 - np.sqrt(sqrt[mask])) / 2.0

    return result


def evi(B: ndarray, R: ndarray, NIR: ndarray, G=2.5, L=1.0, C1=6.0, C2=7.5) -> ndarray:
    """
    Enhanced Vegetation Index
    G * ((NIR - R) / (NIR + C1 * R - C2 * B + L))

    Args:
        B: The input blue visible band
        R: The input red visible band
        NIR: The input NIR band
        G: Gain factor
        L: Canopy background adjustment factor
        C1: Coefficient of aerosol resistance term
        C2: Coefficient of aerosol resistance term

    Returns:
        result: The calculated EVI

    """
    NIR_ = NIR * 0.0001

    R_ = R * 0.0001

    B_ = B * 0.0001

    num = np.subtract(NIR_, R_)

    den = NIR_ + (C1 * R_) - (C2 * B_) + L

    mask = test_for_zero(den)

    result = np.zeros_like(NIR, dtype=np.float64)

    result[mask] = G * (num[mask] / den[mask])

    return result


def savi(R: ndarray, NIR: ndarray, L=0.5) -> ndarray:
    """
    Soil Adjusted Vegetation Index
    ((NIR - R) / (NIR + R + L)) * (1 + L)

    Args:
        R: The input red visible band
        NIR: The input NIR band
        L: Soil brightness correction factor

    Returns:
        result: The calculated SAVI

    """
    NIR_ = NIR * 0.0001

    R_ = R * 0.0001

    num = np.subtract(NIR_, R_)

    den = NIR_ + R_ + L

    mask = test_for_zero(den)

    result = np.zeros_like(R, dtype=np.float)

    result[mask] = num[mask] / den[mask] * (1 + L)

    return result


def ndmi(NIR: ndarray, SWIR1: ndarray) -> ndarray:
    """
    Normalized Difference Moisture Index
    (NIR - SWIR1) / (NIR + SWIR1)

    Args:
        NIR: The input NIR band
        SWIR1: The input SWIR-1 band

    Returns:
        result: The calculated NDMI

    """
    num = np.subtract(NIR, SWIR1)

    den = np.add(NIR, SWIR1)

    mask = test_for_zero(den)

    result = np.zeros_like(NIR, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result


def nbr(NIR: ndarray, SWIR2: ndarray) -> ndarray:
    """
    Normalized Burn Ratio
    (NIR - SWIR2) / (NIR + SWIR2)

    Args:
        NIR: The input NIR band
        SWIR2: The input SWIR-2 band

    Returns:
        result: The calculated NBR

    """
    num = np.subtract(NIR, SWIR2)

    den = np.add(NIR, SWIR2)

    mask = test_for_zero(den)

    result = np.zeros_like(NIR, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result


def nbr2(SWIR1: ndarray, SWIR2: ndarray) -> ndarray:
    """
    Normalized Burn Ratio 2
    (SWIR1 - SWIR2) / (SWIR1 + SWIR2)

    Args:
        SWIR1: The input SWIR-1 band
        SWIR2: The input SWIR-2 band

    Returns:
        result: The calculated NBR-2

    """
    num = np.subtract(SWIR1, SWIR2)

    den = np.add(SWIR1, SWIR2)

    mask = test_for_zero(den)

    result = np.zeros_like(SWIR1, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result
