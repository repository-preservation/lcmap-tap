"""

set the controls.py for the heart of the sun

"""

import datetime as dt
import os
import sys
import time
import traceback

import matplotlib
import matplotlib.pyplot as plt

try:
    import ogr
    import osr

    gdal_found = True

except ImportError:
    import ogr
    import osr

    gdal_found = False

    # TODO Enable logging
    print("GDAL not found, can't generate point shapefile.")

# Tell matplotlib to use the QT5Agg Backend
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QMainWindow, QFileDialog

# Import the main GUI built in QTDesigner, compiled into python with pyuic5.bat
from lcmap_tap.UserInterface import ui_main

# Import the CCDReader class which retrieves json and cache data
from lcmap_tap.RetrieveData.retrieve_data import CCDReader

# Import the PlotWindow class defined in the plotwindow.py module
from lcmap_tap.PlotFrame.plotwindow import PlotWindow

from lcmap_tap.Plotting import make_plots

from lcmap_tap.RetrieveData import ard_info

from lcmap_tap.Auxiliary import projections

from lcmap_tap.Visualization.ard_viewer_qpixelmap import ARDViewerX


class MainControls(QMainWindow):
    def __init__(self):

        super(MainControls, self).__init__()

        # TODO Add widget for ARD
        self.ard_directory = r"Z:\bulk\sites\ard_source\production"

        self.extracted_data = None
        self.plot_window = None
        self.ard_specs = None
        self.ard = None
        self.fig = None

        # Create an instance of a class that builds the user-interface, created in QT Designer and compiled with pyuic5
        self.ui = ui_main.Ui_TAPTool()

        # Call the method that adds all of the widgets to the GUI
        self.ui.setupUi(self)

        self.defaults()

        self.connect_widgets()

        self.init_ui()

    def init_ui(self):
        """
        Show the user interface
        :return:
        """
        self.show()

    def defaults(self):
        """
        Set some defaults

        Returns:
            None
        """
        self.ui.radio_meters.setChecked(True)

    def connect_widgets(self):
        """
        Connect the various widgets to the methods they interact with
        Returns:
            None
        """
        # *** some temporary default values to make testing easier ***
        self.ui.browseoutputline.setText(r"D:\Plot_Outputs\3.30.2018")
        self.ui.browsejsonline.setText(r"Z:\bulk\tiles\h03v02\change\2017.08.18\json")
        self.ui.browsecacheline.setText(r"Z:\bulk\cache\h03v02")
        self.ui.xline.setText("-2000417")
        self.ui.yline.setText("3004111")

        self.check_values()

        self.ui.radio_meters.setChecked(True)

        # *** Connect the various widgets to the methods they interact with ***
        self.ui.browsecachebutton.clicked.connect(self.browsecache)

        self.ui.browsejsonbutton.clicked.connect(self.browsejson)

        self.ui.browseoutputbutton.clicked.connect(self.browseoutput)

        self.ui.browsecacheline.textChanged.connect(self.check_values)

        self.ui.browsejsonline.textChanged.connect(self.check_values)

        self.ui.xline.textChanged.connect(self.check_values)

        self.ui.yline.textChanged.connect(self.check_values)

        self.ui.browseoutputline.textChanged.connect(self.check_values)

        self.ui.plotbutton.clicked.connect(self.plot)

        self.ui.clearpushButton.clicked.connect(self.clear)

        self.ui.savefigpushButton.clicked.connect(self.save_fig)

        self.ui.exitbutton.clicked.connect(self.exit_plot)

        self.ui.clicked_listWidget.itemClicked.connect(self.show_ard)

        return None

    def clear(self):
        """
        Clear the observations window
        :return:
        """
        self.ui.clicked_listWidget.clear()

    @staticmethod
    def get_time():
        """
        Return the current time stamp

        Returns:
            A formatted string containing the current date and time

        """
        return time.strftime("%Y%m%d-%I%M%S")

    def fname_generator(self, ext=".png"):
        """
        Generate a string for an output file
        Args:
            ext: <str> The output file extension, default is .png
        Returns:
            <str> The full path to the output file name
        """
        return "{outdir}{sep}H{h}V{v}_{xy}_{t}{ext}".format(outdir=self.ui.browseoutputline.text(),
                                                            sep=os.sep,
                                                            h=self.extracted_data.geo_info.H,
                                                            v=self.extracted_data.geo_info.V,
                                                            xy=self.ui.xline.text() + "_" + self.ui.yline.text(),
                                                            t=self.get_time(),
                                                            ext=ext)

    def save_fig(self):
        """
        Save the current matplotlib figure to a PNG file
        Returns:
            None
        """
        if not os.path.exists(self.ui.browseoutputline.text()):
            os.makedirs(self.ui.browseoutputline.text())

        fname = self.fname_generator()

        # Overwrite the .png if it already exists
        if os.path.exists(fname):
            try:
                os.remove(fname)

            except IOError:
                # TODO Enable logging
                return None

        plt.savefig(fname, bbox_inches="tight", dpi=150)

        # TODO Enable logging
        print("\nplt object saved to file {}\n".format(fname))

        return None

    def check_values(self):
        """
        Check to make sure all of the required parameters have been entered before enabling certain buttons
        Returns:
            None
        """
        # <int> A container to keep track of how many parameters have been entered
        counter = 0

        # <list> List containing the text() values from each of the input widgets
        checks = [self.ui.browsecacheline.text(),
                  self.ui.browsejsonline.text(),
                  self.ui.xline.text(),
                  self.ui.yline.text(),
                  self.ui.browseoutputline.text()]

        # Parse through the checks list to check for entered text
        for check in checks:
            if check == "":
                self.ui.plotbutton.setEnabled(False)

                self.ui.clearpushButton.setEnabled(False)

                self.ui.savefigpushButton.setEnabled(False)

            else:
                counter += 1

        # If all parameters are entered, then counter will equal 6
        if counter == 5:
            self.ui.plotbutton.setEnabled(True)

        # Don't try to generate a shapefile if GDAL isn't installed
        if gdal_found is False:
            self.ui.radioshp.setEnabled(False)

        return None

    def browsecache(self):
        """
        Open QFileDialog to manually browse to and retrieve the full path to the directory containing ARD cache files
        Returns:
            None
        """
        # <str> Full path to the ARD cache directory (tile-specific)
        cachedir = QFileDialog.getExistingDirectory(self)

        self.ui.browsecacheline.setText(cachedir)

        return None

    def browsejson(self):
        """
        Open a QFileDialog to manually browse to and retrieve the full path to the PyCCD results directory
        Returns:
            None
        """
        # <str> Full path to the directory containing PyCCD results (.json files)
        jsondir = QFileDialog.getExistingDirectory(self)

        self.ui.browsejsonline.setText(jsondir)

        return None

    def browseoutput(self):
        """
        Open a QFileDialog to manually browse to and retrieve the full path to the output directory
        Returns:
            None
        """
        # <str> Full path to the output directory, used for saving plot images
        output_dir = QFileDialog.getExistingDirectory(self)

        self.ui.browseoutputline.setText(output_dir)

        return None

    def show_model_params(self, data):
        """
        Print the model results out to the GUI QPlainTextEdit widget
        Args:
            data: <CCDReader instance> Class instance containing change model results and parameters

        Returns:
            None
        """
        # TODO Enable logging
        self.ui.plainTextEdit_results.clear()

        self.ui.plainTextEdit_results.appendPlainText(data.message)

        try:
            self.ui.plainTextEdit_results.appendPlainText("\n***Duplicate dates***\n{}".format(data.duplicates))

        except AttributeError:
            pass

        self.ui.plainTextEdit_results.appendPlainText("\n\nBegin Date: {}".format(data.BEGIN_DATE))

        self.ui.plainTextEdit_results.appendPlainText("End Date: {}\n".format(data.END_DATE))

        for num, result in enumerate(data.results["change_models"]):
            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num + 1))

            self.ui.plainTextEdit_results.appendPlainText(
                "Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))

            self.ui.plainTextEdit_results.appendPlainText("QA: {}".format(result["curve_qa"]))

            self.ui.plainTextEdit_results.appendPlainText("Change prob: {}\n".format(result["change_probability"]))

        return None

    def plot(self):
        """
        Instantiate the CCDReader class that retrieves the plotting data and generate the plots
        Returns:
            None
        """
        # <bool> If True, generate a point shapefile for the entered coordinates
        shp_on = self.ui.radioshp.isChecked()

        # <bool> If True, input units are meters
        if self.ui.radio_geog.isChecked():
            units = "geog"

        else:
            units = "meters"

        # Close the previous plot window if still open
        try:
            self.plot_window.close()

        # Will raise AttributeError if this is the first plot because "p" doesn't exist yet
        except AttributeError:
            pass

        # If there is a problem with any of the parameters, the first erroneous parameter
        # will cause an exception to occur which will be displayed in the GUI for the user, and the tool won't close.
        try:
            self.extracted_data = CCDReader(x=self.ui.xline.text(),
                                            y=self.ui.yline.text(),
                                            units=units,
                                            cache_dir=str(self.ui.browsecacheline.text()),
                                            json_dir=str(self.ui.browsejsonline.text()))

        except (IndexError, AttributeError, TypeError, ValueError):
            # Clear the results window
            self.ui.plainTextEdit_results.clear()

            # TODO Enable logging
            # Show which exception was raised
            self.ui.plainTextEdit_results.appendPlainText("***Plotting Error***\
                                                          \n\nType of Exception: {}\
                                                          \nException Value: {}\
                                                          \nTraceback Info: {}".format(sys.exc_info()[0],
                                                                                       sys.exc_info()[1],
                                                                                       traceback.print_tb(
                                                                                           sys.exc_info()[2])))

            return None

        # TODO Add a source image directory in the GUI
        self.ard_specs = ard_info.ARDInfo(self.ard_directory,
                                          self.extracted_data.geo_info.H,
                                          self.extracted_data.geo_info.V)

        # Display change model information for the entered coordinates
        self.show_model_params(data=self.extracted_data)

        # <list> The bands and/or indices selected for plotting
        item_list = [str(i.text()) for i in self.ui.listitems.selectedItems()]

        # fig <matplotlib.figure> Matplotlib figure object containing all of the artists
        # artist_map <dict> mapping each specific PathCollection artist to it's underlying dataset
        # lines_map <dict> mapping artist lines and points to the legend lines
        self.fig, artist_map, lines_map, axes = make_plots.draw_figure(data=self.extracted_data, items=item_list)

        if not os.path.exists(self.ui.browseoutputline.text()):
            os.makedirs(self.ui.browseoutputline.text())

        # Generate the ESRI point shapefile
        if shp_on is True and gdal_found is True:
            self.get_shp(coords=self.extracted_data.geo_info.coord,
                         out_shp=self.fname_generator(ext=".shp"))

        # Show the figure in an interactive window
        self.plot_window = PlotWindow(fig=self.fig,
                                      axes=axes,
                                      artist_map=artist_map,
                                      lines_map=lines_map,
                                      gui=self,
                                      scenes=self.extracted_data.image_ids)

        # Make these buttons available once a figure has been created
        self.ui.clearpushButton.setEnabled(True)
        self.ui.savefigpushButton.setEnabled(True)

        return None

    @staticmethod
    def get_shp(coords, out_shp):
        """
        Create a point shapefile at the (x, y) coordinates
        Args:
            coords: <GeoCoordinate>
            out_shp: <str> Full path to the output shapefile

        Returns:
            None
        """
        outdir = "{a}{b}{c}".format(a=os.path.split(out_shp)[0],
                                    b=os.sep,
                                    c="shp")

        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)

            except PermissionError:
                # TODO Enable logging

                return None

        layer_name = os.path.splitext(os.path.split(out_shp)[-1])[0]

        # Set up driver
        driver = ogr.GetDriverByName("ESRI Shapefile")

        # Create data source
        data_source = driver.CreateDataSource(out_shp)

        # Create a SpatialReference() object and import the pre-defined well-known text
        srs = osr.SpatialReference()
        srs.ImportFromWkt(projections.AEA_WKT)

        # Create layer, add fields to contain x and y coordinates
        layer = data_source.CreateLayer(layer_name, srs)
        layer.CreateField(ogr.FieldDefn("X", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("Y", ogr.OFTReal))

        # Create feature, populate X and Y fields
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("X", coords.x)
        feature.SetField("Y", coords.y)

        # Create the Well Known Text containing the point feature location
        wkt = "POINT(%f %f)" % (coords.x, coords.y)

        # Create a point from the Well Known Text
        point = ogr.CreateGeometryFromWkt(wkt)

        # Set feature geometry to point-type
        feature.SetGeometry(point)

        # Create the feature in the layer
        layer.CreateFeature(feature)

        return None

    def show_ard(self, clicked_item):
        """
        Display the ARD image clicked on the plot
        Args:
            clicked_item: <QListWidgetItem> Passed automatically by the itemClicked method of the QListWidget

        Returns:
            None
        """
        # Close the previous ARDViewerX instance if one exists
        print("point clicked: ", clicked_item)

        try:
            self.ard.close()

        except AttributeError:
            pass

        try:
            # Don't include the processing date in the scene ID
            sceneID = clicked_item.text().split()[2][:23]

            scene_files = self.ard_specs.vsipaths[sceneID]

            sensor = self.ard_specs.get_sensor(sceneID)

            self.ard = ARDViewerX(ard_file=scene_files[0:7], ccd=self.extracted_data, sensor=sensor, gui=self)

        # TODO Enable logging
        except (AttributeError, IndexError):
            print(sys.exc_info()[0])

            print(sys.exc_info()[1])

            traceback.print_tb(sys.exc_info()[2])

    def exit_plot(self):
        """
        Close the GUI
        Returns:
            None
        """
        self.close()

        sys.exit(0)
