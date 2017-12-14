# PyCCD-Plotting-Tool

#### Abstract:

This plotting tool was built to aid in the analysis of LCMAP products
generated with PyCCD.  Multispectral time series models and calculated
indices at a specified point location are available for plotting.  The
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

#### Installation

Clone or download the GitHub repository

'''
$cd \<working-dir>
'''

'''
$git clone https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool.git
'''

If git isn't installed:

Go to https://github.com/danzelenak-usgs/PyCCD-Plotting-Tool

Click "Clone or Download", then click "Download Zip"

Navigate to the downloaded archive,  un-package it and move the folder
to a desired working location.

Install Anaconda or Miniconda and create a virtual environment

Download link: https://www.anaconda.com/download/

##### Option A

Create a virtual environment from the provided spec-file.txt
if on a win-64 system.

$conda create -n \<env-name> --file file-spec.txt

##### Option B

Manually create a virtual environment with the following
commands:

$conda create -n \<env-name> python=3.6

$activate \<env-name>

$conda install gdal -c conda-forge

$conda install matplotlib

Installing these packages will get the other requirements of Numpy and
PyQt installed automatically.

#### Run the Tool

Activate the conda environment if not already

$activate \<env-name>

Navigate to the tool's base directory (it should contain the modules
i.e. subfolders and main.py)

$cd \<some-location>

$python main.py
