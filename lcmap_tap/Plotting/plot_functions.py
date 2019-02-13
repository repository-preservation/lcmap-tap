"""Define various functions to make life easier (ideally)"""

import numpy as np
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


def apply_scaling_factor(num: np.ndarray, factor: float=0.0001) -> np.ndarray:
    """
    Apply a scaling factor to input data

    Args:
        num: input array containing reflectance data to be re-scaled
        factor: scaling factor, default is 0.0001

    Returns:
        The re-scaled reflectance data

    """
    return num * factor


def replace_negative_reflectance(num: np.ndarray) -> np.ndarray:
    """
    If any values of the array are negative, replace them with 0.  There should be no negative reflectance values.

    Args:
        num: The input reflectance data for any SR-band

    """
    num[num < 0] = 0

    return num


def mask_zero(num: np.ndarray) -> np.ndarray:
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


def mask_negative(num: np.ndarray) -> np.ndarray:
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


def ndvi(R: np.ndarray, NIR: np.ndarray) -> np.ndarray:
    """
    Normalized Difference Vegetation Index
    (NIR - R) / (NIR + R)

    Args:
        R: The input red visible band
        NIR: The input NIR band

    Returns:
        result: The calculated NDVI

    """
    _R = replace_negative_reflectance(apply_scaling_factor(R))

    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    num = np.subtract(_NIR, _R)

    den = np.add(_NIR, _R)

    mask = mask_zero(den)

    result = np.zeros_like(den, dtype=np.float64)

    result[mask] = num[mask] / den[mask]

    return result


def msavi(R: np.ndarray, NIR: np.ndarray) -> np.ndarray:
    """
    Modified Soil Adjusted Vegetation Index
    (2.0 * NIR + 1.0 - ((2.0 * NIR + 1.0) ** 2.0 - 8.0 * (NIR - R)) ** 0.5) / 2.0

    Args:
        R: The input red visible band
        NIR: The input NIR band

    Returns:
        result: The calculated MSAVI

    """
    _R = replace_negative_reflectance(apply_scaling_factor(R))

    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    sqrt = ((2.0 * _NIR) + 1.0) ** 2.0 - (8.0 * (_NIR - _R))

    mask = mask_negative(sqrt)

    result = np.zeros_like(R, dtype=np.float64)

    result[mask] = ((2.0 * _NIR[mask]) + 1 - np.sqrt(sqrt[mask])) / 2.0

    return result


def evi(B: np.ndarray, R: np.ndarray, NIR: np.ndarray, G=2.5, L=1.0, C1=6.0, C2=7.5) -> np.ndarray:
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
    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    _R = replace_negative_reflectance(apply_scaling_factor(R))

    _B = replace_negative_reflectance(apply_scaling_factor(B))

    num = np.subtract(_NIR, _R)

    den = _NIR + (C1 * _R) - (C2 * _B) + L

    mask = mask_zero(den)

    result = np.zeros_like(NIR, dtype=np.float64)

    result[mask] = G * (num[mask] / den[mask])

    return result


def savi(R: np.ndarray, NIR: np.ndarray, L=0.5) -> np.ndarray:
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
    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    _R = replace_negative_reflectance(apply_scaling_factor(R))

    num = np.subtract(_NIR, _R)

    den = _NIR + _R + L

    mask = mask_zero(den)

    result = np.zeros_like(R, dtype=np.float)

    result[mask] = num[mask] / den[mask] * (1 + L)

    return result


def ndmi(NIR: np.ndarray, SWIR1: np.ndarray) -> np.ndarray:
    """
    Normalized Difference Moisture Index
    (NIR - SWIR1) / (NIR + SWIR1)

    Args:
        NIR: The input NIR band
        SWIR1: The input SWIR-1 band

    Returns:
        result: The calculated NDMI

    """
    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    _SWIR1 = replace_negative_reflectance(apply_scaling_factor(SWIR1))

    num = np.subtract(_NIR, _SWIR1)

    den = np.add(_NIR, _SWIR1)

    mask = mask_zero(den)

    result = np.zeros_like(_NIR, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result


def nbr(NIR: np.ndarray, SWIR2: np.ndarray) -> np.ndarray:
    """
    Normalized Burn Ratio
    (NIR - SWIR2) / (NIR + SWIR2)

    Args:
        NIR: The input NIR band
        SWIR2: The input SWIR-2 band

    Returns:
        result: The calculated NBR

    """
    _NIR = replace_negative_reflectance(apply_scaling_factor(NIR))

    _SWIR2 = replace_negative_reflectance(apply_scaling_factor(SWIR2))

    num = np.subtract(_NIR, _SWIR2)

    den = np.add(_NIR, _SWIR2)

    mask = mask_zero(den)

    result = np.zeros_like(_NIR, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result


def nbr2(SWIR1: np.ndarray, SWIR2: np.ndarray) -> np.ndarray:
    """
    Normalized Burn Ratio 2
    (SWIR1 - SWIR2) / (SWIR1 + SWIR2)

    Args:
        SWIR1: The input SWIR-1 band
        SWIR2: The input SWIR-2 band

    Returns:
        result: The calculated NBR-2

    """
    _SWIR1 = replace_negative_reflectance(apply_scaling_factor(SWIR1))

    _SWIR2 = replace_negative_reflectance(apply_scaling_factor(SWIR2))

    num = np.subtract(_SWIR1, _SWIR2)

    den = np.add(_SWIR1, _SWIR2)

    mask = mask_zero(den)

    result = np.zeros_like(_SWIR1, dtype=np.float)

    result[mask] = num[mask] / den[mask]

    return result
