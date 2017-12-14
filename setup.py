from setuptools import setup, find_packages

setup(
    name='pyccdardplot',
    version='1.0.0',
    packages=find_packages(),
    scripts=['main.py'],
    install_requires=[
        'matplotlib>=2',
        'PyQt>=5.6.0',
        'numpy>=1.11',
        'gdal>=2.0.0',
        'libgdal>=2.0.0'
    ],
    dependency_links=['git https://github.com/conda-forge/gdal-feedstock'],
    python_requires='>=3.4',
    author='Daniel Zelenak',
    author_email='daniel.zelenak.ctr@usgs.gov',
    description='Plotting tool for displaying PyCCD time-series model results and Landsat-ARD observations',
    license='',
    url='https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool'
)
