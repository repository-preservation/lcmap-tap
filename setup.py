"""I'm still working on figuring out exactly how to use setuptools to make the plotting tool more portable.
Under 'install_requires I have pyqt commented out because I kept getting an error that the version couldn't
be satisfied.  I also keep going back and forth between having an entry_point and a script (main.py).  I'm still
not sure exactly how this works.  The way the project is structured makes me believe that defining the script is
the way to go..."""

from setuptools import setup, find_packages

setup(
    name='pyccd_plotter',
    version='1.0.0',
    packages=find_packages(),
    # scripts=['pyccd_plotter/main'],
    install_requires=[
        'matplotlib',
        # 'pyqt',
        'numpy',
        'gdal'
    ],
    dependency_links=['git https://github.com/conda-forge/gdal-feedstock'],
    python_requires='>=3.4',
    author='Daniel Zelenak',
    author_email='daniel.zelenak.ctr@usgs.gov',
    description='Plotting tool for displaying PyCCD time-series model results and Landsat-ARD observations',
    license='',
    url='https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool'
)
