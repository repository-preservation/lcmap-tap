"""
Functions for producing product values from CCDC results.
"""

import datetime as dt
from typing import Union, NamedTuple, Tuple, Sequence, List
from operator import attrgetter
from functools import lru_cache

import numpy as np
from osgeo import gdal

from mapify.app import dfc as _dfc
from mapify.app import chg_begining as _chg_begining
from mapify.app import chg_magbands as _chg_magbands
from mapify.app import lc_map as _lc_map
from mapify.app import nlcdxwalk as _nlcdxwalk


__ordbegin = dt.datetime.strptime(_chg_begining, '%Y-%m-%d').toordinal()


class BandModel(NamedTuple):
    """
    Container for change detection spectral models.
    """
    name: str
    magnitude: float
    rmse: float
    intercept: float
    coefficients: tuple


class CCDCModel(NamedTuple):
    """
    Container for the unified CCDC model.
    """
    start_day: int
    end_day: int
    break_day: int
    obs_count: int
    change_prob: float
    curve_qa: int
    bands: tuple
    class_split: int
    class_probs1: np.ndarray
    class_probs2: np.ndarray
    class_vals: tuple


def sortmodels(models: Sequence, key: str='start_day') -> list:
    """
    Sort a sequence of CCDC models based upon given key.

    Args:
        models: sequence of CCDC of namedtuples
        key: attribute to sort on

    Returns:
        sorted sequence
    """
    return sorted(models, key=attrgetter(key))


# @lru_cache()
def modelprobs(model: CCDCModel, ordinal: int) -> np.ndarray:
    """
    Simple function to extract the class probabilities that go with the associated
    ordinal date. This function makes no assumptions on whether the date is
    actually contained within the segment, it simply does a date comparison
    against the class_split attribute if it exists.

    Args:
        model: classified CCDCmodel namedtuple
        ordinal: ordinal date

    Returns:
        class probabilities
    """
    if 0 < model.class_split <= ordinal:
        return model.class_probs2
    else:
        return model.class_probs1


def growth(model: CCDCModel, lc_mapping: dict=_lc_map) -> bool:
    """
    Determine if the CCDC model represents a growth segment:
    tree -> grass/shrub, indicates decline
    or
    grass/shrub -> tree, indicates growth

    Args:
        model: classified CCDCmodel namedtuple
        lc_mapping: mapping of land cover names to values

    Returns:
        True if it is growth
    """
    if model.class_split > 0:
        if np.argmax(model.class_probs1) == lc_mapping['grass']:
            return True

    return False


def decline(model: CCDCModel, lc_mapping: dict=_lc_map) -> bool:
    """
    Determine if the CCDC model represents a growth segment:
    tree -> grass/shrub, indicates decline
    or
    grass/shrub -> tree, indicates growth

    Args:
        model: classified CCDCmodel namedtuple
        lc_mapping: mapping of land cover names to values

    Returns:
        True if it is decline
    """
    if model.class_split > 0:
        if np.argmax(model.class_probs1) == lc_mapping['tree']:
            return True

    return False


# @lru_cache()
def rankidx(model: CCDCModel, ordinal: int, rank: int) -> int:
    """
    Find the index of a given rank relative to the probabilities.

    Args:
        model: classified CCDCmodel namedtuple
        ordinal: standard python ordinal starting on day 1 of year 1
        rank: which numeric rank to pull,
            0 - primary, 1- secondary, 2 - tertiary ...

    Returns:
        array index
    """
    # argsort is ascending, so -probs flips it to descending.
    return np.argsort(-modelprobs(model, ordinal))[rank]


# @lru_cache()
def modelprob(model: CCDCModel, ordinal: int, rank: int) -> float:
    """
    Provide the probability at the given rank (0, 1, 3 ...). This function
    makes no assumptions on whether the date is actually contained within the
    segment. It is simply used as a comparison against the class_split attribute
    if it exists.

    Args:
        model: classified CCDCmodel namedtuple
        ordinal: standard python ordinal starting on day 1 of year 1
        rank: which numeric rank to pull,
            0 - primary, 1- secondary, 2 - tertiary ...

    Returns:
        probability value at the rank
    """
    return modelprobs(model, ordinal)[rankidx(model, ordinal, rank)]


# @lru_cache()
def scaleprob(prob: float, factor: float=100) -> int:
    """
    Provide consistent scaling of values into integer space. This maintains a
    minimum value of 1.

    Args:
        prob: probability value, typically from 0 to 1
        factor: scale factor

    Returns:
        scaled probability value
    """
    prob *= factor

    if prob < 1:
        return 1

    return int(prob)


