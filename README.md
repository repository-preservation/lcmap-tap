# Time Series Analysis and Plotting (TAP) Tool

***Warning:  This branch of the TAP tool is under active development and is not considered stable.  It may contain bugs or not function at all.***
##
#### Abstract:

The TAP tool is being developed to provide visualization and
analysis of time-series ARD and LCMAP products.  Multi-spectral
time-series models, calculated band indices, and Landsat ARD observations at a specified point (i.e. pixel) location
can be plotted.  The tool leverages [matplotlib](https://matplotlib.org/) and 
[Qt](https://www.qt.io/) to generate an interactive figure that contains the
specified bands and indices, with each of these being drawn on its
own subplot within the figure.   Interactive capabilities of the figure
include zooming to an area of interest, returning to the default
zoom level, adjusting subplot-specific x and y axis ranges, adjusting
subplot sizes, and saving the current figure.  For each subplot the
x-axis represents the dates of the time series, and the y-axis
represents that subplot’s band values.  Each subplot has interactive picking within the plotting area
and within the legend.  Left-clicking on items in the
legend turns on/off those items in the subplot.  Left-clicking on observation points
in the subplot displays the information associated with that
observation in a window on the GUI.  Then, clicking on the selected observation
in this window will open a new display showing the ARD observation.  This ARD-viewer
provides additional options for selecting different band combinations, along with interactive
zooming with the mouse scroll-wheel.  The pixel featured in the plot will also be
highlighted by a yellow boundary approximating the pixel extent.  Left-clicking elsewhere
on the ARD viewer will cause a new plot to be automatically generated for that 
pixel location.  Button controls on
the GUI allow for generating and displaying the plot, clearing the
list of clicked observations, saving the figure in its current state
to a .PNG image file, and exiting out of the tool.  The currently plotted ARD observations can be exported
to a .CSV file for further analysis.

## Installation
These instructions work for both Windows and Linux systems.

lcmap_tap has been installed and tested successfully on Windows 7 & 10, and CentOS Linux (version 7).

This version of the tool (1.0.0-workshop) was developed for the LCMAP workshop sessions Nov. 6-8, 2018 at USGS EROS.

##

##### System Requirements:

python >= 3.6

PyQt5 == 5.10.1

matplotlib >= 2.2.2

numpy

GDAL

pandas

pyyaml

cytoolz

cython

requests

[lcmap-merlin](https://pypi.org/project/lcmap-merlin/)
#

The tool also currently requires:
* JSON files produced by [PyCCD](https://github.com/USGS-EROS/lcmap-pyccd).
* A configuration .YAML file containing the URL which will be used to request ARD observations.  These are
used for both plotting and displaying the ARD imagery.
      

##### Note:
It is recommended to use an [Anaconda](https://www.anaconda.com/) virtual environment since it provides an easier 
method of installation for GDAL.  Otherwise, information for installing GDAL manually can be found [here](https://www.gdal.org/index.html).


* Install Anaconda or Miniconda
  * Download [here](https://www.anaconda.com/download/)
* Create a virtual environment with python 3.6, include the following dependencies in the environment creation:
  * __GDAL__
  * __cython__
  * __cytoolz__
  * __numpy__
  * __pandas__
  
  ```bash
  $conda create -n <env-name> python=3.6 gdal cython cytoolz numpy pandas
  The following NEW packages will be INSTALLED:
  ...
  Proceed ([y]/n)? y

  ```

* Download the TAP source code [here](https://github.com/USGS-EROS/lcmap-tap/archive/workshop.zip) and extract the
zipped folder.  From the command line, cd into the extracted folder.
#### Installing TAP

* From the command line, activate the virtual environment (must use source if using bash)
        
* Use pip to install TAP and the remaining dependencies

    **Windows and Linux**
    ```bash
    pip install --trusted-host pypi.org --trusted-host python.pypi.org --trusted-host files.pythonhosted.org .
    ...

    ```

## Run the Tool

Once installed, lcmap_tap can be executed directly from the command line if the virtual environment 
is activated:
```bash
$activate env-name
$lcmap_tap
```
