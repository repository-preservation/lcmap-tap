"""Controls for reading and writing to a zipped directory of pickle files"""

import os
import sys
import pickle
import zipfile
import subprocess
from subprocess import CalledProcessError
import datetime as dt
from lcmap_tap.logger import log, HOME, exc_handler

sys.excepthook = exc_handler

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
                # Return the empty dictionary
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

    with zipfile.ZipFile(CACHE, 'r') as f:
        names = f.namelist()

    # Remove pre-existing pickle files to avoid duplicates
    for key in cache_data.keys():
        fname = f'{key}.p'

        if fname in names:
            remove_name(CACHE, fname)

    check_cache_size(CACHE)

    with zipfile.ZipFile(CACHE, 'a', compression=zipfile.ZIP_DEFLATED) as f:
        for key, data in cache_data.items():
            fname = f'{key}.p'

            # Create  ZipInfo instance for the input data so that a date_time can be specified.
            info = zipfile.ZipInfo(fname, date_time=dt.datetime.now().timetuple())

            info.compress_type = zipfile.ZIP_DEFLATED

            info.create_system = 0

            f.writestr(info, pickle.dumps(data))

    return None


def update_cache(cache_data, new_data, key):
    """
    Add newly collected data to the pre-existing cache data

    Args:
        cache_data (dict): Pre-existing chip data
        new_data (dict): Newly acquired chip data
        key (str): The chip UL coordinates

    Returns:

    """
    if key in cache_data.keys():
        cache_data[key].update(new_data[key])

    else:
        cache_data[key] = new_data[key]

    return cache_data


def check_cache_size(cache, size=3e8):
    """
    Check the file size of the zip archive.  If it is greater than 300 MB, then delete the the oldest modified
    archive file.

    Args:
        cache (str): Full path to the zip archive.
        size (int): Limit in bytes of the file size (default=3e8).

    Returns:
        None

    """
    if os.path.getsize(cache) > size:
        with zipfile.ZipFile(CACHE, 'r') as f:

            dates = [(c, f.getinfo(c).date_time) for c in f.namelist()]

            log.debug("Archived: %s" % dates)

        dates.sort(key=lambda x: x[1], reverse=False)

        file_to_remove = dates[0][0]

        remove_name(cache, file_to_remove)

    return None


def remove_name(cache, name):
    """
    Helper function to remove a file stored in a zip archive.

    Args:
        cache (str): Full path to the zip archive.
        name (str): Name of a file within the archive.

    Returns:
        None

    """
    cmd = ['zip', '-d', cache, name]

    try:
        subprocess.check_call(cmd)

        log.info("Removed file %s from archive" % name)

    except (CalledProcessError, PermissionError):
        log.warning("Error occurred trying to remove %s from archive" % name)

    return None
