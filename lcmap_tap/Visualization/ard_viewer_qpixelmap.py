import os
import sys
import traceback
from collections import namedtuple
import numpy as np
from osgeo import gdal
import time
import pkg_resources

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5 import QtWidgets, QtGui

from lcmap_tap.Visualization.ui_ard_viewer import Ui_ARDViewer
from lcmap_tap.Visualization.rescale import Rescale

# Import the CCDReader class which retrieves json and cache data
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData import RowColumn
from lcmap_tap.Plotting import plot_functions
from lcmap_tap.Visualization import tc_calculations
from lcmap_tap.Controls import units
from lcmap_tap.logger import log, exc_handler

# DATA_PATH = pkg_resources.resource_filename('lcmap_tap', 'Auxiliary')
# PNG_FILE = pkg_resources.resource_filename('lcmap_tap', os.path.join('Auxiliary', 'locator.png'))

sys.excepthook = exc_handler


class ImageViewer(QtWidgets.QGraphicsView):
    image_clicked = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self):
        super(ImageViewer, self).__init__()

        self._zoom = 0

        self._empty = True

        self.scene = QtWidgets.QGraphicsScene(self)

        self._image = QtWidgets.QGraphicsPixmapItem()

        self._mouse_button = None

        self.view_holder = None

        self.rect = None

        self.scene.addItem(self._image)

        self.setScene(self.scene)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))

        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def has_image(self):
        return not self._empty

    def fitInView(self, scale=True, **kwargs):
        self.rect = QtCore.QRectF(self._image.pixmap().rect())

        if not self.rect.isNull():
            self.setSceneRect(self.rect)

            if self.has_image():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))

                self.scale(1 / unity.width(), 1 / unity.height())

                view_rect = self.viewport().rect()

                scene_rect = self.transform().mapRect(self.rect)

                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())

                self.scale(factor, factor)

                self.view_holder = None

            self._zoom = 0

    def set_image(self, pixmap=None):
        # self._zoom = 0

        if pixmap and not pixmap.isNull():
            self._empty = False

            self._image.setPixmap(pixmap)

        else:
            self._empty = True

            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

            self._image.setPixmap(QtGui.QPixmap())

        if self.view_holder is None:
            self.fitInView()

        else:
            view_rect = self.viewport().rect()

            scene_rect = self.transform().mapRect(self.view_holder)

            factor = min(view_rect.width() / scene_rect.width(),
                         view_rect.height() / scene_rect.height())

            self.scale(factor, factor)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.has_image():
            if event.angleDelta().y() > 0:
                # angleDelta is (+), wheel is rotated forwards away from the user, zoom in
                factor = 1.25
                self._zoom += 1

            else:
                # angleDelta is (-), wheel is rotated backwards towards the user, zoom out
                factor = 0.8
                self._zoom -= 1

            if self._zoom > 0:
                self.scale(factor, factor)

            elif self._zoom == 0:
                self.fitInView()

            else:
                self._zoom = 0

    def toggle_drag(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

        elif not self._image.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event: QtGui.QMouseEvent):

        # 1 -> Left-click
        # 2 -> Right-click
        # 4 -> Wheel-click
        self._mouse_button = event.button()

        if event.button() == QtCore.Qt.RightButton:
            self.toggle_drag()

        if self._image.isUnderMouse() and event.button() == QtCore.Qt.LeftButton \
                and self.dragMode() == QtWidgets.QGraphicsView.NoDrag:
            point = self.mapToScene(event.pos())

            self.image_clicked.emit(QtCore.QPointF(point))

        super(ImageViewer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):

        # self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

        super(ImageViewer, self).mouseReleaseEvent(event)


