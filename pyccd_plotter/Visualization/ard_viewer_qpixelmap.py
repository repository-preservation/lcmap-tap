import sys
import traceback
from collections import namedtuple

import numpy as np
from osgeo import gdal

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtWidgets import QMainWindow, QSizePolicy, QLabel

from pyccd_plotter.Visualization.ui_image_viewer import Ui_ARDViewer

from pyccd_plotter.Visualization.rescale import Rescale


class ARDViewerX(QMainWindow):

    Bands = namedtuple('Bands', ['R', 'G', 'B'])

    def __init__(self, ard_file, ccd, gui):
        super(ARDViewerX, self).__init__()

        # Load the main GUI code that was built in Qt Designer
        self.ui = Ui_ARDViewer()

        # Call the method that builds the GUI window
        self.ui.setupUi(self)

        # Create an empty QLabel object that will be used to display imagery
        self.imgLabel = QLabel()

        # Add the QLabel to the QScrollArea
        self.ui.scrollArea.setWidget(self.imgLabel)

        self.ard_file = ard_file

        self.ccd = ccd

        self.gui = gui

        # Set up some default settings
        self.bands = self.Bands(R=3, G=2, B=1)
        self.extent = 500
        self.r_check, self.g_check, self.b_check = 0, 0, 0

        # Read in the full extent of the raster bands 1, 2, 3, and PIXELQA
        self.read_data()

        self.get_rgb()

        self.band_nums = [1, 2, 3, 4, 5, 6]

        self.r_actions = [self.ui.actionBand_1, self.ui.actionBand_2, self.ui.actionBand_3, self.ui.actionBand_4,
                     self.ui.actionBand_5, self.ui.actionBand_6]

        self.g_actions = [self.ui.actionBand_7, self.ui.actionBand_8, self.ui.actionBand_9, self.ui.actionBand_10,
                     self.ui.actionBand_11, self.ui.actionBand_12]

        self.b_actions = [self.ui.actionBand_13, self.ui.actionBand_14, self.ui.actionBand_15, self.ui.actionBand_16,
                     self.ui.actionBand_17, self.ui.actionBand_18]

        self.lookup_r = {b: r_action for b, r_action in zip(self.band_nums, self.r_actions)}

        self.lookup_g = {b: g_action for b, g_action in zip(self.band_nums, self.g_actions)}

        self.lookup_b = {b: b_action for b, b_action in zip(self.band_nums, self.b_actions)}

        self.extents = [100, 250, 500, 1000, 'full']

        self.extent_actions = [self.ui.action100x100, self.ui.action250x250,
                               self.ui.action500x500, self.ui.action1000x1000, self.ui.actionFull]

        self.lookup_extent = {e: extent_action for e, extent_action in zip(self.extents, self.extent_actions)}

        # Idea for using lambda to pass extra arguments to these slots came from:
        # https://eli.thegreenplace.net/2011/04/25/passing-extra-arguments-to-pyqt-slot
        self.ui.actionBand_1.triggered.connect(lambda: self.get_R(band=1))
        self.ui.actionBand_2.triggered.connect(lambda: self.get_R(band=2))
        self.ui.actionBand_3.triggered.connect(lambda: self.get_R(band=3))
        self.ui.actionBand_4.triggered.connect(lambda: self.get_R(band=4))
        self.ui.actionBand_5.triggered.connect(lambda: self.get_R(band=5))
        self.ui.actionBand_6.triggered.connect(lambda: self.get_R(band=6))

        self.ui.actionBand_7.triggered.connect(lambda: self.get_G(band=1))
        self.ui.actionBand_8.triggered.connect(lambda: self.get_G(band=2))
        self.ui.actionBand_9.triggered.connect(lambda: self.get_G(band=3))
        self.ui.actionBand_10.triggered.connect(lambda: self.get_G(band=4))
        self.ui.actionBand_11.triggered.connect(lambda: self.get_G(band=5))
        self.ui.actionBand_12.triggered.connect(lambda: self.get_G(band=6))

        self.ui.actionBand_13.triggered.connect(lambda: self.get_B(band=1))
        self.ui.actionBand_14.triggered.connect(lambda: self.get_B(band=2))
        self.ui.actionBand_15.triggered.connect(lambda: self.get_B(band=3))
        self.ui.actionBand_16.triggered.connect(lambda: self.get_B(band=4))
        self.ui.actionBand_17.triggered.connect(lambda: self.get_B(band=5))
        self.ui.actionBand_18.triggered.connect(lambda: self.get_B(band=6))

        self.ui.action100x100.triggered.connect(lambda: self.set_extent(extent=100))
        self.ui.action250x250.triggered.connect(lambda: self.set_extent(extent=250))
        self.ui.action500x500.triggered.connect(lambda: self.set_extent(extent=500))
        self.ui.action1000x1000.triggered.connect(lambda: self.set_extent(extent=1000))
        self.ui.actionFull.triggered.connect(lambda: self.set_extent(extent='full'))

        self.ui.update_button.clicked.connect(self.update_image)

        # Display the GUI for the user
        self.init_ui()

        self.display_img()

    def init_ui(self):
        """

        :return:
        """
        self.show()

    def display_img(self):
        """
        Show the image file
        :return:
        """
        try:
            # self.sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

            self.imgLabel.setSizePolicy(self.sizePolicy)

            # Maintain the image native ratio
            self.imgLabel.setScaledContents(False)

            # Trial and error found this to be the correct way to assemble the image.  Otherwise you end up
            # with a rotated and/or mirrored image.  This is however incredibly inefficient.  I'm leaving the code
            # in for reference.  This took approximately 70 seconds to load a 5000x5000 pixel image.  Now it takes
            # less than 3 seconds to load in the full extent image.
            # for y in range(self.extent):
            #     for x in range(self.extent):
            #         try:
            #             self.img.setPixel(x, y, QColor(*self.rgb[y][x]).rgb())
            #
            #         except:
            #             print(sys.exc_info()[0])
            #             print(sys.exc_info()[1])
            #             traceback.print_tb(sys.exc_info()[2])

            # self.pixel_map = QPixmap(self.img_file)

            self.pixel_map = QPixmap.fromImage(self.img)

            # self.imgLabel.setPixmap(self.pixel_map)

            self.imgLabel.setPixmap(self.pixel_map.scaled(self.imgLabel.size(),
                                                          QtCore.Qt.KeepAspectRatio,
                                                          transformMode=QtCore.Qt.SmoothTransformation))

        except AttributeError:
            pass

    def resizeimg(self):
        """

        :return:
        """
        try:
            self.sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.imgLabel.setSizePolicy(self.sizePolicy)

            self.imgLabel.setPixmap(self.pixel_map.scaled(self.imgLabel.size(),
                                                          QtCore.Qt.KeepAspectRatio,
                                                          transformMode=QtCore.Qt.SmoothTransformation))

        except AttributeError:
            pass

    def resizeEvent(self, event):
        """

        :param **kwargs:
        :return:
        """
        try:
            sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

            self.imgLabel.setSizePolicy(sizePolicy)

            self.imgLabel.setPixmap(self.pixel_map.scaled(self.imgLabel.size(),
                                                          QtCore.Qt.KeepAspectRatio,
                                                          transformMode=QtCore.Qt.SmoothTransformation))
        except AttributeError:
            pass

    def get_R(self, band):
        """

        :param band:
        :return:
        """
        # self.R = band

        # Turn off other checked bands (previously checked band)
        for key in self.lookup_r.keys():
            if not key == band:
                self.lookup_r[key].setChecked(False)

        # Get only the checked band
        for key in self.lookup_r.keys():
            if self.lookup_r[key].isChecked():
                self.R = key

                self.r_check = 1

                break

            else:
                self.r_check = 0

    def get_G(self, band):
        """

        :param band:
        :return:
        """
        # self.G = band

        # Turn off other checked bands (previously checked band)
        for key in self.lookup_g.keys():
            if not key == band:
                self.lookup_g[key].setChecked(False)

        # Get only the checked band
        for key in self.lookup_g.keys():
            if self.lookup_g[key].isChecked():
                self.G = key

                self.g_check = 1

                break

            else:
                self.g_check = 0

    def get_B(self, band):
        """

        :param band:
        :return:
        """
        # self.B = band

        # Turn off other checked bands (previously checked band)
        for key in self.lookup_b.keys():
            if not key == band:
                self.lookup_b[key].setChecked(False)

        # Get only the checked band
        for key in self.lookup_b.keys():
            if self.lookup_b[key].isChecked():
                self.B = key

                self.b_check = 1

                break

            else:
                self.b_check = 0

    def set_bands(self):
        """

        :return:
        """
        try:
            self.bands = self.Bands(R=self.R, G=self.G, B=self.B)
            self.read_data()
            # self.get_rgb()

        except AttributeError:
            self.bands = self.Bands(R=3, G=2, B=1)
            self.read_data()
            # self.get_rgb()

        print('Bands: ', self.bands)

    def set_extent(self, extent):
        """

        :return:
        """
        for key in self.lookup_extent.keys():
            if not key == extent:
                self.lookup_extent[key].setChecked(False)

        # Get only the checked extent
        for key in self.lookup_extent.keys():
            if self.lookup_extent[key].isChecked():
                extent = key

        if extent == 'full':
            self.extent = self.r.shape[0]

        else:
            self.extent = extent

        self.get_rgb()

        self.display_img()

    def update_image(self):
        """

        :return:
        """
        try:
            if self.r_check + self.g_check + self.b_check == 3:
                self.bands = self.Bands(R=self.R, G=self.G, B=self.B)

                self.read_data()

                self.get_rgb()

                self.display_img()

            else:
                self.get_rgb()

                self.display_img()

        except AttributeError:
            pass

    def read_data(self):
        """

        :param src_file:
        :return:
        """
        src = gdal.Open(self.ard_file, gdal.GA_ReadOnly)

        if src is None:
            self.gui.ui.plainTextEdit_results.appendPlainText("Could not open {}".format(self.ard_file))

        self.r = src.GetRasterBand(self.bands.R).ReadAsArray()
        self.g = src.GetRasterBand(self.bands.G).ReadAsArray()
        self.b = src.GetRasterBand(self.bands.B).ReadAsArray()

        band_count = src.RasterCount

        if band_count == 7:
            self.qa = src.GetRasterBand(7).ReadAsArray()

        elif band_count == 8:
            self.qa = src.GetRasterBand(8).ReadAsArray()
        # TODO error handling if raster count is not 7 or 8

        else:
            self.qa = np.zeros_like(self.r)
            self.qa[self.r == -9999] = 1

        src = None

    def get_rgb(self):
        """

        :return:
        """
        # Display the full extent of the image
        if self.extent == self.r.shape[0]:

            self.rgb = self.rescale_rgb(r=self.r, g=self.g, b=self.b, qa=self.qa)

            # self.rgb = np.require(self.rgb, np.uint8, 'C')

            self.img = QImage(self.rgb.data, self.extent, self.extent, self.rgb.strides[0], QImage.Format_RGB888)

            self.img.ndarray = self.rgb

        # Display a smaller extent taken from the image
        else:
            pixel_rowcol = self.ccd.geo_to_rowcol(affine=self.ccd.PIXEL_AFFINE, coord=self.ccd.coord)

            row = pixel_rowcol.row - int(self.extent / 2.)
            column = pixel_rowcol.column - int(self.extent / 2.)

            # Make sure that the extent doesn't go off of the main image extent
            if row < 0:
                row = 0
            elif row + self.extent > self.r.shape[0]:
                row = self.r.shape[0] - self.extent
            else:
                pass

            if column < 0:
                column = 0
            elif column + self.extent > self.r.shape[1]:
                column = self.r.shape[1] - self.extent
            else:
                pass

            ul_rowcol = self.ccd.RowColumn(row=row, column=column)

            r = self.r[ul_rowcol.row: ul_rowcol.row + self.extent, ul_rowcol.column: ul_rowcol.column + self.extent]
            g = self.g[ul_rowcol.row: ul_rowcol.row + self.extent, ul_rowcol.column: ul_rowcol.column + self.extent]
            b = self.b[ul_rowcol.row: ul_rowcol.row + self.extent, ul_rowcol.column: ul_rowcol.column + self.extent]
            qa = self.qa[ul_rowcol.row: ul_rowcol.row + self.extent, ul_rowcol.column: ul_rowcol.column + self.extent]

            self.rgb = self.rescale_rgb(r=r, g=g, b=b, qa=qa)

            # self.rgb = np.require(self.rgb, np.uint8, 'C')

            self.img = QImage(self.rgb.data, self.extent, self.extent, self.rgb.strides[0], QImage.Format_RGB888)

            self.img.ndarray = self.rgb

    def rescale_rgb(self, r, g, b, qa):
        """

        :param infile:
        :param r:
        :param g:
        :param b:
        :param qa:
        :param extent:
        :return:
        """

        rgb = np.zeros((self.extent, self.extent, 3), dtype=np.uint8)

        r_rescale = Rescale(src_file=self.ard_file, array=r, qa=qa)
        g_rescale = Rescale(src_file=self.ard_file, array=g, qa=qa)
        b_rescale = Rescale(src_file=self.ard_file, array=b, qa=qa)

        rgb[:, :, 0] = b_rescale.rescaled
        rgb[:, :, 1] = g_rescale.rescaled
        rgb[:, :, 2] = r_rescale.rescaled

        return rgb
