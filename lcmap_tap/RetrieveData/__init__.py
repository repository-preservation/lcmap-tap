
from collections import namedtuple

GeoExtent = namedtuple("GeoExtent", ["x_min", "y_max", "x_max", "y_min"])

GeoAffine = namedtuple("GeoAffine", ["ul_x", "x_res", "rot_1", "ul_y", "rot_2", "y_res"])

GeoCoordinate = namedtuple("GeoCoordinate", ["x", "y"])

RowColumn = namedtuple("RowColumn", ["row", "column"])

RowColumnExtent = namedtuple("RowColumnExtent", ["start_row", "start_col", "end_row", "end_col"])

CONUS_EXTENT = GeoExtent(x_min=-2565585,
                         y_min=14805,
                         x_max=2384415,
                         y_max=3314805)

# <dict> Used to look-up the sensor-specific bands stored in a scene tarball.
band_specs = {
    "LC08": {
        "SR": {"blue": "SRB2",
               "green": "SRB3",
               "red": "SRB4",
               "nir": "SRB5",
               "swir1": "SRB6",
               "swir2": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"thermal": "BTB10"}
    },
    "LE07": {
        "SR": {"blue": "SRB1",
               "green": "SRB2",
               "red": "SRB3",
               "nir": "SRB4",
               "swir1": "SRB5",
               "swir2": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"thermal": "BTB6"}
    },
    "LT05": {
        "SR": {"blue": "SRB1",
               "green": "SRB2",
               "red": "SRB3",
               "nir": "SRB4",
               "swir1": "SRB5",
               "swir2": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"thermal": "BTB6"}
    },
    "LT04": {
        "SR": {"blue": "SRB1",
               "green": "SRB2",
               "red": "SRB3",
               "nir": "SRB4",
               "swir1": "SRB5",
               "swir2": "SRB7",
               "qa": "PIXELQA"},
        "BT": {"thermal": "BTB6"}
    },
}

ard_groups = {'reds': ['LC08_SRB4', 'LE07_SRB3', 'LT05_SRB3', 'LT04_SRB3'],
#               'toa_reds': ['LC08_TAB4', 'LE07_TAB3', 'LT05_TAB3', 'LT04_TAB3'],
              'greens': ['LC08_SRB3', 'LE07_SRB2', 'LT05_SRB2', 'LT04_SRB2'],
#               'toa_greens': ['LC08_TAB3', 'LE07_TAB2', 'LT05_TAB2', 'LT04_TAB2'],
              'blues': ['LC08_SRB2', 'LE07_SRB1', 'LT05_SRB1', 'LT04_SRB1'],
#               'toa_blues': ['LC08_TAB2', 'LE07_TAB1', 'LT05_TAB1', 'LT04_TAB1'],
              'nirs': ['LC08_SRB5', 'LE07_SRB4', 'LT05_SRB4', 'LT04_SRB4'],
#               'toa_nirs': ['LC08_TAB5', 'LE07_TAB4', 'LT05_TAB4', 'LT04_TAB4'],
              'swir1s': ['LC08_SRB6', 'LE07_SRB5', 'LT05_SRB5', 'LT04_SRB5'],
#               'toa_swir1s': ['LC08_TAB6', 'LE07_TAB5', 'LT05_TAB5', 'LT04_TAB5'],
              'swir2s': ['LC08_SRB7', 'LE07_SRB7', 'LT05_SRB7', 'LT04_SRB7'],
#               'toa_swir2s': ['LC08_TAB7', 'LE07_TAB7', 'LT05_TAB7', 'LT04_TAB7'],
              'thermals': ['LC08_BTB10', 'LE07_BTB6', 'LT05_BTB6', 'LT04_BTB6'],
              'qas': ['LC08_PIXELQA', 'LE07_PIXELQA', 'LT05_PIXELQA', 'LT04_PIXELQA']
              }

item_lookup = {'All Spectral Bands and Indices': ['blues', 'greens', 'reds', 'nirs', 'swir1s', 'swir2s',
                                                  'thermals', 'qas'],
               'All Spectral Bands': ['blues', 'greens', 'reds', 'nirs', 'swir1s', 'swir2s', 'thermals', 'qas'],

               'All Indices': ['blues', 'reds', 'nirs', 'swir1s', 'swir2s', 'qas'],

               'Blue': ['blues', 'qas'],
               'Green': ['greens', 'qas'],
               'Red': ['reds', 'qas'],
               'NIR': ['nirs', 'qas'],
               'SWIR-1': ['swir1s', 'qas'],
               'SWIR-2': ['swir2s', 'qas'],
               'Thermal': ['thermals', 'qas'],
               'NDVI': ['reds', 'nirs', 'qas'],
               'MSAVI': ['reds', 'nirs', 'qas'],
               'SAVI': ['reds', 'nirs', 'qas'],
               'EVI': ['blues', 'reds', 'nirs', 'qas'],
               'NDMI': ['nirs', 'swir1s', 'qas'],
               'NBR': ['nirs', 'swir2s', 'qas'],
               'NBR-2': ['swir1s', 'swir2s', 'qas']
               }

indices = ['ndvi', 'msavi', 'evi', 'savi', 'ndmi', 'nbr', 'nbr2']
spectrals = ['blues', 'greens', 'reds', 'nirs', 'swir1s', 'swir2s', 'thermals']

aliases = {'Blue': ['blues'],
           'Green': ['greens'],
           'Red': ['reds'],
           'NIR': ['nirs'],
           'SWIR-1': ['swir1s'],
           'SWIR-2': ['swir2s'],
           'Thermal': ['thermals'],
           'NDVI': ['ndvi'],
           'MSAVI': ['msavi'],
           'EVI': ['evi'],
           'SAVI': ['savi'],
           'NDMI': ['ndmi'],
           'NBR': ['nbr'],
           'NBR-2': ['nbr2'],
           'All Indices': indices,
           'All Spectral Bands': spectrals
           }

