"""This plotting tool is being developed to provide visualization and analysis support of LCMAP products generated
with PyCCD. Multi-spectral time-series models and calculated indices at a specified point location are available for
plotting. The plots by default include all ARD observations, PyCCD time-segment model-fits, time-segment attributes
including start, end, and break dates, and datelines representing annual increments on day 1 of each year. The tool
generates an interactive figure that contains the specified bands and indices, with each of these being drawn on its
own subplot within the figure. Interactive capabilities of the figure include zooming-in to an area of interest,
returning to the default zoom level, adjusting subplot-specific x and y axis ranges, adjusting subplot sizes,
and saving the current figure. For each subplot the x-axis represents the dates of the time series, and the y-axis
represents that subplot’s band values. Both axes are rescaled and relabeled on zoom events allowing for finer
resolution at smaller scales. Each subplot has interactive picking within the plotting area and within the legend.
Left-clicking on observation points in the subplot displays the information associated with that observation in a
window on the GUI. Left-clicking on items in the legend turns on/off those items in the subplot. Button controls on
the GUI allow for generating and displaying the plot, clearing the list of clicked observations, saving the figure in
its current state to a .PNG image file, and exiting out of the tool. """

from setuptools import setup, find_packages

setup(
    name='lcmap_tap',

    version='0.3.3',

    packages=find_packages(),

    install_requires=[
        'matplotlib',
        'numpy',
        'gdal',
        'pyyaml',
        'cytoolz',
        'cython',
        'requests',
        'lcmap-merlin'
    ],

    entry_points={'gui_scripts': ['lcmap_tap = lcmap_tap.__main__:main']},

    python_requires='>=3.6',

    include_package_data = True,

    author='Daniel Zelenak',

    author_email='dzelenak@contractor.usgs.gov',

    long_description=__doc__,

    description='A data visualization tool for PyCCD time-series model results and Landsat ARD',

    license='Public Domain',

    url='https://github.com/USGS-EROS/lcmap-tap'
)
