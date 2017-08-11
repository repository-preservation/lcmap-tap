
import sys
import os
import datetime as dt

import matplotlib

matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QMainWindow, QFileDialog

# Import the main GUI built in QTDesigner
from Controls.ui_main import Ui_PyCCDPlottingTool

# Import the CCDReader class which retrieves json and cache data
from retrieve_data import CCDReader

# Import the PlotWindow display built in QT Designer
from PlotFrame.plotwindow import PlotWindow

import matplotlib.pyplot as plt


class PlotControls(QMainWindow):

    def __init__(self):

        super(PlotControls, self).__init__()

        self.ui = Ui_PyCCDPlottingTool()

        self.ui.setupUi(self)

        self.ui.browsecachebutton.clicked.connect(self.browsecache)

        self.ui.browsejsonbutton.clicked.connect(self.browsejson)

        self.ui.browseoutputbutton.clicked.connect(self.browseoutput)

        # self.ui.comboBox_bands.activated()
        self.band_index = self.ui.comboBox_bands.currentIndex()

        self.ui.comboBox_bands.activated.connect(self.updateplot)

        self.ui.plotbutton.clicked.connect(self.plot)

        self.ui.exitbutton.clicked.connect(self.exit_plot)

        self.init_ui()

    def init_ui(self):

        self.show()

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

    def plot(self):

        cachedir = self.ui.browsecacheline.text()

        jsondir = self.ui.browsejsonline.text()

        outputdir = self.ui.browseoutputline.text()

        arccoords = self.ui.arccoordsline.text()

        hval = self.ui.hline.text()

        vval = self.ui.vline.text()

        model_on = self.ui.radiomodelfit.isChecked()

        masked_on = self.ui.radiomasked.isChecked()

        shp_on = self.ui.radioshp.isChecked()

        global data
        data = CCDReader(h=int(hval), v=int(vval), cache_dir=str(cachedir),
                         json_dir=str(jsondir), arc_coords=str(arccoords), output_dir=str(outputdir),
                         model_on=model_on, masked_on=masked_on)

        for num, result in enumerate(data.results["change_models"]):

            self.ui.plainTextEdit_results.appendPlainText("Result: {}".format(num))
            self.ui.plainTextEdit_results.appendPlainText("Start Date: {}".format(dt.datetime.fromordinal(result["start_day"])))
            self.ui.plainTextEdit_results.appendPlainText("End Date: {}".format(dt.datetime.fromordinal(result["end_day"])))
            self.ui.plainTextEdit_results.appendPlainText("Break Date: {}".format(dt.datetime.fromordinal(result["break_day"])))
            self.ui.plainTextEdit_results.appendPlainText("QA: {}".format(result["curve_qa"]))
            self.ui.plainTextEdit_results.appendPlainText("Change prob: {}\n".format(result["change_probability"]))

        xmin = min(data.dates_in[data.mask]) - 100
        xmax = max(data.dates_in[data.mask]) + 750

        ymin = [min(data.data_in[num, data.mask]) - 100 for num in range(len(data.bands))]
        ymax = [max(data.data_in[num, data.mask]) + 100 for num in range(len(data.bands))]

        self.ui.lineEdit_xmin.setText(str(dt.datetime.fromordinal(xmin))[:10])
        self.ui.lineEdit_xmax.setText(str(dt.datetime.fromordinal(xmax))[:10])

        self.ui.lineEdit_ymin.setText(str(ymin[self.band_index]))
        self.ui.lineEdit_ymax.setText(str(ymax[self.band_index]))


        print("Plotting...")

        plt.style.use("ggplot")

        fig, axes = plt.subplots(nrows=7, ncols=1, figsize=(16, 34), dpi=60)

        for num, b in enumerate(data.bands):

            axes[num].plot(data.dates_in[data.mask], data.data_in[num, data.mask], 'go', ms=7, mec='k',
                        mew=0.5)  # Observed values

            if data.masked_on == True:

                axes[num].plot(data.dates_in[~data.mask], data.data_in[num, ~data.mask], color='0.65',
                                 marker='o', linewidth=0, ms=3)

                addmaskstr = "MASKEDON"

            else:

                addmaskstr = "MASKEDOFF"

            axes[num].plot(data.dates_out, data.data_out[num], 'ro', ms=5, mec='k', mew=0.5)

            if data.model_on == True:

                addmodelstr = "_MODELON"

                for c in range(0, len(data.results["change_models"])):
                    axes[num].plot(data.prediction_dates[c * len(data.bands) + num],
                                     data.predicted_values[c * len(data.bands) + num], "orange", linewidth=2)

                for s in data.start_dates: axes[num].axvline(s, color='b')

                for b in data.break_dates: axes[num].axvline(b, color='r')

                plot_match_dates = []

                for b in data.break_dates:

                    for s in data.start_dates:

                        if b == s: plot_match_dates.append(s)

                for m in plot_match_dates: axes[num].axvline(m, color='purple')

            elif data.model_on == False:

                addmodelstr = "_MODELOFF"

            axes[num].set_title('Band {}'.format(str(num + 1)))

            axes[num].set_xlim([xmin, xmax])

            axes[num].set_ylim([ymin[num], ymax[num]])

        # ****X-Axis Ticks and Labels****
        # list of years
        y = [yi for yi in range(1981, 2018, 2)]

        # list of datetime objects with YYYY-MM-dd pattern
        t = [dt.datetime(yx, 7, 1) for yx in y]

        # list of ordinal time objects
        ord_time = [dt.datetime.toordinal(tx) for tx in t]

        # list of datetime formatted strings
        x_labels = [str(dt.datetime.fromordinal(int(L)))[:10] if L != "0.0" and L != "" else "0" for L in ord_time]

        # Add x-ticks and x-tick_labels
        for a, axis in enumerate(axes):

            axes[a].set_xticks(ord_time)

            axes[a].set_xticklabels(x_labels, rotation=70, horizontalalignment="right")

        # ****Generate the output .png filename****
        fname = "{}{}h{}v{}_{}_{}{}.png".format(data.OutputDir, os.sep, data.H, data.V, data.arc_paste, addmaskstr,
                                                addmodelstr)

        if shp_on == True: self.get_shp()

        # ****Save figure to .png and show figure in QWidget****
        fig.tight_layout()

        if not os.path.exists(fname):

            plt.savefig(fname, figuresize=(16, 38), bbox_inches="tight", dpi=150)

            print("\nplt object saved to file {}\n".format(fname))

        global p
        p = PlotWindow(fig)

        return None

    def updateplot(self):

        self.band_index = self.ui.comboBox_bands.currentIndex()

        xmin = min(data.dates_in[data.mask]) - 100
        xmax = max(data.dates_in[data.mask]) + 750

        ymin = [min(data.data_in[num, data.mask]) - 100 for num in range(len(data.bands))]
        ymax = [max(data.data_in[num, data.mask]) + 100 for num in range(len(data.bands))]

        # Display the x-min and x-max in datetime format YYYY-MM-DD
        self.ui.lineEdit_xmin.setText(str(dt.datetime.fromordinal(xmin))[:10])
        self.ui.lineEdit_xmax.setText(str(dt.datetime.fromordinal(xmax))[:10])

        # Display the y-min and y-max for the currently selected band in the combobox
        self.ui.lineEdit_ymin.setText(str(ymin[self.band_index]))
        self.ui.lineEdit_ymax.setText(str(ymax[self.band_index]))

    def get_shp(self):

        # GeoCoordinate(x=(float value), y=(float value), reference coords.x and coords.y to access x and y values
        coords = data.coord

        layer_name = "H" + str(data.H) + "_V" + str(data.V) + "_" + str(coords.x) + "_" + str(coords.y)

        out_shp = data.OutputDir + os.sep + layer_name + ".shp"

        if not os.path.exists(out_shp):

            from osgeo import ogr, osr

            # Set up driver
            driver = ogr.GetDriverByName("ESRI Shapefile")

            # Create data source
            data_source = driver.CreateDataSource(out_shp)

            # Set the spatial reference system to NAD83 CONUS Albers
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(5070)

            # Create layer, add fields to contain x and y coordinates
            layer = data_source.CreateLayer(layer_name, srs)
            layer.CreateField(ogr.FieldDefn("X", ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn("Y", ogr.OFTReal))

            # Create feature, populate X and Y fields
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("X", coords.x)
            feature.SetField("Y", coords.y)

            # Create the Well Known Text for the feature
            wkt = "POINT(%f %f)" %((coords.x), (coords.y))

            # Create a point from the Well Known Text
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set feature geometry to point-type
            feature.SetGeometry(point)

            # Create the feature in the layer
            layer.CreateFeature(feature)

            # Dereference the feature
            feature = None

            # Save and close the data source
            data_source = None

        return None

    def exit_plot(self):

        # Close the main GUI and plot window
        self.close()

        sys.exit(0)
