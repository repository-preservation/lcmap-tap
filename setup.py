from setuptools import setup

setup(
    name='PyCCD-Plotting-Tool',
    version='1.0.0',
    packages=['Controls', 'PlotFrame', 'Plotting', 'RetrieveData', 'UserInterface'],
    scripts=['main.py'],
    url='https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool',
    license='',
    author='Daniel Zelenak',
    author_email='daniel.zelenak.ctr@usgs.gov',
    description='Plotting tool for PyCCD results and ARD observations',
    install_requires=[
            'matplotlib>=2',
            'PyQt==5.6.0',
            'numpy>=1.11',
            'gdal>=2.1'
    ]
)
