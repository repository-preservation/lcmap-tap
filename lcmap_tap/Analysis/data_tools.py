"""Some helpful functions for working with a pandas DataFrame object"""

from lcmap_tap.Analysis import mask_values
import warnings
import datetime as dt
import pandas as pd
import numpy as np
from collections import OrderedDict

warnings.simplefilter('ignore')


def temporal(df, ascending=True, field='dates'):
    """
    Sort the input data frame based on time
    Args:
        df (pd.DataFrame): The input data
        ascending (bool): Whether or not to sort in ascending order
        field (str): The data frame field containing datetime objects

    Returns:
        pd.DataFrame

    """
    return df.sort_values(field, ascending).reset_index(drop=True)


def sort_on(df, field, ascending=True):
    """
    A more open-ended sorting function, may be used on a specified field

    Args:
        df (pd.DataFrame): The input data
        field (str): The field to sort on
        ascending (bool): Whether or not to sort in ascending order

    Returns:
        pd.DataFrame

    """
    return df.sort_values(field, ascending).reset_index(drop=True)


def dates(df, params, field='dates'):
    """
    Return an inclusive sliced portion of the input data frame based on a min and max date

    Args:
        df (pd.DataFrame): The input data
        params (Tuple[dt.datetime, dt.datetime]): Dates, must be in order of MIN, MAX
        field (str): The date field used to find matching values

    Returns:
        pd.DataFrame

    """
    _min, _max = params

    return df[(df[field] >= _min) & (df[field] <= _max)].reset_index(drop=True)


def years(df):
    """
    Get an array of unique years in the current time series

    Args:
        df (pd.DataFrame): The input data frame

    Returns:
        np.ndarray

    """
    return df['dates'].apply(lambda x: (x.timetuple()).tm_year).unique()


def date_range(params):
    """
    Generate date ranges for a seasonal time series

    Args:
        params (dict): Arguments for the pandas date_range function

    Returns:

    """
    return pd.date_range(**params)


def seasons(df, start_mon, start_d, end_mon, end_d, periods=None, freq='D', **kwargs):
    """

    Args:
        df:
        start_mon:
        start_d:
        end_mon:
        end_d:
        periods:
        freq:
        **kwargs:

    Returns:

    """
    return OrderedDict([(y,
                         date_range({'start': dt.datetime(y, start_mon, start_d),
                                     'end': dt.datetime(y, end_mon, end_d),
                                     'periods': periods,
                                     'freq': freq}))

                        for y in years(df)])


def stats(arr):
    """
    Return the statistics for an input array of values

    Args:
        arr (np.ndarray)

    Returns:
        OrderedDict

    """
    try:
        return OrderedDict([('min', arr.mean()),
                            ('max', arr.max()),
                            ('mean', arr.mean()),
                            ('std', arr.std())])

    except ValueError:  # Can happen if the input array is empty
        return OrderedDict([('min', None),
                            ('max', None),
                            ('mean', None),
                            ('std', None)])


def get_seasonal_info(df, params):
    """
    A wrapper function for easily returning the statistics on a seasonal basis for a given field of the data frame

    Args:
        df (pd.DataFrame)
        params (dict)

    Returns:
        OrderedDict

    """

    __seasons = seasons(df, **params)

    return OrderedDict([
        (y, stats(
            values(
                mask(
                    dates(df, (__seasons[y][0], __seasons[y][-1])), **params
                ), **params
            )
        )
         )
        for y in years(df)
    ])


def values(df, field, **kwargs):
    """
    Return values from a specific field of the data frame within a given time extent

    Args:
        df (pd.DataFrame): The exported TAP tool data
        field (str): The field representing the column name

    Returns:
        np.ndarray: An array of the time-specified values

    """
    return df[field].values


def plot_data(d, field):
    """
    Return the x and y series to be used for plotting

    Args:
        d (OrderedDict)
        field (str)

    Returns:
        Tuple[list, list]:
            [0] The x-series
            [1] The y-series

    """
    return ([year for year in d.keys() if d[year][field] is not None],
            [i[field] for k, i in d.items() if i[field] is not None])


def mask(df, mask_values=mask_values, mask_field='qa', **kwargs):
    """
    Remove rows from the data frame that match a condition

    Args:
        df (pd.DataFrame): The input data
        mask_value (Number[int, float]): The value used to filter the data frame, rows == value will be removed!
        mask_field (str): The field to use for filtering

    Returns:
        pd.DataFrame

    """
    return df[~df[mask_field].isin(np.array(mask_values))].reset_index(drop=True)
