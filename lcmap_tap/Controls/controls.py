"""
Establish the main GUI Window using PyQt, provide the main interactions with child widgets
"""

from lcmap_tap.UserInterface import ui_main_workshop
from lcmap_tap.Controls import UNITS
from lcmap_tap.RetrieveData import aliases, RowColumn
from lcmap_tap.RetrieveData.retrieve_ard import ARDData
from lcmap_tap.RetrieveData.retrieve_ccd import CCDReader
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData.retrieve_classes import SegmentClasses
from lcmap_tap.PlotFrame.plotwindow import PlotWindow
from lcmap_tap.PlotFrame.symbology_window import SymbologyWindow
from lcmap_tap.Plotting import make_plots, LOOKUP, LINES, POINTS
from lcmap_tap.Plotting.plot_config import PlotConfig
from lcmap_tap.Plotting.plot_specs import PlotSpecs
from lcmap_tap.Auxiliary import projections
from lcmap_tap.Visualization.chip_viewer import ChipsViewerX
from lcmap_tap.MapCanvas.mapcanvas import MapCanvas
from lcmap_tap.logger import log, exc_handler, QtHandler
from lcmap_tap.Auxiliary.caching import read_cache, update_cache
from lcmap_tap import HOME

import datetime as dt
import os
import sys
import time
import re
import matplotlib
import matplotlib.pyplot as plt
import yaml
import pkg_resources
import pandas as pd
import numpy as np
from osgeo import ogr, osr
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5 import QtCore

# Tell matplotlib to use the QT5Agg Backend
matplotlib.use('Qt5Agg')

sys.excepthook = exc_handler

try:
    CONFIG = yaml.load(open(pkg_resources.resource_filename('lcmap_tap', 'config.yaml')))

except FileNotFoundError as e:
    log.error('Exception: %s' % e, exc_info=True)

    log.critical('Configuration file not present, TAP Tool will not be able to retrieve data.  Exiting')

    sys.exit(1)


def get_time():
    """
    Return the current time stamp

    Returns:
        A formatted string containing the current date and time

    """
    return time.strftime("%Y%m%d-%H%M%S")