# @lru_cache()
def modelclass(model: CCDCModel, ordinal: int, rank: int) -> int:
    """
    Provide the class value at the given rank (0, 1, 2, 3 ...). This function
    makes no assumptions on whether the date is actually contained within the
    segment. It is simply used as a comparison against the class_split attribute
    if it exists.

    Args:
        model: classified CCDCmodel namedtuple
        ordinal: standard python ordinal starting on day 1 of year 1
        rank: which numeric rank to pull,
            0 - primary, 1- secondary, 2 - tertiary ...

    Returns:
        class value at the rank
    """
    return model.class_vals[rankidx(model, ordinal, rank)]


def noclass(model: CCDCModel, ordinal: int, rank: int) -> bool:
    return modelclass(model, ordinal, rank) == 0


def landcover(models: Sequence, ordinal: int, rank: int, dfcmap: dict=_dfc,
              fill_begin: bool=True, fill_end: bool=True, fill_samelc: bool=True,
              fill_difflc: bool=True, fill_nodata: bool=True, fill_nodataval: int=None,
              **kwargs) -> int:
    """
    Given a sequence of CCDC models representing pixel history and an ordinal date,
    what is the Primary Land Cover value?

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1
        rank: which numeric rank to pull,
            0 - primary, 1- secondary, 2 - tertiary ...
        dfcmap: data format mapping, determines what values to assign for the
            various conditionals that could occur
        fill_begin: if the date falls before a known segment,
            use the first segment's value
        fill_end: if the date falls after all segments have ended,
            use the last segment's value
        fill_samelc: if the date falls between two segments,
            and they have the same class, use that class
        fill_difflc: if the date falls between two segments,
            if the date falls before the break date of the first segment, then use the first,
            if the date falls after the break date, then use the second
        fill_nodata: whether fill where there is no models at all
        fill_nodataval: value to use when there is no data

    Returns:
        primary land cover class value

    """
    if ordinal <= 0 or not models:
        if fill_nodata:
            return fill_nodataval
        return dfcmap['lc_insuff']

    # ord date before time series models -> cover back
    if ordinal < models[0].start_day:
        if fill_begin:
            return modelclass(models[0], ordinal, rank)
        return dfcmap['lc_insuff']

    # ord date after time series models -> cover forward
    if ordinal > models[-1].end_day:
        if fill_end:
            return modelclass(models[-1], ordinal, rank)
        return dfcmap['lc_insuff']

    prev_end = 0
    prev_br = 0
    prev_class = 0
    for m in models:
        curr_class = modelclass(m, ordinal, rank)
        # Date is contained within the model
        if m.start_day <= ordinal <= m.end_day:
            return curr_class
        # Same land cover fill
        elif fill_samelc and curr_class == prev_class and prev_end < ordinal < m.start_day:
            return curr_class
        # Different land cover fill, previous break -> current model
        elif fill_difflc and prev_br <= ordinal < m.start_day:
            return curr_class
        # Different land cover fill, model end -> break
        elif fill_difflc and m.end_day < ordinal < m.break_day:
            return curr_class

        prev_end = m.end_day
        prev_br = m.break_day
        prev_class = curr_class

    return dfcmap['lc_inbtw']


def landcover_conf(models: Sequence, ordinal: int, rank: int, dfcmap: dict=_dfc,
                   **kwargs) -> int:
    """
    Given a sequence of CCDC models representing pixel history and an ordinal date,
    what is the Primary Land Cover Confidence value?

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1
        rank: which numeric rank to pull,
            0 - primary, 1- secondary, 2 - tertiary ...
        dfcmap: data format mapping, determines what values to assign for the
            various conditionals that could occur

    Returns:
        primary land cover confidence value
    """
    if ordinal <= 0 or not models:
        return dfcmap['lcc_nomodel']

    # ord date before time series models
    if ordinal < models[0].start_day:
        return dfcmap['lcc_back']

    # ord date after time series models
    if ordinal > models[-1].end_day:
        if models[-1].change_prob == 1:
            return dfcmap['lcc_afterbr']

        return dfcmap['lcc_forwards']

    prev_end = 0
    prev_class = 0
    for m in models:
        curr_class = modelclass(m, ordinal, rank)
        # Date is contained within the model
        if m.start_day <= ordinal <= m.end_day:
            # Annualized classification mucking jazz
            if growth(m):
                return dfcmap['lcc_growth']
            elif decline(m):
                return dfcmap['lcc_decline']
            return scaleprob(modelprob(m, ordinal, rank))
        elif curr_class == prev_class and prev_end < ordinal < m.start_day:
            return dfcmap['lcc_samelc']
        elif prev_end <= ordinal < m.start_day:
            return dfcmap['lcc_difflc']

        prev_end = m.end_day
        prev_class = curr_class

    raise ValueError


