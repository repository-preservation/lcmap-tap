import sys
import os
import datetime as dt

import matplotlib

matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QMainWindow, QFileDialog

# Import the main GUI built in QTDesigner, compiled into python with pyuic5.bat
# from Controls.ui_main import Ui_PyCCDPlottingTool
from Controls.UI_MAINv3 import Ui_PyCCDPlottingTool

# Import the CCDReader class which retrieves json and cache data
from retrieve_data import CCDReader

# Import the PlotWindow display built in QT Designer
from PlotFrame.plotwindow import PlotWindow

from Plotting import make_plots

import matplotlib.pyplot as plt

# ARD standard projection
WKT = 'PROJCS["Albers",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378140,298.2569999999957,AUTHORITY["EPSG",' \
      '"7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG",' \
      '"4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",29.5],' \
      'PARAMETER["standard_parallel_2",45.5],PARAMETER["latitude_of_center",23],PARAMETER["longitude_of_center",-96],' \
      'PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'


class PlotControls(QMainWindow):
    def __init__(self):

        super(PlotControls, self).__init__()

        self.ui = Ui_PyCCDPlottingTool()

        self.ui.setupUi(self)

        self.ui.browsecachebutton.clicked.connect(self.browsecache)

        self.ui.browsejsonbutton.clicked.connect(self.browsejson)

        self.ui.browseoutputbutton.clicked.connect(self.browseoutput)

        self.item_list = self.ui.listitems.selectedItems()

        self.ui.plotbutton.clicked.connect(self.plot)

        self.ui.exitbutton.clicked.connect(self.exit_plot)

        self.init_ui()

    def init_ui(self):

        self.show()

    def check_if_values(self):

        if self.ui.browsecacheline.text() is None:
            return False

        elif self.ui.browsejsonline.text() is None:
            return False

        elif self.ui.hline.text() is None:
            return False

        elif self.ui.vline.text() is None:
            return False

        elif self.ui.browseoutputline.text() is None:
            return False

        elif self.ui.arccoordsline.text() is None:
            return False

        else:
            return True

    def browsecache(self):

        cachedir = QFileDialog.getExistingDirectory(self)

        self.ui.browsecacheline.setText(cachedir)

        return None

    def browsejson(self):

        jsondir = QFileDialog.getExistingDirectory(self)

        self.ui.browsejsonline.setText(jsondir)

        return None

    def browseoutput(self):

        outputdir = QFileDialog.getExistingDirectory(self)

        self.ui.browseoutputline.setText(outputdir)

        return None

    def show_results(self, data):
        for num, result in enumerate(data.results["change_models"]):
            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num))

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
        cachedir = self.ui.browsecacheline.text()

        jsondir = self.ui.browsejsonline.text()

        outputdir = self.ui.browseoutputline.text()

        arccoords = self.ui.arccoordsline.text()

        hval = self.ui.hline.text()

        vval = self.ui.vline.text()

        model_on = self.ui.radiomodelfit.isChecked()

        masked_on = self.ui.radiomasked.isChecked()


        """
        shp_on = self.ui.radioshp.isChecked()

        if self.check_if_values is True:
            # global data
            extracted_data = CCDReader(h=int(self.ui.hline.text()), v=int(self.ui.vline.text()),
                                       cache_dir=str(self.ui.browsecacheline.text()),
                                       json_dir=str(self.ui.browsejsonline.text()),
                                       arc_coords=str(self.ui.arccoordsline.text()),
                                       output_dir=str(self.ui.browseoutputline.text()),
                                       model_on=self.ui.radiomodelfit.isChecked(),
                                       masked_on=self.ui.radiomasked.isChecked())

        else:
            return None

        self.show_results(data=extracted_data)

        """
        for num, result in enumerate(data.results["change_models"]):
            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num))

            self.ui.plainTextEdit_results.appendPlainText(
                "Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))

            self.ui.plainTextEdit_results.appendPlainText(
                "Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))

            self.ui.plainTextEdit_results.appendPlainText("QA: {}".format(result["curve_qa"]))

            self.ui.plainTextEdit_results.appendPlainText("Change prob: {}\n".format(result["change_probability"]))


        xmin = min(extracted_data.dates_in[extracted_data.mask]) - 100
        xmax = max(extracted_data.dates_in[extracted_data.mask]) + 750

        ymin = [min(extracted_data.data_in[num, extracted_data.mask]) - 100 for num in range(len(extracted_data.bands))]
        ymax = [max(extracted_data.data_in[num, extracted_data.mask]) + 100 for num in range(len(extracted_data.bands))]


        self.ui.lineEdit_xmin.setText(str(dt.datetime.fromordinal(xmin))[:10])
        self.ui.lineEdit_xmax.setText(str(dt.datetime.fromordinal(xmax))[:10])

        self.ui.lineEdit_ymin.setText(str(ymin[self.band_index]))
        self.ui.lineEdit_ymax.setText(str(ymax[self.band_index]))
        """

        print("Plotting...")

        fig = make_plots.draw(data=extracted_data, items=self.item_list)

        """
        plt.style.use("ggplot")

        fig, axes = plt.subplots(nrows=7, ncols=1, figsize=(16, 34), dpi=60)

        

        for num, b in enumerate(data.bands):

            # Plot the observed values
            axes[num].plot(data.dates_in[data.mask], data.data_in[num, data.mask], 'go', ms=7, mec='k',
                           mew=0.5)

            if data.masked_on is True:

                # Plot masked observations if option is selected
                axes[num].plot(data.dates_in[~data.mask], data.data_in[num, ~data.mask], color='0.65',
                               marker='o', linewidth=0, ms=3)

                addmaskstr = "MASKEDON"

            axes[num].plot(data.dates_out, data.data_out[num], 'ro', ms=5, mec='k', mew=0.5)

            if data.model_on is True:

                addmodelstr = "_MODELON"

                # Plot PyCCD model results, break dates, and start dates if option is selected
                for c in range(0, len(data.results["change_models"])):
                    axes[num].plot(data.prediction_dates[c * len(data.bands) + num],
                                   data.predicted_values[c * len(data.bands) + num], "orange", linewidth=2)

                for s in data.start_dates: axes[num].axvline(s, color='b')

                for b in data.break_dates: axes[num].axvline(b, color='r')

                plot_match_dates = []

                for b in data.break_dates:

                    for s in data.start_dates:

                        if b == s: plot_match_dates.append(s)

                # Use a purple line to show where break date = start date
                for m in plot_match_dates: axes[num].axvline(m, color='purple')

            axes[num].set_title('Band {}'.format(str(num + 1)))

            axes[num].set_xlim([xmin, xmax])

            axes[num].set_ylim([ymin[num], ymax[num]])

        # TODO add indices to the plot output


        # ****X-Axis Ticks and Labels****
        # list of years
        # get year values for labeling plots
        dates = data.dates_in + data.dates_out
        year1 = str(dt.datetime.fromordinal(dates[0]))[:4]
        year2 = str(dt.datetime.fromordinal(dates[-1]))[:4]
        years = list(range(int(year1), int(year2) + 2, 2))

        # list of datetime objects with YYYY-MM-dd pattern
        t = [dt.datetime(yx, 7, 1) for yx in years]

        # list of ordinal time objects
        ord_time = [dt.datetime.toordinal(tx) for tx in t]

        # list of datetime formatted strings
        x_labels = [str(dt.datetime.fromordinal(int(L)))[:10] if L != "0.0" and L != "" else "0" for L in ord_time]

        # Add x-ticks and x-tick_labels
        for a, axis in enumerate(axes):
            axes[a].set_xticks(ord_time)

            axes[a].set_xticklabels(x_labels, rotation=70, horizontalalignment="right")
        """

        addmaskstr, addmodelstr = "MASKEDOFF", "_MODELOFF"

        # ****Generate the output .png filename****
        fname = "{}{}h{}v{}_{}_{}{}.png".format(extracted_data.OutputDir, os.sep, extracted_data.H, extracted_data.V,
                                                extracted_data.arc_paste, addmaskstr, addmodelstr)

        if shp_on is True:
            self.get_shp(extracted_data)

        # ****Save figure to .png and show figure in QWidget****
        fig.tight_layout()

        if not os.path.exists(fname):
            plt.savefig(fname, figuresize=(16, 38), bbox_inches="tight", dpi=150)

            print("\nplt object saved to file {}\n".format(fname))

        global p
        p = PlotWindow(fig)

        return None

    def get_shp(self, data):

        # GeoCoordinate(x=(float value), y=(float value), reference coords.x and coords.y to access x and y values
        coords = data.coord

        layer_name = "H" + str(data.H) + "_V" + str(data.V) + "_" + str(coords.x) + "_" + str(coords.y)

        out_shp = data.OutputDir + os.sep + layer_name + ".shp"

        if not os.path.exists(out_shp):

            try:

                from osgeo import ogr, osr

            except ImportError:

                import ogr, osr

                return None

            # Set up driver
            driver = ogr.GetDriverByName("ESRI Shapefile")

            # Create data source
            data_source = driver.CreateDataSource(out_shp)

            # Set the spatial reference system to NAD83 CONUS Albers
            srs = osr.SpatialReference()

            # Set the spatial reference system to match ARD output (WGS 84 Albers)
            srs.ImportFromWkt(WKT)

            # Create layer, add fields to contain x and y coordinates
            layer = data_source.CreateLayer(layer_name, srs)
            layer.CreateField(ogr.FieldDefn("X", ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn("Y", ogr.OFTReal))

            # Create feature, populate X and Y fields
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("X", coords.x)
            feature.SetField("Y", coords.y)

            # Create the Well Known Text for the feature
            wkt = "POINT(%f %f)" % (coords.x), (coords.y)

            # Create a point from the Well Known Text
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set feature geometry to point-type
            feature.SetGeometry(point)

            # Create the feature in the layer
            layer.CreateFeature(feature)

            # Save and close the data source
            data_source = None

            # Dereference the feature
            feature, point, layer = None, None, None

        return None

    def exit_plot(self):

        # Close the main GUI and plot window
        self.close()

        sys.exit(0)
