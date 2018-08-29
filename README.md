# Time Series Analysis and Plotting (TAP) Tool

#### Abstract:

This plotting tool is being developed to provide visualization and
analysis support of LCMAP products generated with PyCCD.  Additionally, it provides 
plotting of time-series ARD.  Multi-spectral
time-series models and calculated indices at a specified point (i.e. pixel) location
can be plotted.  The GUI provides customization for which components are included
on the plot.  The default setting is to include all ARD observations, PyCCD time-segment
model-fits, time-segment attributes including start, end, and break
dates, and datelines representing annual increments on day 1 (January 1) of each
year.  The tool leverages [matplotlib](https://matplotlib.org/) and 
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
highlighted by a magenta boundary along the pixel extent.  Left-clicking elsewhere
on the ARD viewer will cause a new plot to be automatically generated for that 
pixel location.  Button controls on
the GUI allow for generating and displaying the plot, clearing the
list of clicked observations, saving the figure in its current state
to a .PNG image file, and exiting out of the tool.

## Installation
These instructions work for both Windows and Linux systems.

lcmap_tap has been installed and run successfully on Windows 7 & 10, and CentOS Linux (version 7).

The current version of the tool (0.4.0) was developed using python 3.6

##

##### System Requirements:

python == 3.6

matplotlib == 2.2.2

PyQt5 >= 5.6

numpy == 1.14.5

GDAL == 2.2.2

pyyaml

cytoolz

cython

requests

lcmap-merlin == 2.2.0
#

The tool also currently requires:

* All available ARD observations stored in tarballs, *see* [EarthExplorer](https://earthexplorer.usgs.gov/).
  *  A Python script that uses [EarthExplorer API](https://earthexplorer.usgs.gov/inventory/documentation) (requires account log in) for downloading ARD is [here](https://github.com/danzelenak-usgs/Landsat-ARD-Tools/blob/master/download_ard_edit.py).
* JSON files produced by [PyCCD](https://github.com/USGS-EROS/lcmap-pyccd).
      

##### Note:
It is recommended to use an [Anaconda](https://www.anaconda.com/) virtual environment for installing
the LCMAP TAP tool and its dependencies.


* Install Anaconda or Miniconda
  * Download [here](https://www.anaconda.com/download/)
* Create a virtual environment with python 3.6:
    ```bash
    $conda create -n <env-name> python=3.6
    ```
#### Installing Python Dependencies
[GDAL](http://www.gdal.org/index.html) and the other required python packages are easily installed with the 'conda install' command.

* From the command line, activate the virtual environment:
    
    Windows |Linux
    --------|-------
    $activate env-name |$source activate env-name
    
* Install the required packages

    **Windows and Linux**
    ```bash
    (env-name)$conda install numpy gdal matplotlib pyyaml cytoolz requests cython
    The following NEW packages will be INSTALLED:
    ...
    Proceed ([y]/n)? y
    ```
* Install lcmap-merlin
    ```
    (env-name)$pip install lcmap-merlin --trusted-host pypi.org --trusted-host python.pypi.org --trusted-host files.pythonhosted.org
    ```

#### Retrieving and installing LCMAP_TAP code 

* [Download](https://github.com/USGS-EROS/lcmap-tap/archive/master.zip) lcmap_tap as a zipped folder.

* Unzip, then using the command prompt enter into the unzipped folder:
    ```bash
    $cd <some-path-to-the-target-folder>\LCMAP_TAP\
    ```
* Install the plotting tool by running 'pip install' in the currently active
virtual env
    ```bash
    (env-name)$ pip install .
    ```
## Run the Tool

Once installed, lcmap_tap can be executed directly from the command line:
```bash
$activate env-name
(env-name)$lcmap_tap
```