class MainControls(QMainWindow):
    session = get_time()

    merlin_url = CONFIG['URL']

    def __init__(self):

        super().__init__()

        # Create an instance of a class that builds the user-interface, created in QT Designer and compiled with pyuic5
        self.ui = ui_main_workshop.Ui_MainWindow_tap()

        # Call the method that adds all of the widgets to the GUI
        self.ui.setupUi(self)

        # Create an empty dict that will contain any available cached chip data
        self.cache_data = dict()

        self.config = None
        self.plot_window = None
        self.ard_specs = None
        self.ard = None
        self.fig = None
        self.current_view = None
        self.tile = None
        self.item_list = None
        self.highlighted = None
        self.artist_map = None
        self.lines_map = None
        self.axes = None
        self.geo_info = None  # container for geographic info derived from the input coordinates
        self.ard_observations = None  # container for the ARD stack at the pixel
        self.ccd_results = None  # container for PyCCD results at the pixel
        self.class_results = None  # container for classification results at the pixel
        self.plot_specs = None  # container for plotting data
        self.begin = dt.date(year=1982, month=1, day=1)
        self.end = dt.date(year=2017, month=12, day=31)

        self.plotconfig = PlotConfig()

        # Use these to store ARD viewer color channels
        self.store_r = 3
        self.store_g = 2
        self.store_b = 1

        self.fig_num = 0

        self.working_directory = None

        # Used to display log output to the QPlainTextEdit on the main GUI
        self.qt_handler = QtHandler(self.ui.PlainTextEdit_results)

        self.leaflet_map = MapCanvas(self)

        self.selected_units = self.ui.ComboBox_units.currentText()

        self.connect_widgets()

        self.ui.LineEdit_x1.setText('-2193585')
        self.ui.LineEdit_y1.setText('1886805')

        self.show()

    def connect_widgets(self):
        """
        Connect the various widgets to the methods they interact with

        Returns:
            None

        """
        # *** Connect the various widgets to the methods they interact with ***
        self.ui.LineEdit_x1.textChanged.connect(self.set_units)

        self.ui.LineEdit_x1.textChanged.connect(self.assemble_paths)

        self.ui.LineEdit_x1.textChanged.connect(self.check_values)

        self.ui.LineEdit_y1.textChanged.connect(self.set_units)

        self.ui.LineEdit_y1.textChanged.connect(self.assemble_paths)

        self.ui.LineEdit_y1.textChanged.connect(self.check_values)

        self.ui.ComboBox_units.currentIndexChanged.connect(self.set_units)

        # Call the activated signal when the user clicks on any item (new or old) in the comboBox
        # [str] calls the overloaded signal that passes the Qstring, not the index of the item
        # self.ui.version_comboBox.activated[str].connect(self.set_version)

        self.ui.PushButton_outputDir.clicked.connect(self.browse_output)

        self.ui.LineEdit_outputDir.textChanged.connect(self.check_values)

        self.ui.PushButton_plot.clicked.connect(self.plot)

        self.ui.PushButton_clear.clicked.connect(self.clear)

        self.ui.PushButton_saveFigure.clicked.connect(self.save_fig)

        self.ui.PushButton_close.clicked.connect(self.exit_plot)

        self.ui.ListWidget_selected.itemClicked.connect(self.show_ard)

        self.ui.PushButton_locator.clicked.connect(self.show_locator_map)

        self.ui.PushButton_export.clicked.connect(self.export_data)

    def show_locator_map(self):
        """
        Open the Leaflet map for selecting a coordinate for plotting

        """
        self.leaflet_map.show()

    def clear(self):
        """
        Clear the GUI of user-entered information

        """
        def __clear(list_widget):
            list_widget.clearSelection()

        self.ui.ListWidget_selected.clear()

        __clear(self.ui.ListWidget_items)

        self.ui.LineEdit_x1.setText('')

        self.ui.LineEdit_y1.setText('')

        self.ui.LineEdit_outputDir.setText('')

        return None

    def set_units(self):
        """
        Change the unit labels if the units are changed on the GUI, display the converted units if values are entered

        """
        self.selected_units = self.ui.ComboBox_units.currentText()

        self.ui.Label_x1.setText(UNITS[self.selected_units]["Label_x1"])

        self.ui.Label_y1.setText(UNITS[self.selected_units]["Label_y1"])

        self.ui.Label_x2.setText(UNITS[self.selected_units]["Label_x2"])

        self.ui.Label_y2.setText(UNITS[self.selected_units]["Label_y2"])

        self.ui.Label_convertedUnits.setText(UNITS[self.selected_units]["Label_convertedUnits"])

        if len(self.ui.LineEdit_x1.text()) > 0 and len(self.ui.LineEdit_y1.text()) > 0:
            # <GeoCoordinate> containing the converted coordinates to display
            temp = GeoInfo.unit_conversion(coord=GeoInfo.get_geocoordinate(xstring=self.ui.LineEdit_x1.text(),
                                                                           ystring=self.ui.LineEdit_y1.text()),
                                           src=UNITS[self.selected_units]["unit"],
                                           dest=UNITS[self.ui.Label_convertedUnits.text()]["unit"])

            self.ui.LineEdit_x2.setText(str(temp.x))

            self.ui.LineEdit_y2.setText(str(temp.y))

            if UNITS[self.selected_units]["unit"] == "meters":
                geocoord = GeoInfo.get_geocoordinate(xstring=self.ui.LineEdit_x1.text(),
                                                     ystring=self.ui.LineEdit_y1.text())

            else:
                geocoord = GeoInfo.get_geocoordinate(xstring=self.ui.LineEdit_x2.text(),
                                                     ystring=self.ui.LineEdit_y2.text())

            h, v = GeoInfo.get_hv(geocoord.x, geocoord.y)

            self.tile = "h{:02}v{:02}".format(h, v)

    def fname_generator(self, ext=".png"):
        """
        Generate a string for an output file

        Args:
            ext: <str> The output file extension, default is .png

        Returns:
            <str> The full path to the output file name

        """
        outdir = self.ui.LineEdit_outputDir.text()

        coord = f"{self.geo_info.coord.x}_{self.geo_info.coord.y}"

        fname = f"H{self.geo_info.H}V{self.geo_info.V}_{coord}_{get_time()}{ext}"

        return os.path.join(outdir, fname)

    def save_fig(self):
        """
        Save the current matplotlib figure to a PNG file

        """
        if not os.path.exists(self.ui.LineEdit_outputDir.text()):
            os.makedirs(self.ui.LineEdit_outputDir.text())

        fname = self.fname_generator()

        # Overwrite the .png if it already exists
        if os.path.exists(fname):
            try:
                os.remove(fname)

            except (IOError, PermissionError) as _e:
                log.error('Exception: %s' % _e, exc_info=True)

        # Make sure the timeseries plot is set as the current figure
        plt.figure(f'timeseries_figure_{self.fig_num}')

        plt.savefig(fname, bbox_inches="tight", dpi=150)

        log.debug("Plot figure saved to file {}".format(fname))

    def assemble_paths(self):
        """
        Generate the paths to the various required data

        """
        # self.set_units()
        if self.tile:
            self.class_directory = os.path.join(CONFIG['CCD'], self.tile, 'class', 'annualized', 'pickles')

            self.ccd_directory = os.path.join(CONFIG['CCD'], self.tile, 'change', 'n-compare', 'json')

        self.working_directory = self.ui.LineEdit_outputDir.text()

        if self.working_directory is None or self.working_directory is "":
            self.working_directory = os.path.join(HOME, self.session)

            self.ui.LineEdit_outputDir.setText(self.working_directory)

        if not os.path.exists(self.working_directory):
            os.makedirs(self.working_directory)

    def check_values(self):
        """
        Check to make sure all of the required parameters have been entered before enabling Plot

        """
        # <int> A container to keep track of how many parameters have been entered
        counter = 0

        checks = [self.ui.LineEdit_x1.text(),
                  self.ui.LineEdit_y1.text(),
                  self.ui.LineEdit_outputDir.text()]

        # Parse through the checks list to check for entered text
        for check in checks:
            if check == "":
                self.ui.PushButton_plot.setEnabled(False)

                self.ui.PushButton_clear.setEnabled(False)

                self.ui.PushButton_saveFigure.setEnabled(False)

            else:
                counter += 1

        # If all parameters are entered and valid, enable the plot button
        if counter == len(checks):
            self.ui.PushButton_plot.setEnabled(True)

    @staticmethod
    def check_path(name, path):
        """
        Check if the input path exists
        Args:
            name <str>: The path category (e.g. cache, json, ard)
            path <str>: A path on the system

        Returns:
            <bool>

        """
        if not os.path.exists(path):
            log.warning("The %s path %s cannot be found" % (name, path))

            return False

        else:
            return True

    def browse_output(self):
        """
        Open a QFileDialog to manually browse to and retrieve the full path to the output directory

        """
        # <str> Full path to the output directory, used for saving plot images
        output_dir = QFileDialog.getExistingDirectory(self)

        if len(output_dir) > 0:
            self.ui.LineEdit_outputDir.setText(output_dir)

    def show_model_params(self, results, geo):
        """
        Print the model results out to the GUI QPlainTextEdit widget

        Args:
            results: Class instance containing change model results and parameters
            geo: Class instance containing geographic info

        """
        log.info("Plotting for tile H{:02}V{:02} at point ({}, {}) meters".format(geo.H, geo.V,
                                                                                  geo.coord.x,
                                                                                  geo.coord.y))

        try:
            self.ui.PlainTextEdit_results.appendPlainText("\n\nBegin Date: {}".format(results.begin))
            log.info("Begin Date: {}".format(results.begin))

            self.ui.PlainTextEdit_results.appendPlainText("End Date: {}\n".format(results.end))
            log.info("End Date: {}".format(results.end))

            for num, result in enumerate(results.results["change_models"]):
                self.ui.PlainTextEdit_results.appendPlainText("Result: {}".format(num + 1))
                log.info("Result: {}".format(num + 1))

                self.ui.PlainTextEdit_results.appendPlainText(
                    "Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))
                log.info("Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))

                self.ui.PlainTextEdit_results.appendPlainText(
                    "End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))
                log.info("End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))

                self.ui.PlainTextEdit_results.appendPlainText(
                    "Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))
                log.info("Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))

                self.ui.PlainTextEdit_results.appendPlainText("QA: {}".format(result["curve_qa"]))
                log.info("QA: {}".format(result["curve_qa"]))

                self.ui.PlainTextEdit_results.appendPlainText("Change prob: {}\n".format(result["change_probability"]))
                log.info("Change prob: {}".format(result["change_probability"]))

        except (ValueError, TypeError) as _e:
            log.error('Exception: %s' % _e, exc_info=True)

            pass

    def plot(self):
        """
        TODO: Add descriptive information

        """
        if self.plot_window:
            self.plot_window.close()

        self.fig_num += 1

        # <list> The bands and/or indices selected for plotting
        self.item_list = [str(i.text()) for i in self.ui.ListWidget_items.selectedItems()]

        self.geo_info = GeoInfo(x=self.ui.LineEdit_x1.text(),
                                y=self.ui.LineEdit_y1.text(),
                                units=UNITS[self.selected_units]["unit"])

        self.cache_data = read_cache(self.geo_info, self.cache_data)

        self.ard_observations = ARDData(geo=self.geo_info,
                                        url=self.merlin_url,
                                        items=self.item_list,
                                        cache=self.cache_data)

        self.cache_data = update_cache(self.cache_data, self.ard_observations.cache, self.ard_observations.key)

        try:
            self.ccd_results = CCDReader(tile=self.geo_info.tile,
                                         chip_coord=self.geo_info.chip_coord_ul,
                                         pixel_coord=self.geo_info.pixel_coord_ul,
                                         json_dir=self.ccd_directory)

        except (IndexError, AttributeError, TypeError, ValueError, FileNotFoundError) as _e:
            log.error('Exception: %s' % _e, exc_info=True)

            self.ccd_results = None

        try:
            self.class_results = SegmentClasses(chip_coord_ul=self.geo_info.chip_coord_ul,
                                                class_dir=self.class_directory,
                                                rc=self.geo_info.chip_pixel_rowcol,
                                                tile=self.geo_info.tile)

        except (IndexError, AttributeError, TypeError, ValueError, FileNotFoundError) as _e:
            log.error('Exception: %s' % _e, exc_info=True)

            self.class_results = None

        self.plot_specs = PlotSpecs(ard=self.ard_observations.pixel_ard,
                                    change=self.ccd_results,
                                    segs=self.class_results,
                                    items=self.item_list,
                                    begin=self.begin,
                                    end=self.end)

        self.ui.PushButton_export.setEnabled(True)

        # Display change model information for the entered coordinates
        self.show_model_params(results=self.plot_specs, geo=self.geo_info)

        """
        fig <matplotlib.figure> Matplotlib figure object containing all of the artists
        
        artist_map <dict> mapping of each specific PathCollection artist to it's underlying dataset
        
        lines_map <dict> mapping of artist lines and points to the legend lines
        
        axes <ndarray> 2D array of matplotlib.axes.Axes objects
        """
        self.fig, self.artist_map, self.lines_map, self.axes = make_plots.draw_figure(data=self.plot_specs,
                                                                                      items=self.item_list,
                                                                                      fig_num=self.fig_num,
                                                                                      config=self.plotconfig.opts)

        if not os.path.exists(self.ui.LineEdit_outputDir.text()):
            os.makedirs(self.ui.LineEdit_outputDir.text())

        # Generate the ESRI point shapefile
        temp_shp = self.fname_generator(ext=".shp")
        root, name = os.path.split(temp_shp)
        root = root + os.sep + "shp"

        self.get_shp(coords=self.geo_info.coord,
                     out_shp="{}{}{}".format(root, os.sep, name))

        # Show the figure in an interactive window
        self.plot_window = PlotWindow(fig=self.fig,
                                      axes=self.axes,
                                      artist_map=self.artist_map,
                                      lines_map=self.lines_map
                                      )

        self.plot_window.selected_obs.connect(self.connect_plot_selection)

        self.plot_window.change_symbology.connect(self.change_symbology)

        # Make these buttons available once a figure has been created
        self.ui.PushButton_clear.setEnabled(True)

        self.ui.PushButton_saveFigure.setEnabled(True)

    @staticmethod
    def get_shp(coords, out_shp):
        """
        Create a point shapefile at the (x, y) coordinates
        Args:
            coords: <GeoCoordinate> 
            out_shp: <str> Contains a root path and filename for the output shapefile

        """
        if not os.path.exists(os.path.split(out_shp)[0]):
            try:
                os.makedirs(os.path.split(out_shp)[0])

            except PermissionError as _e:

                log.warning("Generating shapefile raised exception: ")
                log.warning(_e, exc_info=True)

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

    def show_ard(self, clicked_item):
        """
        Display the ARD image clicked on the plot

        Args:
            clicked_item: <QListWidgetItem> Passed automatically by the itemClicked method of the QListWidget

        Returns:
            None
        """
        match = re.search(r'\d{4}-\D{3}-\d{2}', clicked_item.text()).group()

        date = dt.datetime.strptime(match, '%Y-%b-%d')

        try:
            if self.ard:

                # Update with the previously selected color channels so they are displayed in the new ARD viewer
                self.store_r = self.ard.r
                self.store_g = self.ard.g
                self.store_b = self.ard.b

                self.close_ard()

            self.ard = ChipsViewerX(x=self.geo_info.coord.x,
                                    y=self.geo_info.coord.y,
                                    date=date,
                                    url=self.merlin_url,
                                    subplot=self.plot_window.b,
                                    geo=self.geo_info,
                                    r=self.store_r,
                                    g=self.store_g,
                                    b=self.store_b,
                                    outdir=self.working_directory)

            self.ard.update_plot_signal.connect(self.update_plot)

        except (AttributeError, IndexError) as _e:
            log.error("Display ARD raised an exception: %s" % _e, exc_info=True)

    def close_ard(self):
        """
        If plotting for a new HV tile, close the previous ARD Viewer window if one was previously opened

        Returns:
            None

        """
        try:
            self.ard.exit()

        except AttributeError as _e:
            log.error('Exception: %s' % _e, exc_info=True)

    def export_data(self):
        """
        Export the currently plotted data to an output CSV that will be saved in the specified working directory.

        """
        data = dict()

        for item in self.item_list:
            if item in aliases.keys():
                group = aliases[item]

                for key in group:
                    data[key] = self.ard_observations.pixel_ard[key]

        try:
            data['qa'] = self.ard_observations.pixel_ard['qas']

            data['dates'] = self.ard_observations.pixel_ard['dates']

        except KeyError as _e:
            log.error('Exception: %s' % _e, exc_info=True)

        data = pd.DataFrame(data).sort_values('dates').reset_index(drop=True)

        data['dates'] = data['dates'].apply(lambda x: dt.datetime.fromordinal(x))

        data.to_csv(os.path.join(self.working_directory,
                                 f'{get_time()}_{self.geo_info.pixel_coord_ul.x}_{self.geo_info.pixel_coord_ul.y}.csv'))

        return None

    @staticmethod
    def exit_plot():
        """
        Close all TAP tool windows and exit the program

        """
        log.info("Exiting TAP Tool")

        sys.exit(0)

    def closeEvent(self, event):
        """
        Override method if the GUI is closed but 'Close' button is not used

        Args:
            event:

        Returns:

        """
        self.exit_plot()

    @QtCore.pyqtSlot(object)
    def connect_plot_selection(self, val):
        """
        Display the selected observation in the main control window

        Args:
            val (dict): Information describing which observation was selected in a particular axes

        Returns:

        """
        log.debug("emitted selection: {}".format(val))

        output = "Obs. Date: {:%Y-%b-%d}\n{}-Value: {}".format(val['date'], val['b'], val['value'])

        self.plot_window.b = val['b']

        self.ui.ListWidget_selected.addItem(output)

    @QtCore.pyqtSlot(object)
    def update_plot(self):
        """
        Generate a new plot for the clicked point location

        Returns:
            None

        """
        # Gather information to retrieve necessary data for the new plot
        rowcol = RowColumn(row=self.ard.row, column=self.ard.col)

        coords = GeoInfo.rowcol_to_geo(affine=self.ard.pixel_image_affine,
                                       rowcol=rowcol)

        # Update the x and y so that they are displayed correctly with save_img
        self.ard.x = coords.x
        self.ard.y = coords.y

        log.debug("New point selected: %s" % str(coords))

        # Update the X and Y coordinates in the GUI with the new point
        if UNITS[self.selected_units]["unit"] == "meters":

            self.ui.LineEdit_x1.setText(str(coords.x))

            self.ui.LineEdit_y1.setText(str(coords.y))

        # Convert to lat/long before updating the coordinate text on the GUI
        else:
            _coords = GeoInfo.unit_conversion(coords)

            self.ui.LineEdit_x1.setText(str(_coords.x))

            self.ui.LineEdit_y1.setText(str(_coords.y))

        # Do the plotting and generate a new figure
        self.check_values()

        self.plot()

        """Need to determine the y-axis value for the new time series.  Can be done by determining the index within
        the new time-series of the x-axis (i.e. date) value from the previous time series """
        x_look_thru = {"obs_points": self.plot_specs.dates_in[self.plot_specs.qa_mask[
            self.plot_specs.date_mask]],

                       "out_points": self.plot_specs.dates_out[self.plot_specs.fill_out],

                       "mask_points": self.plot_specs.dates_in[~self.plot_specs.qa_mask[
                           self.plot_specs.date_mask]]
                       }

        y_look_thru = {"obs_points": self.plot_specs.all_lookup[self.ard.ax][0][self.plot_specs.date_mask][
            self.plot_specs.qa_mask[
                self.plot_specs.date_mask]],

                       "out_points": self.plot_specs.all_lookup[self.ard.ax][0][~self.plot_specs.date_mask][
                           self.plot_specs.fill_out],

                       "mask_points": self.plot_specs.all_lookup[self.ard.ax][0][self.plot_specs.date_mask][
                           ~self.plot_specs.qa_mask[
                               self.plot_specs.date_mask]]
                       }

        for key, x in x_look_thru.items():
            if self.ard.date_x in x:
                x_series = x

                y_series = y_look_thru[key]

                #: int: the location of the date in the new time series
                ind = np.where(x_series == self.ard.date_x)

                #: the reflectance or index value for the new time series
                data_y = np.take(y_series, ind)

                # Display the highlighted pixel in the new plot
                highlight = self.plot_window.artist_map[self.ard.ax][0]

                # highlight.set_data(self.date_x[0], self.data_y[0])
                highlight.set_data(self.ard.date_x, data_y)

                self.plot_window.canvas.draw()

                break

    @QtCore.pyqtSlot(object)
    def change_symbology(self, label):
        self.label = label

        pick = LOOKUP[self.label]

        current_settings = self.plotconfig.opts['DEFAULTS'][pick]

        # --- Reference the currently used marker or line style ---
        if 'marker' in current_settings.keys():
            marker = current_settings['marker']

        else:
            marker = current_settings['linestyle']

        # --- Reference the currently used marker size or line width ---
        if 's' in current_settings.keys():
            size = current_settings['s']

        elif 'ms' in current_settings.keys():
            size = current_settings['ms']

        else:
            size = current_settings['linewidth']

        # --- Reference the currently used color name ---
        if self.label is 'Selected':
            color = current_settings['mec']

        else:
            color = current_settings['color']

        # --- Reference the currently used background color ---
        bg = self.plotconfig.opts['DEFAULTS']['background']['color']

        self.symbol_selector = SymbologyWindow(marker, size, color, bg, self.label)

        self.symbol_selector.selected_marker.connect(self.redraw_plot)

        self.symbol_selector.file_saver.connect(self.save_plot_config)

        self.symbol_selector.file_loader.connect(self.load_plot_config)

    @QtCore.pyqtSlot(object)
    def redraw_plot(self, val):
        self.fig_num += 1

        log.debug("Received plot config vals: {}".format(val))

        if self.label in POINTS:
            self.plotconfig.update_config(self.label, {'marker': val['marker'],
                                                       's': val['markersize'],
                                                       'color': val['color'],
                                                       'background': val['background']})

        else:
            self.plotconfig.update_config(self.label, {'linestyle': val['marker'],
                                                       'linewidth': val['markersize'],
                                                       'color': val['color'],
                                                       'background': val['background']})

        self.symbol_selector.close()

        self.fig, self.artist_map, self.lines_map, self.axes = make_plots.draw_figure(data=self.plot_specs,
                                                                                      items=self.item_list,
                                                                                      fig_num=self.fig_num,
                                                                                      config=self.plotconfig.opts)

        self.plot_window = PlotWindow(fig=self.fig,
                                      axes=self.axes,
                                      artist_map=self.artist_map,
                                      lines_map=self.lines_map
                                      )

        self.plot_window.selected_obs.connect(self.connect_plot_selection)

        self.plot_window.change_symbology.connect(self.change_symbology)

    @QtCore.pyqtSlot(object)
    def save_plot_config(self, outfile):
        """Save the plot configuration settings for use in a different session"""
        log.debug('plot config outfile: {}'.format(outfile))

        with open(outfile, 'w') as f:
            yaml.dump(self.plotconfig.opts, f)

        self.symbol_selector.close()

    @QtCore.pyqtSlot(object)
    def load_plot_config(self, infile):
        with open(infile, 'r') as f:
            self.plotconfig.opts = yaml.load(f)

        self.symbol_selector.close()

        self.fig_num += 1

        self.fig, self.artist_map, self.lines_map, self.axes = make_plots.draw_figure(data=self.plot_specs,
                                                                                      items=self.item_list,
                                                                                      fig_num=self.fig_num,
                                                                                      config=self.plotconfig.opts)

        self.plot_window = PlotWindow(fig=self.fig,
                                      axes=self.axes,
                                      artist_map=self.artist_map,
                                      lines_map=self.lines_map
                                      )

        self.plot_window.selected_obs.connect(self.connect_plot_selection)

        self.plot_window.change_symbology.connect(self.change_symbology)