def crosswalk(inarr: np.ndarray, xwalkmap: dict=_nlcdxwalk, **kwargs) -> np.ndarray:
    """
    Cross-walks values in a data set to another set of values.

    Args:
        inarr: values to crosswalk
        xwalkmap: mapping of how to crosswalk

    Returns:
        np array of cross-walked values
    """

    outarr = np.copy(inarr)

    for old, new in xwalkmap.items():
        outarr[inarr == old] = new

    return outarr


def lc_nodatafill(lc_arr: np.ndarray, nlcd: np.ndarray, lcc_arr: np.ndarray=None,
                  xwalk: bool=True, xwalkmap: dict=_nlcdxwalk,
                  dfcmap: dict=_dfc, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fill areas without a model with NLCD data.

    Args:
        lc_arr: array of land cover values
        nlcd: array of NLCD values for same region
        lcc_arr: array of land cover confidence values
        xwalk: boolean if the NLCD values need to be cross-walked
        xwalkmap: mapping to on how to cross-walk the NLCD values
        dfcmap: data format mapping, determines what values to assign for the
            various conditionals that could occur

    Returns:
        filled land cover and land cover confidence arrays (if confidence was given)
    """
    if xwalk:
        nlcd = crosswalk(nlcd, xwalkmap)

    outlc = np.copy(lc_arr)
    outlcc = None

    mask = outlc == dfcmap['lc_insuff']
    outlc[mask] = nlcd[mask]

    if lcc_arr:
        outlcc = np.copy(lcc_arr)
        outlcc[mask] = dfcmap['lccf_nomodel']

    return outlc, outlcc


def lc_primary(models: Sequence, ordinal: int, dfcmap: dict=_dfc,
               fill_begin: bool=True, fill_end: bool=True, fill_samelc: bool=True,
               fill_difflc: bool=True, fill_nodata: bool=True, fill_nodataval: int=None,
               **kwargs) -> int:
    return landcover(models, ordinal, 0, dfcmap, fill_begin, fill_end, fill_samelc,
                     fill_difflc, fill_nodata, fill_nodataval, **kwargs)


def lc_secondary(models: Sequence, ordinal: int, dfcmap: dict=_dfc,
                 fill_begin: bool=True, fill_end: bool=True, fill_samelc: bool=True,
                 fill_difflc: bool=True, fill_nodata: bool=True, fill_nodataval: int=None,
                 **kwargs) -> int:
    return landcover(models, ordinal, 1, dfcmap, fill_begin, fill_end, fill_samelc,
                     fill_difflc, fill_nodata, fill_nodataval, **kwargs)


def lc_primaryconf(models: Sequence, ordinal: int, dfcmap: dict=_dfc, **kwargs) -> int:
    return landcover_conf(models, ordinal, 0, dfcmap)


def lc_secondaryconf(models: Sequence, ordinal: int, dfcmap: dict=_dfc, **kwargs) -> int:
    return landcover_conf(models, ordinal, 1, dfcmap)


def lc_fromto(models: Sequence, ordinal: int, dfcmap: dict=_dfc,
              fill_begin: bool=True, fill_end: bool=True, fill_samelc: bool=True,
              fill_difflc: bool=True, fill_nodata: bool=True, fill_nodataval: int=None,
              **kwargs) -> int:
    """
    Traditional from-to for the primary land cover.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1
        dfcmap: data format mapping, determines what values to assign for the
            various conditionals that could occur
        fill_begin: if the date falls before a known segment,
            use the first segment's value
        fill_end: if the date falls after all segments have ended,
            use the last segment's value
        fill_samelc: if the date falls between two segments,
            and they have the same class, use that class
        fill_difflc: if the date falls between two segments,
            if the date falls before the break date of the first segment, then use the first,
            if the date falls after the break date, then use the second
        fill_nodata: whether fill where there is no models at all
        fill_nodataval: value to use when there is no data

    Returns:
        fromto value

    """
    prev_yr = dt.date.fromordinal(ordinal)
    prev_yr = dt.date(year=prev_yr.year - 1, month=prev_yr.month, day=prev_yr.day)

    curr = lc_primary(models, ordinal, dfcmap, fill_begin, fill_end, fill_samelc, 
                      fill_difflc, fill_nodata, fill_nodataval, **kwargs)
    prev = lc_primary(models, prev_yr.toordinal(), dfcmap, fill_begin, fill_end, fill_samelc, 
                      fill_difflc, fill_nodata, fill_nodataval, **kwargs)

    if prev == curr:
        return curr

    return prev * 10 + curr


def chg_doy(models: Sequence, ordinal: int, **kwargs) -> int:
    """
    The day of year that a change happened, if a change happened in the
    same year as the ordinal given.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        day of year or 0

    """
    if ordinal <= 0 or not models:
        return 0

    query_date = dt.date.fromordinal(ordinal)

    for m in models:
        if m.break_day <= 0:
            continue

        break_date = dt.date.fromordinal(m.break_day)

        if query_date.year == break_date.year and m.change_prob == 1:
            return break_date.timetuple().tm_yday

    return 0


def chg_mag(models: Sequence, ordinal: int, bands: Sequence=_chg_magbands, **kwargs) -> float:
    """
    The spectral magnitude of the change (if one occurred) in the same
    year as the given ordinal.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1
        bands: spectral band names to perform the calculation over

    Returns:
        magnitude or 0

    """
    if ordinal <= 0 or not models:
        return 0

    query_date = dt.date.fromordinal(ordinal)

    for m in models:
        if m.break_day <= 0:
            continue

        break_date = dt.date.fromordinal(m.break_day)

        if query_date.year == break_date.year and m.change_prob == 1:
            mags = [b.magnitude for b in m.bands if b.name in bands]
            return np.linalg.norm(mags)

    return 0


def chg_modelqa(models: Sequence, ordinal: int, **kwargs) -> int:
    """
    Information on the quality of the curve fit the intercept the ordinal date.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        curve_qa or 0

    """
    if ordinal <= 0 or not models:
        return 0

    for m in models:
        if m.start_day <= ordinal <= m.end_day:
            return m.curve_qa

    return 0


def chg_seglength(models: Sequence, ordinal: int, ordbegin: int=__ordbegin, **kwargs) -> int:
    """
    How long, in days, has the current model been underway. This includes
    between or outside of CCD segments as well.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1
        ordbegin: when to start counting from

    Returns:
        number of days
    """
    if ordinal <= 0:
        return 0

    diff = [ordinal - ordbegin]
    for m in models:
        if ordinal > m.end_day:
            diff.append(ordinal - m.end_day)
        else:
            diff.append(ordinal - m.start_day)

    return min(filter(lambda x: x >= 0, diff), default=0)


def chg_lastbrk(models: Sequence, ordinal: int, **kwargs) -> int:
    """
    How long ago, in days, was the last spectral break.
    0 if before the first break.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        number of days
    """
    if ordinal <= 0 or not models:
        return 0

    diff = [(ordinal - m.break_day) for m in models if m.change_prob == 1]

    return min(filter(lambda x: x >= 0, diff), default=0)


def predict(band: BandModel, ordinal: int) -> float:
    """
    Predict the value at the given day.
    Does no bounds checking.

    Args:
        band: individual CCDC band model
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        predicted value
    """
    w = 2 * np.pi / 365.2425
    sl, c1, c2, c3, c4, c5, c6 = band.coefficients
    return (c1 * np.cos(w * ordinal) + c2 * np.sin(w * ordinal) +
            c3 * np.cos(2 * w * ordinal) + c4 * np.sin(2 * w * ordinal) +
            c5 * np.cos(3 * w * ordinal) + c6 * np.sin(3 * w * ordinal) +
            band.intercept + sl * ordinal)


def syntheticselect(models: Sequence, ordinal: int) -> Union[CCDCModel, None]:
    """
    Select a model to build predictions from.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        model
    """
    if not models:
        return None

    # ord date before time series models -> cover back
    if ordinal < models[0].start_day:
        return models[0]

    # ord date after time series models -> cover forward
    if ordinal > models[-1].end_day:
        return models[-1]

    prev_br = 0
    for m in models:
        # Date is contained within the model
        if m.start_day <= ordinal <= m.end_day:
            return m
        elif prev_br <= ordinal < m.start_day:
            return m
        elif m.end_day < ordinal < m.break_day:
            return m

        prev_br = m.break_day

    raise ValueError


def kelvin(therm: float) -> float:
    """
    Pyccd converts (and scales) the thermal values into Celsius, this converts
    them back to kelvin.

    Args:
        therm: thermal value in degrees Celsius

    Returns:
        thermal value in kelvin
    """
    return therm / 10 + 27315


def synthetic(models: Sequence, ordinal: int, **kwargs) -> List[int]:
    """
    Do the model predictions in order to produce fake imagery.

    Args:
        models: sorted sequence of CCDC namedtuples that represent the pixel history
        ordinal: standard python ordinal starting on day 1 of year 1

    Returns:
        blue, green, red, nir, swir1, swir2, thermal values
    """
    model = syntheticselect(models, ordinal)

    if model is None:
        return [0] * 7

    vals = []
    for name in ('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'thermal'):
        for band in model.bands:
            if band.name == name:
                if name == 'thermal':
                    vals.append(int(kelvin(predict(band, ordinal))))
                else:
                    vals.append(int(predict(band, ordinal)))

    return vals


def prodmap() -> dict:
    """
    Container function to hold the product mapping, showing which names map to
    which functions and other such information ...

    {'product name': [function, gdal data type],
     ...}

    Returns:
        product mapping
    """
    return {'Chg_ChangeDay': [chg_doy, gdal.GDT_UInt16],
            'Chg_LastChange': [chg_lastbrk, gdal.GDT_UInt16],
            'Chg_SegLength': [chg_seglength, gdal.GDT_UInt16],
            'Chg_ChangeMag': [chg_mag, gdal.GDT_Float32],
            'Chg_Quality': [chg_modelqa, gdal.GDT_Byte],
            'LC_Primary': [lc_primary, gdal.GDT_Byte],
            'LC_Secondary': [lc_secondary, gdal.GDT_Byte],
            'LC_PrimeConf': [lc_primaryconf, gdal.GDT_Byte],
            'LC_SecondConf': [lc_secondaryconf, gdal.GDT_Byte],
            'LC_Change': [lc_fromto, gdal.GDT_Byte],
            'Synthetic': [synthetic, gdal.GDT_UInt16]}


def is_lc(name: str) -> bool:
    """
    Helper function to identify if a product is a land cover thematic product.

    Args:
        name: the name of the product

    Returns:
        True if it is a land cover product
    """
    return name in ('LC_Primary', 'LC_Secondary', 'LC_Change')


def lc_color() -> gdal.ColorTable:
    """
    Provide a default color table for Land Cover thematic products.

    Returns:
        color table
    """
    ct = gdal.ColorTable()
    ct.SetColorEntry(0, (0, 0, 0, 0))  # Black No data
    ct.SetColorEntry(1, (238, 0, 0, 0))  # Red Developed
    ct.SetColorEntry(2, (171, 112, 40, 0))  # Orange Ag
    ct.SetColorEntry(3, (227, 227, 194, 0))  # Yellow Grass
    ct.SetColorEntry(4, (28, 99, 48, 0))  # Green Tree
    ct.SetColorEntry(5, (71, 107, 161, 0))  # Blue Water
    ct.SetColorEntry(6, (186, 217, 235, 0))  # Lt. Blue Wet
    ct.SetColorEntry(7, (255, 255, 255, 0))  # White Snow
    ct.SetColorEntry(8, (179, 174, 163, 0))  # Brown Barren
    ct.SetColorEntry(9, (251, 154, 153, 0))  # Pink Change

    # SegChange Values
    # Same class
    ct.SetColorEntry(11, (238, 0, 0, 0))  # Red Developed
    ct.SetColorEntry(22, (171, 112, 40, 0))  # Orange Ag
    ct.SetColorEntry(33, (227, 227, 194, 0))  # Yellow Grass
    ct.SetColorEntry(44, (28, 99, 48, 0))  # Green Tree
    ct.SetColorEntry(55, (71, 107, 161, 0))  # Blue Water
    ct.SetColorEntry(66, (186, 217, 235, 0))  # Lt. Blue Wet
    ct.SetColorEntry(77, (255, 255, 255, 0))  # White Snow
    ct.SetColorEntry(88, (179, 174, 163, 0))  # Brown Barren

    for i in range(1, 9):
        ct.SetColorEntry(i * 10, (145, 145, 145, 0))  # End of Time Series

        for j in range(1, 9):
            if i != j:
                ct.SetColorEntry(int(f'{i}{j}'), (162, 1, 255, 0))  # Different class

    return ct
