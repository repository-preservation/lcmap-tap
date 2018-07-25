
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
