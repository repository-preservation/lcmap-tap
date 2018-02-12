# Time Series Analysis and Plotting (TAP) Tool

#### Abstract:

This plotting tool is being developed to provide visualization and
analysis support of LCMAP products generated with PyCCD.  Multispectral
time-series models and calculated indices at a specified point location
are available for plotting.  The
plots by default include all ARD observations, PyCCD time-segment
model-fits, time-segment attributes including start, end, and break
dates, and datelines representing annual increments on day 1 of each
year.  The tool generates an interactive figure that contains the
specified bands and indices, with each of these being drawn on its
own subplot within the figure.   Interactive capabilities of the figure
include zooming-in to an area of interest, returning to the default
zoom level, adjusting subplot-specific x and y axis ranges, adjusting
subplot sizes, and saving the current figure.  For each subplot the
x-axis represents the dates of the time series, and the y-axis
represents that subplot’s band values.  Both axes are rescaled and
relabeled on zoom events allowing for finer resolution at smaller
scales.  Each subplot has interactive picking within the plotting area
and within the legend.  Left-clicking on observation points
in the subplot displays the information associated with that
observation in a window on the GUI.  Left-clicking on items in the
legend turns on/off those items in the subplot.  Button controls on
the GUI allow for generating and displaying the plot, clearing the
list of clicked observations, saving the figure in its current state
to a .PNG image file, and exiting out of the tool.

## Installing

##### System Requirements:

python >= 3.4

Matplotlib

PyQt5

Numpy

GDAL
#

The tool currently requires cache files generated by Chris Holden's YATSM (https://github.com/ceholden/yatsm)
and JSON files produced by PyCCD (https://github.com/USGS-EROS/lcmap-pyccd)

##### Note:
It is recommended to use an Anaconda virtual environment for installing
the LCMAP TAP tool and its dependencies.


* Install Anaconda or Miniconda
  * Download link: https://www.anaconda.com/download/
* Create a virtual environment with python 3.6
    ```bash
    $conda create -n <env-name> python=3.6
    ```

GDAL is a requirement and it is easiest to install using conda:

* First install the binaries if you don't have them, they can be found here:
    * http://www.gisinternals.com/release.php
* Activate the virtual environment and install the GDAL python bindings
    ```bash
    $activate <env-name>
    (env-name)$conda install gdal
    ```
* Enter into a working directory, clone or download the GitHub
repository into this directory
    ```bash
    $cd \<working-dir>
    $git clone https://github.com/danzelenak-usgs/LCMAP_TAP.git
    ```
* Enter into the cloned repository folder, or unzip and enter into the
downloaded repository folder

    ```bash
    $cd LCMAP_TAP\
    ```
* Install the plotting tool using setup.py in the currently active
virtual env
    ```bash
    (env-name)$ python setup.py install
    ```
    This should install the remaining dependencies along with the tool
itself.  If there are any errors with installing the dependencies
automatically, then use conda to do so:

    ```bash
    (env-name)$conda install matplotlib
    ```

Installing matplotlib like this will automatically install the remaining
dependencies


## Run the Tool

* Option A - From the command line, with the virtual environment activated:
    ```bash
    $activate <env-name>
    (env-name)$lcmap_tap
    ```
* Option B - Use the pyccd_plotter.exe
    * located in <python_path>/Scripts/lcmap_tap.exe


