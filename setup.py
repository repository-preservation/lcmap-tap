"""The Time Series Analysis and Plotting (TAP) tool is being developed to provide visualization and analysis support of
LCMAP products generated with PyCCD.  Multispectral time-series models and calculated indices at a specified point
location are available for plotting.  The plots by default include all ARD observations, PyCCD time-segment model-fits,
time-segment attributes including start, end, and break dates, and datelines representing annual increments on day 1 of
each year.  The tool generates an interactive Matplotlib figure that displays plots for bands and indices selected by
the user via the GUI.
"""

from setuptools import setup, find_packages

setup(
    name='lcmap_tap',

    version='0.1.0',

    packages=find_packages(),

    install_requires=[
        'matplotlib',
        'PyQt5',
        'numpy',
        'gdal'
    ],

    entry_points={'gui_scripts': ['lcmap_tap = lcmap_tap.__main__:main']},

    dependency_links=['https://github.com/conda-forge/gdal-feedstock/'],

    python_requires='>=3.5',

    author='Daniel Zelenak',

    author_email='daniel.zelenak.ctr@usgs.gov',

    long_description=__doc__,

    description='A plotting tool for displaying PyCCD time-series model results and Landsat-ARD observations',

    license='Public Domain',

    url='https://github.com/danzelenak-usgs/LCMAP_TAP'
)
