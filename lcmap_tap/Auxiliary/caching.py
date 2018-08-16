"""Controls for reading and writing to a zipped directory of pickle files"""

import os
import pickle
import zipfile
from lcmap_tap.logger import log, HOME

CACHE = os.path.join(HOME, 'ard_cache.zip')


def read_cache(geo_info, cache_data):
    """
    Using the chip coordinates, locate the pickle file containing that chip within the zip archive

    Args:
        geo_info (GeoInfo): Geographic information pertaining to an input coordinate
        cache_data (dict): The current collection of chip data

    Returns:

    """
    # The pickle file to look for within the zip archive
    fname = f'{geo_info.chip_coord.x}_{geo_info.chip_coord.y}.p'

    # The key to be used in the cache_data dict
    key = os.path.splitext(fname)[0]

    log.info("Reading cache data from %s" % CACHE)
    log.info("Looking for chip file %s" % fname)

    try:
        with zipfile.ZipFile(CACHE, 'r') as f:
            contents = f.namelist()

            if fname in contents:
                with f.open(fname, 'r') as p:
                    temp = {os.path.splitext(fname)[0]: pickle.load(p)}

                cache_data = update_cache(cache_data, temp, key)

            else:
                log.info("Chip file %s does not exist yet" % fname)

    except (FileNotFoundError, EOFError):
        log.info("Cache file %s not found but will be generated on exit" % CACHE)

    return cache_data


def save_cache(cache_data):
    """
    Add the chip data to a zipped archive

    Args:
        cache_data (dict): Chip data

    Returns:

    """
    log.info("Saving cache data to %s ..." % CACHE)

    with zipfile.ZipFile(CACHE, 'w', compression=zipfile.ZIP_DEFLATED) as f:
        for key, data in cache_data.items():
            # fname = str(key).replace('(', '').replace(')', '').replace(', ', '_')

            with f.open(f'{key}.p', 'w') as p:
                pickle.dump(data, p)

    return None


def update_cache(cache_data, new_data, key):
    """
    Add newly collected data to the pre-existing cache data

    Args:
        cache_data (dict): Pre-existing chip data
        new_data (dict): Newly acquired chip data

    Returns:

    """
    if key in cache_data.keys():
        cache_data[key].update(new_data[key])

    else:
        cache_data[key] = new_data[key]

    return cache_data


def check_cache_size(cache, length=10):
    """
    Get the number of chips in the cache.  If it's greater than a set length, then remove the oldest
    entries until the length is satisfied

    Returns:

    """
    lookup = sorted([(k, item['pulled']) for k, item in cache.items()],
                    key=lambda d: d[1], reverse=False)

    test = len(cache)

    for ind in lookup:
        if test > length:
            try:
                cache.pop(ind[0], None)

                test = test - 1

            except KeyError:
                continue

    return cache
