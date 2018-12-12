"""Make a QWidget that will hold a matplotlib figure to visualize a mosaic of ARD chips"""

from lcmap_tap.logger import log, exc_handler
from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.RetrieveData.retrieve_chips import Chips
from lcmap_tap.Visualization.chipviewer_main import Ui_MainWindow_chipviewer

import os
import sys
import time
import datetime as dt
import matplotlib.pyplot as plt

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow

sys.excepthook = exc_handler


def get_time():
    """
    Return the current time stamp

    Returns:
        A formatted string containing the current date and time

    """
    return time.strftime("%Y%m%d-%H%M%S")


class ImageViewer(QtWidgets.QGraphicsView):
    image_clicked = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self):
        super().__init__()

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


class ChipsViewerX(QMainWindow):
    channel_lookup = {'Blue': ['blues'],
                      'Green': ['greens'],
                      'Red': ['reds'],
                      'NIR': ['nirs'],
                      'SWIR-1': ['swir1s'],
                      'SWIR-2': ['swir2s'],
                      'Thermal': ['thermals'],
                      'NDVI': ['reds', 'nirs'],
                      'MSAVI': ['reds', 'nirs'],
                      'SAVI': ['reds', 'nirs'],
                      'EVI': ['blues', 'reds', 'nirs'],
                      'NDMI': ['nirs', 'swir1s'],
                      'NBR-1': ['nirs', 'swir2s'],
                      'NBR-2': ['swir1s', 'swir2s']}

    channels = {'r_channel': ('Red', channel_lookup['Red']),
                'g_channel': ('Green', channel_lookup['Green']),
                'b_channel': ('Blue', channel_lookup['Blue'])}

    update_plot_signal = QtCore.pyqtSignal(object)

    def __init__(self, x, y, date, url, subplot, geo, r, g, b, outdir):
        """

        Args:
            x:
            y:
            date:
            url:
            subplot:
            geo:
            r:
            g:
            b:
        """
        super().__init__()

        self.x = x
        self.y = y
        self.date = date
        self.url = url
        self.r = r
        self.g = g
        self.b = b
        self.working_dir = outdir

        self.fig_num = 1

        self.geo_info = geo

        self.ui = Ui_MainWindow_chipviewer()

        self.ui.setupUi(self)

        self.ui.ComboBox_red.setCurrentIndex(self.r)
        self.ui.ComboBox_green.setCurrentIndex(self.g)
        self.ui.ComboBox_blue.setCurrentIndex(self.b)

        self.lower = float(self.ui.LineEdit_lower.text())
        self.upper = float(self.ui.LineEdit_upper.text())

        self.chips = Chips(x=self.x, y=self.y, date=self.date, url=self.url,
                           lower=self.lower, upper=self.upper, **self.channels)

        self.pixel_image_affine = GeoInfo.get_affine(self.chips.chips_ul.x, self.chips.chips_ul.y)

        self.pixel_rowcol = GeoInfo.geo_to_rowcol(affine=self.pixel_image_affine, coord=self.geo_info.coord)

        self.row = self.pixel_rowcol.row

        self.col = self.pixel_rowcol.column

        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.graphics_view = ImageViewer()

        self.ui.ScrollArea_viewer.setWidget(self.graphics_view)

        self.img = QImage(self.chips.rgb.data, self.chips.rgb.shape[1], self.chips.rgb.shape[0],
                          self.chips.rgb.strides[0],
                          QImage.Format_RGB888)

        self.img.ndarray = self.chips.rgb

        self.display_img()

        self.make_rect()

        self.init_ui()

        self.graphics_view.fitInView()

        # Before generating the new plot, create a reference to the previously clicked date and subplot
        self.ax = subplot

        self.date_x = self.date.toordinal()  # Date in ordinal datetime format, the x coordinate

        self.ui.PushButton_update.clicked.connect(self.update_channels)

        self.ui.PushButton_zoom.clicked.connect(self.zoom_to_point)

        self.graphics_view.image_clicked.connect(self.update_rect)

        self.ui.PushButton_save.clicked.connect(self.save_img)

    def init_ui(self):
        self.show()

    def update_percentiles(self):
        try:
            self.lower = float(self.ui.LineEdit_lower.text())

            self.upper = float(self.ui.LineEdit_upper.text())

        except (ValueError, TypeError):
            self.lower = 1.0

            self.upper = 99.0

            self.ui.LineEdit_lower.setText('1.0')

            self.ui.LineEdit_upper.setText('99.0')

    def save_img(self):
        """

        Returns:

        """
        date = self.date.strftime('%Y%m%d')

        r = self.ui.ComboBox_red.currentText().lower()
        g = self.ui.ComboBox_green.currentText().lower()
        b = self.ui.ComboBox_blue.currentText().lower()

        try:
            outdir = self.working_dir

            if r == b and r == g:
                outfile = os.path.join(outdir, f'{r}_{date}_{get_time()}.png')

            else:
                outfile = os.path.join(outdir, f'{r}_{g}_{b}_{date}_{get_time()}.png')

            fig, ax = plt.subplots(figsize=(10, 10), num=f'ard_figure_{self.fig_num}')

            # Make sure that the ARD figure is active
            plt.figure(f'ard_figure_{self.fig_num}')

            plt.axis('off')

            ax.grid(False)

            center = self.chips.tile_geo.chip_coord_ul

            _date = dt.datetime.fromordinal(self.chips.grid[center]['data'][0][1]['dates']
                                            [self.chips.grid[center]['ind']]).strftime('%Y-%m-%d')

            title = f'Date: {_date}'

            text = f'X: {self.x}\nY: {self.y}'

            ax.set_title(title)

            ax.imshow(self.chips.rgb, interpolation='nearest')

            ax.scatter(x=self.col, y=self.row, marker='s', facecolor='none',
                       color='yellow', s=15, linewidth=1)

            ax.text(0, -.01, text, horizontalalignment='left', verticalalignment='top', transform=ax.transAxes)

            plt.savefig(outfile, bbox_inches='tight', dpi=200)

            log.debug("Plot figure saved to file {}".format(outfile))

            plt.gcf().clear()

            self.fig_num += 1

        except (TypeError, ValueError) as e:
            log.error('ARD save_img raised exception: %s' % e, exc_info=True)

    def update_channels(self):
        """
        Update which channels have been selected for visualization

        """
        self.channels['r_channel'] = (self.ui.ComboBox_red.currentText(),
                                      self.channel_lookup[self.ui.ComboBox_red.currentText()])

        self.channels['g_channel'] = (self.ui.ComboBox_green.currentText(),
                                      self.channel_lookup[self.ui.ComboBox_green.currentText()])

        self.channels['b_channel'] = (self.ui.ComboBox_blue.currentText(),
                                      self.channel_lookup[self.ui.ComboBox_blue.currentText()])

        self.r = self.ui.ComboBox_red.currentIndex()
        self.g = self.ui.ComboBox_green.currentIndex()
        self.b = self.ui.ComboBox_blue.currentIndex()

        self.update_percentiles()

        self.chips = Chips(x=self.x, y=self.y, date=self.date, url=self.url,
                           lower=self.lower, upper=self.upper, **self.channels)

        self.img = QImage(self.chips.rgb.data, self.chips.rgb.shape[1], self.chips.rgb.shape[0],
                          self.chips.rgb.strides[0],
                          QImage.Format_RGB888)

        self.img.ndarray = self.chips.rgb

        self.display_img()

        self.make_rect()

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

        row_lr = check_lower(self.row, self.chips.rgb.shape[0])
        col_lr = check_lower(self.col, self.chips.rgb.shape[0])

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
        self.graphics_view._zoom = 5

        self.graphics_view.view_holder = QtCore.QRectF(self.graphics_view.mapToScene(0, 0),
                                                       self.graphics_view.mapToScene(self.width(),
                                                                                     self.graphics_view.height()))

        # Set the scene rectangle to the original image size, which may be larger than the current view rect
        if not self.graphics_view.rect.isNull():
            self.graphics_view.setSceneRect(self.graphics_view.rect)

    def make_rect(self):
        """
        Create a rectangle on the image where the selected pixel location is located

        Returns:
            None

        """
        pen = QtGui.QPen(QtCore.Qt.yellow)
        pen.setWidthF(0.3)

        upper_left = QtCore.QPointF(self.col, self.row)
        bottom_right = QtCore.QPointF(self.col + 1, self.row + 1)

        self.current_pixel = QtWidgets.QGraphicsRectItem(QtCore.QRectF(upper_left, bottom_right))
        self.current_pixel.setPen(pen)

        self.graphics_view.scene.addItem(self.current_pixel)

    def update_rect(self, pos: QtCore.QPointF):
        """
        Get new row/col when image is clicked, draw a new rectangle at that clicked row/col location
        Args:
            pos: Contains row and column of the scene location that was clicked

        Returns:

        """
        # Only draw a new plot and update the rectangle if this option is selected
        if self.ui.RadioButton_plot.isChecked():
            # Remove the previous rectangle from the scene
            # if self.current_pixel:
            self.graphics_view.scene.removeItem(self.current_pixel)

            time.sleep(1)

            pen = QtGui.QPen(QtCore.Qt.yellow)
            pen.setWidthF(0.3)

            self.row = int(pos.y())
            self.col = int(pos.x())

            upper_left = QtCore.QPointF(self.col, self.row)
            bottom_right = QtCore.QPointF(self.col + 1, self.row + 1)

            self.current_pixel = QtWidgets.QGraphicsRectItem(QtCore.QRectF(upper_left, bottom_right))
            self.current_pixel.setPen(pen)

            self.graphics_view.scene.addItem(self.current_pixel)

            time.sleep(1)

            signal = (self.row, self.col)

            self.update_plot_signal.emit(signal)

    def exit(self):
        self.close()
