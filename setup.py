from setuptools import setup, find_packages

setup(
    name='pyccd_plotter',
    version='1.0.0',
    packages=find_packages(),
    # scripts=['main.py'],
    install_requires=[
        'matplotlib',
        'pyqt',
        'numpy',
        'gdal'
    ],
    dependency_links=['git https://github.com/conda-forge/gdal-feedstock'],
    python_requires='>=3.4',
    entry_point={
        'gui_scripts': ['run=pyccd-plotter.main']
    },
    author='Daniel Zelenak',
    author_email='daniel.zelenak.ctr@usgs.gov',
    description='Plotting tool for displaying PyCCD time-series model results and Landsat-ARD observations',
    license='',
    url='https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool'
)