class ARDViewerX(QtWidgets.QMainWindow):
    Bands = namedtuple('Bands', ['R', 'G', 'B'])

    band_nums = [1, 2, 3, 4, 5, 6]

    def __init__(self, ard_file, geo, sensor, gui):
        """

        Args:
            ard_file: List of the vsipaths associated with the current ard observation
            geo: A container for geographic reference information
            sensor:
            gui:

        """
        super(ARDViewerX, self).__init__()

        # Load the main GUI code that was built in Qt Designer
        self.ui = Ui_ARDViewer()

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))
        self.setWindowIcon(icon)

        # Call the method that builds the GUI window
        self.ui.setupUi(self)

        self.sizePolicy = None
        self.pixel_map = None
        self.R = None
        self.G = None
        self.B = None
        self.r = None
        self.g = None
        self.b = None
        self.qa = None
        self.img = None
        self.rgb = None
        self.index = None
        self.current_pixel = None
        self.new_ccd = None
        self.date_x = None
        self.data_y = None
        self.x_series = None
        self.y_series = None
        self.ax = None
        self.marker = None

        self.graphics_view = ImageViewer()

        self.ui.scrollArea.setWidget(self.graphics_view)

        # self.current_view = current_view

        self.ard_file = ard_file

        self.sensor = sensor

        self.geo_info = geo

        self.gui = gui

        self.pixel_rowcol = self.geo_info.geo_to_rowcol(affine=self.geo_info.PIXEL_AFFINE,
                                                        coord=self.geo_info.coord)

        self.row = self.pixel_rowcol.row

        self.col = self.pixel_rowcol.column

        # Set up some default settings
        self.bands = self.Bands(R=3, G=2, B=1)

        # self.extent = 500

        self.r_check, self.g_check, self.b_check = 0, 0, 0

        # Read in the full extent of the raster bands 1, 2, 3, and PIXELQA
        self.read_data()

        self.get_rgb()

        self.r_actions = [self.ui.actionBand_1, self.ui.actionBand_2, self.ui.actionBand_3, self.ui.actionBand_4,
                          self.ui.actionBand_5, self.ui.actionBand_6]

        self.g_actions = [self.ui.actionBand_7, self.ui.actionBand_8, self.ui.actionBand_9, self.ui.actionBand_10,
                          self.ui.actionBand_11, self.ui.actionBand_12]

        self.b_actions = [self.ui.actionBand_13, self.ui.actionBand_14, self.ui.actionBand_15, self.ui.actionBand_16,
                          self.ui.actionBand_17, self.ui.actionBand_18]

        self.lookup_r = {b: r_action for b, r_action in zip(self.band_nums, self.r_actions)}

        self.lookup_g = {b: g_action for b, g_action in zip(self.band_nums, self.g_actions)}

        self.lookup_b = {b: b_action for b, b_action in zip(self.band_nums, self.b_actions)}

        # Idea for using lambda to pass extra arguments to these slots came from:
        # https://eli.thegreenplace.net/2011/04/25/passing-extra-arguments-to-pyqt-slot
        # Selected R Channel
        self.ui.actionBand_1.triggered.connect(lambda: self.get_R(band=1))
        self.ui.actionBand_2.triggered.connect(lambda: self.get_R(band=2))
        self.ui.actionBand_3.triggered.connect(lambda: self.get_R(band=3))
        self.ui.actionBand_4.triggered.connect(lambda: self.get_R(band=4))
        self.ui.actionBand_5.triggered.connect(lambda: self.get_R(band=5))
        self.ui.actionBand_6.triggered.connect(lambda: self.get_R(band=6))

        # Select G Channel
        self.ui.actionBand_7.triggered.connect(lambda: self.get_G(band=1))
        self.ui.actionBand_8.triggered.connect(lambda: self.get_G(band=2))
        self.ui.actionBand_9.triggered.connect(lambda: self.get_G(band=3))
        self.ui.actionBand_10.triggered.connect(lambda: self.get_G(band=4))
        self.ui.actionBand_11.triggered.connect(lambda: self.get_G(band=5))
        self.ui.actionBand_12.triggered.connect(lambda: self.get_G(band=6))

        # Select B Channel
        self.ui.actionBand_13.triggered.connect(lambda: self.get_B(band=1))
        self.ui.actionBand_14.triggered.connect(lambda: self.get_B(band=2))
        self.ui.actionBand_15.triggered.connect(lambda: self.get_B(band=3))
        self.ui.actionBand_16.triggered.connect(lambda: self.get_B(band=4))
        self.ui.actionBand_17.triggered.connect(lambda: self.get_B(band=5))
        self.ui.actionBand_18.triggered.connect(lambda: self.get_B(band=6))

        self.ui.actionNDVI.triggered.connect(lambda: self.get_index("ndvi"))
        self.ui.actionMSAVI.triggered.connect(lambda: self.get_index("msavi"))
        self.ui.actionEVI.triggered.connect(lambda: self.get_index("evi"))
        self.ui.actionSAVI.triggered.connect(lambda: self.get_index("savi"))
        self.ui.actionNDMI.triggered.connect(lambda: self.get_index("ndmi"))
        self.ui.actionNBR.triggered.connect(lambda: self.get_index("nbr"))
        self.ui.actionNBR_2.triggered.connect(lambda: self.get_index("nbr2"))

        self.ui.actionTC.triggered.connect(self.get_tc)

        self.ui.update_button.clicked.connect(self.update_image)

        self.ui.actionSave_Image.triggered.connect(self.save_img)

        self.ui.actionExit.triggered.connect(self.exit)

        # Display the GUI for the user
        self.init_ui()

        self.display_img()

        self.make_rect()

        # self.add_marker()

        self.graphics_view.fitInView()

        self.ui.zoom_button.clicked.connect(self.zoom_to_point)

        self.graphics_view.image_clicked.connect(self.update_rect)

    def init_ui(self):
        """
        Initialize the map-viewer window
        Returns:

        """
        self.show()

    def exit(self):
        """
        Close the map-viewer window using File -> Exit, reset self.gui.ard to None so that clicking an observation
        invokes a new ARD viewer window.

        Returns:

        """
        self.gui.ard = None

        self.close()

    def closeEvent(self, event):
        """
        Override the close event to perform an action when the window is closed.  In this case, it is desired to have
        self.gui.ard be reset to None if the ARD viewer window is closed.  This way a new window will be invoked if
        a new observation is selected for display.

        Returns:
            None

        """
        self.gui.ard = None

        event.accept()

    def save_img(self):
        """

        Returns:

        """
        default_fmt = ".png"

        fmts = [".bmp", ".jpg", ".png"]

        try:
            browse = QtWidgets.QFileDialog.getSaveFileName()[0]

            # If no file extension was specified, make it .png
            if os.path.splitext(browse)[1] == '':
                browse = browse + default_fmt

            # If a file extension was specified, make sure it is valid for a QImage
            elif os.path.splitext(browse)[1] != '':

                if not any([f == os.path.splitext(browse)[1] for f in fmts]):
                    # If the file extension isn't valid, set it to .png instead
                    browse = os.path.splitext(browse)[0] + default_fmt

            self.img.save(browse, quality=100)

        except (TypeError, ValueError):
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            traceback.print_tb(sys.exc_info()[2])

    def display_img(self):
        """
        Show the ARD image

        Returns:

        """
        # Grab the current extent of the scene view so that the next image that gets opened is in the same extent
        self.graphics_view.view_holder = QtCore.QRectF(self.graphics_view.mapToScene(0, 0),
                                                       self.graphics_view.mapToScene(self.graphics_view.width(),
                                                                                     self.graphics_view.height()))

        try:
            self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

            self.pixel_map = QPixmap.fromImage(self.img)

            self.graphics_view.set_image(self.pixel_map)

            view_rect = self.graphics_view.viewport().rect()

            scene_rect = self.graphics_view.transform().mapRect(self.graphics_view.view_holder)

            factor = min(view_rect.width() / scene_rect.width(),
                         view_rect.height() / scene_rect.height())

            self.graphics_view.scale(factor, factor)

            # Set the scene rectangle to the original image size, which may be larger than the current view rect

            if not self.graphics_view.rect.isNull():
                self.graphics_view.setSceneRect(self.graphics_view.rect)

                # log.debug("self.graphics_view.rect used to set SceneRect")

        except AttributeError:
            pass

    def zoom_to_point(self):
        """
        Zoom to the selected point

        Returns:
            None

        """

        def check_upper(val, limit=0):
            for i in range(50, -1, -1):
                val_ul = val - i

                if val_ul > limit:
                    return val_ul

                elif val_ul < limit:
                    continue

                else:
                    return limit

        def check_lower(val, limit):
            for i in range(50, -1, -1):
                val_lr = val + i

                if val_lr < limit:
                    return val_lr

                elif val_lr > limit:
                    continue

                else:
                    return limit

        row_ul = check_upper(self.row)
        col_ul = check_upper(self.col)

        row_lr = check_lower(self.row, self.r.shape[0])
        col_lr = check_lower(self.col, self.r.shape[0])

        upper_left = QtCore.QPointF(col_ul, row_ul)
        bottom_right = QtCore.QPointF(col_lr, row_lr)

        rect = QtCore.QRectF(upper_left, bottom_right)

        view_rect = self.graphics_view.viewport().rect()

        scene_rect = self.graphics_view.transform().mapRect(rect)

        factor = min(view_rect.width() / scene_rect.width(),
                     view_rect.height() / scene_rect.height())

        self.graphics_view.scale(factor, factor)

        self.graphics_view.centerOn(self.current_pixel)

        # Arbitrary number of times to zoom out with the mouse wheel before full extent is reset
        self.graphics_view._zoom = 18

        self.graphics_view.view_holder = QtCore.QRectF(self.graphics_view.mapToScene(0, 0),
                                                       self.graphics_view.mapToScene(self.width(),
                                                                                     self.graphics_view.height()))

        # Set the scene rectangle to the original image size, which may be larger than the current view rect
        if not self.graphics_view.rect.isNull():
            self.graphics_view.setSceneRect(self.graphics_view.rect)

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

        :return:
        """
        try:
            self.r = gdal.Open(self.ard_file[self.bands.R - 1]).ReadAsArray()
            self.g = gdal.Open(self.ard_file[self.bands.G - 1]).ReadAsArray()
            self.b = gdal.Open(self.ard_file[self.bands.B - 1]).ReadAsArray()

            self.qa = gdal.Open(self.ard_file[-1]).ReadAsArray()

        except AttributeError:
            self.gui.ui.PlainTextEdit_results.appendPlainText("Could not open {}".format(self.ard_file))

    def get_rgb(self):
        """

        :return:
        """
        self.rgb = self.rescale_rgb(r=self.r, g=self.g, b=self.b, qa=self.qa)

        self.img = QImage(self.rgb.data, self.r.shape[0], self.r.shape[0], self.rgb.strides[0], QImage.Format_RGB888)

        self.img.ndarray = self.rgb

    def get_index(self, name: str):
        """
        Generate and display the index that was selected

        Args:
            name: The index name, used to identify the appropriate index calculation and input arguments

        Returns:
            None

        """

        def get_array(in_file):
            return gdal.Open(in_file, gdal.GA_ReadOnly).ReadAsArray()

        index_calc = {"ndvi": {"func": plot_functions.ndvi,
                               "args": {"R": get_array(self.ard_file[2]),
                                        "NIR": get_array(self.ard_file[3])}},
                      "msavi": {"func": plot_functions.msavi,
                                "args": {"R": get_array(self.ard_file[2]),
                                         "NIR": get_array(self.ard_file[3])}},
                      "savi": {"func": plot_functions.savi,
                               "args": {"R": get_array(self.ard_file[2]),
                                        "NIR": get_array(self.ard_file[3])}},
                      "evi": {"func": plot_functions.evi,
                              "args": {"B": get_array(self.ard_file[0]),
                                       "R": get_array(self.ard_file[2]),
                                       "NIR": get_array(self.ard_file[3])}},
                      "ndmi": {"func": plot_functions.ndmi,
                               "args": {"NIR": get_array(self.ard_file[3]),
                                        "SWIR1": get_array(self.ard_file[4])}},
                      "nbr": {"func": plot_functions.nbr,
                              "args": {"NIR": get_array(self.ard_file[3]),
                                       "SWIR2": get_array(self.ard_file[5])}},
                      "nbr2": {"func": plot_functions.nbr2,
                               "args": {"SWIR1": get_array(self.ard_file[4]),
                                        "SWIR2": get_array(self.ard_file[5])}}
                      }

        func = index_calc[name]["func"]

        self.index = func(**index_calc[name]["args"])

        self.qa = get_array(self.ard_file[-1])

        index_rescale = Rescale(sensor=self.sensor, array=self.index, qa=self.qa)

        self.rgb = np.zeros((self.r.shape[0], self.r.shape[0], 3), dtype=np.uint8)

        self.rgb[:, :, 0] = index_rescale.rescaled
        self.rgb[:, :, 1] = index_rescale.rescaled
        self.rgb[:, :, 2] = index_rescale.rescaled

        self.img = QImage(self.rgb.data, self.rgb[:, :, 0].shape[0], self.rgb[:, :, 0].shape[0],
                          self.rgb.strides[0], QImage.Format_RGB888)

        self.img.ndarray = self.rgb

        self.display_img()

    def get_tc(self):
        """

        Returns:

        """
        bright, green, wet = tc_calculations.get_tc_bands(self.sensor, self.ard_file)

        bright_rs = Rescale(self.sensor, bright, self.qa)

        green_rs = Rescale(self.sensor, green, self.qa)

        wet_rs = Rescale(self.sensor, wet, self.qa)

        self.rgb = np.zeros((self.r.shape[0], self.r.shape[0], 3), dtype=np.uint8)

        self.rgb[:, :, 0] = bright_rs.rescaled
        self.rgb[:, :, 1] = green_rs.rescaled
        self.rgb[:, :, 2] = wet_rs.rescaled

        self.img = QImage(self.rgb.data, self.rgb[:, :, 0].shape[0], self.rgb[:, :, 0].shape[0],
                          self.rgb.strides[0], QImage.Format_RGB888)

        self.img.ndarray = self.rgb

        self.display_img()

    def rescale_rgb(self, r, g, b, qa):
        """

        :param r:
        :param g:
        :param b:
        :param qa:
        :return:
        """
        rgb = np.zeros((self.r.shape[0], self.r.shape[0], 3), dtype=np.uint8)

        r_rescale = Rescale(sensor=self.sensor, array=r, qa=qa)
        g_rescale = Rescale(sensor=self.sensor, array=g, qa=qa)
        b_rescale = Rescale(sensor=self.sensor, array=b, qa=qa)

        rgb[:, :, 0] = r_rescale.rescaled
        rgb[:, :, 1] = g_rescale.rescaled
        rgb[:, :, 2] = b_rescale.rescaled

        return rgb

    def make_rect(self):
        """
        Create a rectangle on the image where the selected pixel location is located

        Returns:
            None

        """
        pen = QtGui.QPen(QtCore.Qt.cyan)
        pen.setWidthF(0.1)

        self.row = self.pixel_rowcol.row
        self.col = self.pixel_rowcol.column

        upper_left = QtCore.QPointF(self.col, self.row)
        bottom_right = QtCore.QPointF(self.col + 1, self.row + 1)

        self.current_pixel = QtWidgets.QGraphicsRectItem(QtCore.QRectF(upper_left, bottom_right))
        self.current_pixel.setPen(pen)

        self.graphics_view.scene.addItem(self.current_pixel)

    # def add_marker(self):
    #     """
    #     Add the marker icon to show where in the image the highlighted pixel is located
    #
    #     TODO: make the icon scalable
    #     TODO: only display the icon when zoomed out a specific level from the highlighted pixel
    #
    #     Returns:
    #
    #     """
    #     # Use the png file to create a QPixmap object
    #     self.marker = QtWidgets.QGraphicsPixmapItem(QPixmap(PNG_FILE))
    #
    #     # Get the bounding rectangle of the QPixmap object
    #     marker_rect = self.marker.boundingRect()
    #
    #     # Create a QPointF object based on the highlighted pixel row and column that represents the
    #     # center of the bottom edge of the QPixmap bounding rectangle
    #     marker_placement = QtCore.QPointF(self.col - marker_rect.width() / 2, self.row - marker_rect.height())
    #
    #     # Set the position of the marker
    #     self.marker.setPos(marker_placement)
    #
    #     # Add the QPixmap to the QGraphicsScene on the QGraphicsView
    #     # self.graphics_view.scene.addItem(self.marker)
    #
    #     # self.marker.setFlag(QtWidgets.QGraphicsPixmapItem.ItemIgnoresTransformations)

    # def remove_marker(self):
    #     """
    #     When the view port is at a certain zoom level, remove the marker
    #     Returns:
    #
    #     """
    #     if self.marker is not None:
    #         self.graphics_view.scene.removeItem(self.marker)

    def update_rect(self, pos: QtCore.QPointF):
        """
        Get new row/col when image is clicked, draw a new rectangle at that clicked row/col location
        Args:
            pos: Contains row and column of the scene location that was clicked

        Returns:

        """
        # Only draw a new plot and update the rectangle if this option is selected
        if self.ui.radioPlot.isChecked():
            # Remove the previous rectangle from the scene
            if self.current_pixel:
                self.graphics_view.scene.removeItem(self.current_pixel)

            pen = QtGui.QPen(QtCore.Qt.cyan)
            pen.setWidthF(0.1)

            self.row = int(pos.y())
            self.col = int(pos.x())

            upper_left = QtCore.QPointF(self.col, self.row)
            bottom_right = QtCore.QPointF(self.col + 1, self.row + 1)

            self.current_pixel = QtWidgets.QGraphicsRectItem(QtCore.QRectF(upper_left, bottom_right))
            self.current_pixel.setPen(pen)

            # self.graphics_view.scene.addRect(self.rect, pen)
            self.graphics_view.scene.addItem(self.current_pixel)

            time.sleep(1)

            self.update_plot()

    def update_plot(self):
        """
        Generate a new plot for the clicked point location

        Returns:
            None

        """
        # Before generating the new plot, create a reference to the previously clicked date and subplot
        self.ax = self.gui.plot_window.b  # Subplot name

        # log.debug("self.ax = %s" % self.ax)

        self.date_x = self.gui.plot_window.x  # Date in ordinal datetime format, the x coordinate

        # log.debug("self.date_x = %s" % self.date_x)

        # Gather information to retrieve necessary data for the new plot
        rowcol = RowColumn(row=self.row, column=self.col)

        coords = GeoInfo.rowcol_to_geo(affine=self.geo_info.PIXEL_AFFINE,
                                       rowcol=rowcol)

        log.info("New point selected: %s" % str(coords))

        # Update the X and Y coordinates in the GUI with the new point
        if units[self.gui.selected_units]["unit"] == "meters":

            self.gui.ui.LineEdit_x1.setText(str(coords.x))

            self.gui.ui.LineEdit_y1.setText(str(coords.y))

        # Convert to lat/long before updating the coordinate text on the GUI
        else:
            _coords = GeoInfo.unit_conversion(coords)

            self.gui.ui.LineEdit_x1.setText(str(_coords.x))

            self.gui.ui.LineEdit_y1.setText(str(_coords.y))

        # Do the plotting and generate a new figure
        self.gui.check_values()

        self.gui.plot()

        """Need to determine the y-axis value for the new time series.  Can be done by determining the index within
        the new time-series of the x-axis (i.e. date) value from the previous time series """
        x_look_thru = {"obs_points": self.gui.plot_specs.dates_in[self.gui.plot_specs.qa_mask[
            self.gui.plot_specs.date_mask]],

                       "out_points": self.gui.plot_specs.dates_out[self.gui.plot_specs.fill_out],

                       "mask_points": self.gui.plot_specs.dates_in[~self.gui.plot_specs.qa_mask[
                           self.gui.plot_specs.date_mask]]
                       }

        y_look_thru = {"obs_points": self.gui.plot_specs.all_lookup[self.ax][0][self.gui.plot_specs.date_mask][
            self.gui.plot_specs.qa_mask[
                self.gui.plot_specs.date_mask]],

                       "out_points": self.gui.plot_specs.all_lookup[self.ax][0][~self.gui.plot_specs.date_mask][
                           self.gui.plot_specs.fill_out],

                       "mask_points": self.gui.plot_specs.all_lookup[self.ax][0][self.gui.plot_specs.date_mask][
                           ~self.gui.plot_specs.qa_mask[
                               self.gui.plot_specs.date_mask]]
                       }

        for key, x in x_look_thru.items():
            if self.date_x in x:
                log.info("Found date clicked %s in %s" % (self.date_x, key))

                self.x_series = x

                self.y_series = y_look_thru[key]

                break

        #: int: the location of the date in the new time series
        ind = np.where(self.x_series == self.date_x)

        #: the reflectance or index value for the new time series
        self.data_y = np.take(self.y_series, ind)

        # log.debug("Y-series value returned: %s" % self.data_y)

        # log.debug("From plot_window X: %s" % self.date_x)

        # log.debug("From plot_window Y: %s" % self.data_y)

        # Display the highlighted pixel in the new plot
        highlight = self.gui.plot_window.artist_map[self.ax][0]

        # log.debug("method update_plot, highlight=%s" % str(highlight))

        # highlight.set_data(self.date_x[0], self.data_y[0])
        highlight.set_data(self.date_x, self.data_y)

        self.gui.plot_window.canvas.draw()

        # Clear the list of previously clicked ARD observations because they can't be referenced in the new time-series
        self.gui.ui.ListWidget_selected.clear()
