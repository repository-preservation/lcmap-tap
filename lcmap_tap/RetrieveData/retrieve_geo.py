"""Generate useful geographic information for tile, chip, and pixel granularities"""

from lcmap_tap.logger import exc_handler
from lcmap_tap.Auxiliary import projections
from lcmap_tap.RetrieveData import GeoExtent, GeoAffine, GeoCoordinate, RowColumn, CONUS_EXTENT
import sys
from typing import Tuple
import re
from osgeo import ogr, osr

sys.excepthook = exc_handler


class GeoInfo:
    """
    Generate and retain useful geographic information relating to the tile, chip, and pixel
    """

    def __init__(self, x: str, y: str, units: str="meters"):
        """

        Args:
            x: X-coordinate in specific units
            y: Y-coordinate in specific units
            units: Coordinate units, either projected CONUS AEA meters or geographic WGS84 lat/long

        """
        if units == "meters":
            # <GeoCoordinate> Containing the input coordinate in meters
            self.coord = self.get_geocoordinate(xstring=x, ystring=y)

            # <GeoCoordinate> Containing the input coordinate in geographic lat/lon
            self.geo_coord = self.unit_conversion(coord=self.coord)

        else:
            # <GeoCoordinate> Containing the input coordinate in geographic lat/lon
            self.geo_coord = self.get_geocoordinate(xstring=x, ystring=y)

            # <GeoCoordinate> Containing the input coordinate in meters
            self.coord = self.unit_conversion(coord=self.geo_coord, src="lat/long", dest="meters")

            # Convert the meters to integer format
            self.coord = GeoCoordinate(x=int(self.coord.x), y=int(self.coord.y))

        self.CONUS_EXTENT = CONUS_EXTENT

        self.H, self.V = self.get_hv(x=self.coord.x, y=self.coord.y)

        self.tile = "h{:02}v{:02}".format(self.H, self.V)

        self.EXTENT, self.PIXEL_AFFINE = self.geospatial_hv(loc=self.CONUS_EXTENT,
                                                            h=self.H,
                                                            v=self.V)

        self.TILE_CHIP_AFFINE = GeoAffine(ul_x=self.PIXEL_AFFINE.ul_x,
                                          x_res=3000,
                                          rot_1=0,
                                          ul_y=self.PIXEL_AFFINE.ul_y,
                                          rot_2=0,
                                          y_res=-3000)

        self.tile_pixel_rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, self.coord)

        self.pixel_coord_ul = self.rowcol_to_geo(self.PIXEL_AFFINE, self.tile_pixel_rowcol)

        self.tile_chip_rowcol = self.geo_to_rowcol(self.TILE_CHIP_AFFINE, self.coord)

        self.chip_coord_ul = self.rowcol_to_geo(self.TILE_CHIP_AFFINE, self.tile_chip_rowcol)

        self.PIXEL_CHIP_AFFINE = GeoAffine(ul_x=self.chip_coord_ul.x,
                                           x_res=30,
                                           rot_1=0,
                                           ul_y=self.chip_coord_ul.y,
                                           rot_2=0,
                                           y_res=-30)

        self.CHIP_EXTENT = self.geospatial_chip(loc=self.EXTENT,
                                                column=self.tile_chip_rowcol.column,
                                                row=self.tile_chip_rowcol.row)

        self.chip_pixel_rowcol = self.geo_to_rowcol(self.PIXEL_CHIP_AFFINE, self.pixel_coord_ul)

        self.rowcol = self.geo_to_rowcol(self.PIXEL_AFFINE, self.coord)

    @staticmethod
    def get_hv(x: GeoCoordinate.x,
               y: GeoCoordinate.y,
               x_min: GeoExtent.x_min = CONUS_EXTENT.x_min,
               y_max: GeoExtent.y_max = CONUS_EXTENT.y_max,
               base: int = 150000
               ) -> Tuple[int, int]:
        """
        Determine the H and V designations from the entered geo-coordinates

        Args:
            x: GeoCoordinate.x
            y: GeoCoordinate.y
            x_min: Use the CONUS_EXTENT.x_min
            y_max: Use the CONUS_EXTENT.y_max
            base:

        Returns:
            Tuple containing the H and V as integers

        """
        h = int((x - x_min) / base)

        v = int((y_max - y) / base)

        return h, v

    @staticmethod
    def geospatial_hv(loc: GeoExtent, h: int, v: int,
                      block_length: int=5000, res: int=30) -> Tuple[GeoExtent, GeoAffine]:
        """
        Return the tile extent and affine

        Args:
            loc: The larger encompassing extent (i.e. CONUS) containing xmin, xmax, ymin, ymax values
            h: H designation
            v: V designation
            block_length: The length of one side of a grid block
            res: The length of one side of a pixel

        Returns:
            The extent and affine transformation for an ARD tile

        """
        xmin = loc.x_min + h * block_length * res
        xmax = loc.x_min + h * block_length * res + block_length * res
        ymax = loc.y_max - v * block_length * res
        ymin = loc.y_max - v * block_length * res - block_length * res

        return (GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin),
                GeoAffine(ul_x=xmin, x_res=res, rot_1=0, ul_y=ymax, rot_2=0, y_res=-res))

    @staticmethod
    def geospatial_chip(loc: GeoExtent, column: int, row: int,
                        chip_length: int=100, res: int=30) -> Tuple[GeoExtent, GeoAffine]:
        """
        Return the chip extent and affine

        Args:
            loc: Containing xmin, xmax, ymin, ymax values
            column: The chip column within an ARD tile
            row: The chip row within an ARD tile
            chip_length: The length of one side of a chip
            res: The length of one side of a pixel

        Returns:
            The extent and affine transformation for a chip

        """
        xmin = loc.x_min + column * chip_length * res
        xmax = loc.x_min + column * chip_length * res + chip_length * res
        ymax = loc.y_max - row * chip_length * res
        ymin = loc.y_max - row * chip_length * res - chip_length * res

        return (GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin),
                GeoAffine(ul_x=xmin, x_res=res, rot_1=0, ul_y=ymax, rot_2=0, y_res=-res))

    @staticmethod
    def get_geocoordinate(xstring: str, ystring: str) -> GeoCoordinate:
        """
        Create GeoCoordinate type to hold the x and y coordinate values as type float

        Args:
            xstring: The user-input x-coordinate
            ystring: The user-input y-coordinate

        Returns:
            A GeoCoordinate with x and y attributes

        """
        if isinstance(xstring, int):
            xstring = str(xstring)

        if isinstance(ystring, int):
            ystring = str(ystring)

        def str_to_float(split: list):
            try:
                return float(re.sub(",", "", split[0]))

            # This occurs when entering a negative value; cannot convert "-" to float
            except (ValueError, IndexError):
                return 0.00

        xpieces = xstring.split()
        ypieces = ystring.split()

        return GeoCoordinate(x=str_to_float(xpieces),
                             y=str_to_float(ypieces))

    @staticmethod
    def unit_conversion(coord: GeoCoordinate, src: str="meters", dest: str="lat/long") -> GeoCoordinate:
        """
        Convert between different units for a given coordinate system
        projected units = meters
        geographic units = dec. deg.

        Args:
            src: Input units
            dest: Output units
            coord: GeoCoordinate with x and y attributes

        Choices:
            ["proj": "meters", "geog": "lat/long"]

        Returns:
            GeoCoordinate with x and y attributes

        """
        units = {"meters": projections.AEA_WKT,
                 "lat/long": projections.WGS_84_WKT}

        in_srs = osr.SpatialReference()
        in_srs.ImportFromWkt(units[src])

        out_srs = osr.SpatialReference()
        out_srs.ImportFromWkt(units[dest])

        point = ogr.Geometry(ogr.wkbPoint)

        point.AddPoint(coord.x, coord.y)

        transform = osr.CoordinateTransformation(in_srs, out_srs)

        point.Transform(transform)

        return GeoCoordinate(x=point.GetX(),
                             y=point.GetY())

    @staticmethod
    def geo_to_rowcol(affine: GeoAffine, coord: GeoCoordinate) -> RowColumn:
        """
        Transform geo-coordinate to row/col given a reference affine

        Yline = (Ygeo - GT(3) - Xpixel*GT(4)) / GT(5)
        Xpixel = (Xgeo - GT(0) - Yline*GT(2)) / GT(1)

        Args:
            affine: The affine transformation parameters
            coord: GeoCoordinate with x and y attributes

        Returns:
            The row and column within the array of the input coordinate

        """

        row = (coord.y - affine.ul_y - affine.ul_x * affine.rot_2) / affine.y_res
        col = (coord.x - affine.ul_x - affine.ul_y * affine.rot_1) / affine.x_res

        return RowColumn(row=int(row), column=int(col))

    @staticmethod
    def rowcol_to_geo(affine: GeoAffine, rowcol: RowColumn) -> GeoCoordinate:
        """
        Transform a row/col into a geospatial coordinate given reference affine.

        Xgeo = GT(0) + Xpixel*GT(1) + Yline*GT(2)
        Ygeo = GT(3) + Xpixel*GT(4) + Yline*GT(5)

        Args:
            affine: The affine transformation parameters
            rowcol: The row and column within the array to convert to coordinates

        Returns:
            The geographic coordinate of the location in the array

        """
        x = affine.ul_x + rowcol.column * affine.x_res + rowcol.row * affine.rot_1
        y = affine.ul_y + rowcol.column * affine.rot_2 + rowcol.row * affine.y_res

        return GeoCoordinate(x=x, y=y)

    @staticmethod
    def get_affine(ulx, uly, size=30):
        """
        Source: Kelcy Smith
        Return a GDAL affine transformation for a given upper left coordinate

        Args:
            ulx (int): x-coordinate for the upper left location of the extent
            uly (int): y-coordinate for the uppef left location of the extent
            size (int): The resolution, default is 30 meters

        Returns:
            GeoAffine ["ul_x", "x_res", "rot_1", "ul_y", "rot_2", "y_res"]

        """
        return GeoAffine(ul_x=ulx, x_res=size, rot_1=0, ul_y=uly, rot_2=0, y_res=-size)

    @staticmethod
    def find_ul(coord_ls):
        """
        Source: Kelcy Smith
        Helper function to identify the upper left coordinate from a list of coordinates.
        """
        xs, ys = zip(*coord_ls)

        return GeoCoordinate(x=min(xs), y=max(ys))

    @staticmethod
    def find_lr(coord_ls):
        """
        Source: Kelcy Smith
        Helper function to identify the lower left coordinate from a list of coordinates.
        Note this is not the LR of the extent.
        """
        xs, ys = zip(*coord_ls)

        return GeoCoordinate(x=max(xs), y=min(ys))
