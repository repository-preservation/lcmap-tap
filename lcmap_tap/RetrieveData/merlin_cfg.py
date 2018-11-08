"""Get the required ubids and build a custom merlin profile"""

import sys
from lcmap_tap.RetrieveData import ard_groups
from lcmap_tap.logger import exc_handler
from merlin import chipmunk, dates, specs, formats
from functools import partial
from cytoolz import assoc
from typing import Iterable

sys.excepthook = exc_handler


def get_ubids(items: Iterable) -> dict:
    """
    Return a dictionary for custom-selected chipmunk-ard ubids

    Args:
        items: A list of spectral or index products selected on the GUI to retrieve data for

    Returns:
        dict: Nested dict under the main 'chipmunk-ard' key, each key points to the ubids for that band (e.g. reds)

    """
    temp = {band: ard_groups[band] for band in items}

    return {'chipmunk-ard': temp}


def get_profile(ubids: dict, url: str) -> dict:
    """
    Create a custom profile that can be used by merlin to make a call to chipmunk for specific bands

    Args:
        url: CONUS ARD chipmunk url
        ubids: The custom ubids selected by the user

    Returns:
        dict: The profile specifying which bands to retrieve

    """
    env = {"CHIPMUNK_URL": url}

    return {'grid_fn': partial(chipmunk.grid,
                               url=env.get('CHIPMUNK_URL', None),
                               resource=env.get('CHIPMUNK_GRID_RESOURCE', '/grid')),

            'dates_fn': dates.symmetric,

            'chips_fn': partial(chipmunk.chips,
                                url=env.get('CHIPMUNK_URL', None),
                                resource=env.get('CHIPMUNK_CHIPS_RESOURCE', '/chips')),

            'specs_fn': partial(specs.mapped, ubids=ubids['chipmunk-ard']),

            'format_fn': formats.pyccd,

            'registry_fn': partial(chipmunk.registry,
                                   url=env.get('CHIPMUNK_URL', None),
                                   resource=env.get('CHIPMUNK_REGISTRY_RESOURCE', '/registry')),

            'snap_fn': partial(chipmunk.snap,
                               url=env.get('CHIPMUNK_URL', None),
                               resource=env.get('CHIPMUNK_SNAP_RESOURCE', '/grid/snap'))}


def make_cfg(items: Iterable, url: str, profile: str='chipmunk-ard') -> dict:
    """
    Wrapper to generate the custom profile and ubids in one function

    Args:
        items: A list of spectral bands including thermal, and/or indices
        url: CONUS ARD chipmunk url
        profile: The name of the profile, default is 'chipmunk-ard'

    Returns:
        A Merlin configuration

    """
    p = get_profile(get_ubids(items), url)

    return assoc(p, 'profile', profile)
