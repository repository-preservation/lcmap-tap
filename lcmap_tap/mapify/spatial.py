"""
Functions handling spatial coordinates, and reading/writing rasters.
"""

import os
from functools import lru_cache
from typing import Tuple, List

from osgeo import gdal
import numpy as np

from mapify.app import cu_tileaff as _cu_tileaff
from mapify.app import conuswkt as _conuswkt


def create(path: str, rows: int, cols: int, affine: tuple,
           datatype: int, proj: str=_conuswkt, bands: int=1,
           ct: List[gdal.ColorTable]=None) -> gdal.Dataset:
    """
    Create a GeoTif and return the data set to work with.
    If the file exists at the given path, this will attempt to remove it.
    WARNING:
        ATTEMPTS TO REMOVE THE FILE IF IT ALREADY EXISTS

    Args:
        path: file path to create
        rows: number of rows
        cols: number of columns
        affine: gdal GeoTransform tuple
        datatype: gdal data type for the file
        proj: projection well known text
        bands: number of bands to create
        ct: list of gdal color tables to apply to the bands

    Returns:
        gdal data set for the file
    """
    if os.path.exists(path):
        os.remove(path)

    ds = (gdal
          .GetDriverByName('GTiff')
          .Create(path, cols, rows, bands, datatype))

    ds.SetGeoTransform(affine)
    ds.SetProjection(proj)

    if ct:
        for idx, table in enumerate(ct):
            ds.GetRasterBand(idx + 1).SetColorTable(table)

    return ds


def update(path: str) -> gdal.Dataset:
    """
    Open a raster file for editing

    Args:
        path: file path

    Returns:
        gdal data set for editing
    """
    return gdal.Open(path, gdal.GA_Update)


def write(ds: gdal.Dataset, data: np.ndarray,
          col_off: int=0, row_off: int=0, band: int=1) -> int:
    """
    Write a chip of data to the given data set and band.

    Args:
        ds: gdal data set to write to
        data: data to write
        col_off: column offset to start writing data
        row_off: row offset to start writing data
        band: which band if it is a tiff-stack

    Returns:
        0 if successfull
    """
    return ds.GetRasterBand(band).WriteArray(data, col_off, row_off)


def writep(path: str, data: np.ndarray,
           col_off: int=0, row_off: int=0, band: int=1) -> None:
    """
    Write some data to the given file.

    Args:
        path: file path to write to
        data: data to write
        col_off: column offset to start writing data
        row_off: row offset to start writing data
        band: which band if it is a tiff-stack

    Returns:
        
    """
    ds = update(path)
    ds.GetRasterBand(band).WriteArray(data, col_off, row_off)
    ds = None
    return


def readrc(path: str, col_off: int=0, row_off: int=0, 
           num_cols: int=None, num_rows: int=None, band: int=1) -> np.ndarray:
    """
    Read data from a raster file.

    Args:
        path: file path to read from
        col_off: column offset to start reading data
        row_off: row offset to start reading data
        num_cols: how many columns to read
        num_rows: how man rows to read
        band: which band if it is a tiff-stack

    Returns:
        ndarray of data
    """
    ds = gdal.Open(path, gdal.GA_ReadOnly)
    arr = ds.GetRasterBand(band).ReadAsArray(col_off, row_off, num_cols, num_rows)
    ds = None
    return arr


def readxy(path: str, x_off: float, y_off: float, 
           num_cols: int=None, num_rows: int=None, band: int=1) -> np.ndarray:
    """
    Read data from a raster file, offsets based on geospatial coordinates that should match
    the raster's projection space.

    Args:
        path: file path to read from
        x_off: projected x coordinate offset to start reading data
        y_off: projected y coordinate offset to start reading data
        num_cols: how many columns to read
        num_rows: how man rows to read
        band: which band if it is a tiff-stack

    Returns:
        ndarray of data
    """
    ds = gdal.Open(path, gdal.GA_ReadOnly)
    aff = ds.GetGeoTransform()
    row_off, col_off = transform_geo(x_off, y_off, aff)
    arr = ds.GetRasterBand(band).ReadAsArray(col_off, row_off, num_cols, num_rows)
    ds = None
    return arr


@lru_cache()
def buildaff(ulx: float, uly: float, pixelres: float) -> tuple:
    """
    Build a gdal GeoTransform tuple

    Args:
        ulx: projected geo-spatial upper-left x reference coord
        uly: projected geo-spatial upper-left y reference coord
        pixelres: pixel resolution

    Returns:
        affine tuple
    """
    return ulx, pixelres, 0, uly, 0, -pixelres


@lru_cache()
def transform_geo(x: float, y: float, affine: tuple) -> Tuple[int, int]:
    """
    Perform the affine transformation from a x/y coordinate to row/col
    space.

    Args:
        x: projected geo-spatial x coord
        y: projected geo-spatial y coord
        affine: gdal GeoTransform tuple

    Returns:
        containing pixel row/col
    """
    col = (x - affine[0] - affine[3] * affine[2]) / affine[1]
    row = (y - affine[3] - affine[0] * affine[4]) / affine[5]

    return int(row), int(col)


@lru_cache()
def transform_rc(row: int, col: int, affine: tuple) -> Tuple[int, int]:
    """
    Perform the affine transformation from a row/col coordinate to projected x/y
    space.

    Args:
        row: pixel/array row number
        col: pixel/array column number
        affine: gdal GeoTransform tuple

    Returns:
        x/y coordinate
    """
    x = affine[0] + col * affine[1] + row * affine[2]
    y = affine[3] + col * affine[4] + row * affine[5]

    return x, y


@lru_cache()
def determine_hv(x: float, y: float, affine: tuple=_cu_tileaff) -> Tuple[int, int]:
    """
    Determine the ARD tile H/V that contains the given coordinate.

    Args:
        x: projected geo-spatial x coord
        y: projected geo-spatial y coord
        affine: gdal GeoTransform tuple

    Returns:
        ARD tile h/v
    """
    return transform_geo(x, y, affine)[::-1]
