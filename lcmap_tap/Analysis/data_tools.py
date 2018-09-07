"""Some helpful functions for working with a pandas DataFrame object"""


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
    min, max = params

    return df[(df[field] >= min) & (df[field] <= max)].reset_index(drop=True)


def filter(df, value, field='qa'):
    """
    Remove rows from the data frame that match a condition

    Args:
        df (pd.DataFrame): The input data
        value (Number[int, float]): The value used to filter the data frame, rows == value will be removed!
        field (str): The field to use for filtering

    Returns:
        pd.DataFrame

    """
    return df[df[field] != value].reset_index(drop=True)
