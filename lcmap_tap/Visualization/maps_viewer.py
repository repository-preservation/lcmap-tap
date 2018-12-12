"""A window for displaying mapped products"""

import os
import sys
import glob
import pkg_resources

from PyQt5.QtCore import pyqtSignal, QPointF, QRectF, Qt
from PyQt5.QtGui import QPixmap, QBrush, QPen, QColor, QMouseEvent, QWheelEvent, QIcon
from PyQt5.QtWidgets import QFrame, QSlider, QMainWindow, QGraphicsView, QGraphicsScene, \
    QGraphicsPixmapItem, QGraphicsRectItem, QSizePolicy

from lcmap_tap.Visualization.ui_maps_viewer import Ui_MapViewer
from lcmap_tap.Visualization import PRODUCTS, VERSIONS
from lcmap_tap.logger import log, exc_handler

sys.excepthook = exc_handler


class ImageViewer(QGraphicsView):
    image_clicked = pyqtSignal(QPointF)

    def __init__(self):
        super(ImageViewer, self).__init__()

        self._zoom = 0

        self._empty = True

        self.scene = QGraphicsScene(self)

        self._image = QGraphicsPixmapItem()

        self._mouse_button = None

        self.view_holder = None

        self.scene.addItem(self._image)

        self.setScene(self.scene)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.setFrameShape(QFrame.NoFrame)

    def has_image(self):
        return not self._empty

    def fitInView(self, scale=True, **kwargs):
        rect = QRectF(self._image.pixmap().rect())

        if not rect.isNull():
            self.setSceneRect(rect)

            if self.has_image():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))

                self.scale(1 / unity.width(), 1 / unity.height())

                view_rect = self.viewport().rect()

                scene_rect = self.transform().mapRect(rect)

                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())

                self.scale(factor, factor)

                # Reset the view holder to None
                self.view_holder = None

            self._zoom = 0

    def set_image(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self._empty = False

            self._image.setPixmap(pixmap)

        else:
            self._empty = True

            self.setDragMode(QGraphicsView.NoDrag)

            self._image.setPixmap(QPixmap())

        if not self.view_holder:
            self.fitInView()

        else:
            view_rect = self.viewport().rect()

            scene_rect = self.transform().mapRect(self.view_holder)

            factor = min(view_rect.width() / scene_rect.width(),
                         view_rect.height() / scene_rect.height())

            self.scale(factor, factor)

    def wheelEvent(self, event: QWheelEvent):
        if self.has_image():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1

            else:
                factor = 0.8
                self._zoom -= 1

            if self._zoom > 0:
                self.scale(factor, factor)

            elif self._zoom == 0:
                self.fitInView()

            else:
                self._zoom = 0

        self.view_holder = QRectF(self.mapToScene(0, 0), self.mapToScene(self.width(), self.height()))

    def toggle_drag(self):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)

        elif not self._image.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event: QMouseEvent):
        # 1 -> Left-click
        # 2 -> Right-click
        # 4 -> Wheel-click
        self._mouse_button = event.button()

        if event.button() == Qt.RightButton:
            self.toggle_drag()

        if self._image.isUnderMouse() and event.button() == Qt.LeftButton \
                and self.dragMode() == QGraphicsView.NoDrag:
            point = self.mapToScene(event.pos())

            log.debug("point %s" % str(point))

            self.image_clicked.emit(QPointF(point))

        super(ImageViewer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

        super(ImageViewer, self).mouseReleaseEvent(event)


class MapsViewer(QMainWindow):
    def __init__(self, tile, root, geo, version, begin_year=1984, end_year=2015):

        super(MapsViewer, self).__init__()

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))

        self.setWindowIcon(icon)

        self.tile = tile

        self.root = root

        self.geo_info = geo

        self.current_pixel = None

        self.pixel_rowcol = self.geo_info.geo_to_rowcol(affine=self.geo_info.PIXEL_AFFINE,
                                                        coord=self.geo_info.coord)

        self.row = self.pixel_rowcol.row

        self.col = self.pixel_rowcol.column

        log.debug("MAP VIEWER, tile_pixel_rowcol: %s" % str(self.pixel_rowcol))

        if not os.path.exists(os.path.join(self.root, version)):
            self.version = self.get_version()

        else:
            self.version = version

        self.root = os.path.join(self.root, self.version)

        log.info("MAP VIEWER using version %s" % self.version)

        log.debug("MAP VIEWER, root: %s" % self.root)

        self.get_product_root_directories()

        self.ui = Ui_MapViewer()

        self.ui.setupUi(self)

        self.graphics_view = ImageViewer()

        self.ui.scrollArea.setWidget(self.graphics_view)

        self.img_list1 = list()

        self.pixel_map = None

        self.ui.date_slider.setMinimum(begin_year)

        self.ui.date_slider.setMaximum(end_year)

        self.ui.date_slider.setTickPosition(QSlider.TicksBothSides)

        self.ui.date_slider.setTickInterval(1)

        # This show's the left-most value of the time slider initially, 1984
        self.ui.show_date.setText(str(self.ui.date_slider.value()))

        self.ui.move_left.clicked.connect(self.move_left)

        self.ui.move_right.clicked.connect(self.move_right)

        self.ui.date_slider.valueChanged.connect(self.date_changed)

        self.ui.pushButton_zoom.clicked.connect(self.zoom_to_point)

        self.ui.comboBox_map1.currentIndexChanged.connect(self.browse_map)

        self.ui.exit_QPush.clicked.connect(self.exit)

        self.make_rect()

        self.init_ui()

    def init_ui(self):
        """
        Display the GUI
        :return:
        """
        self.show()

    def get_version(self) -> str:
        """
        Determine which version of pyccd products to use if the selected version doesn't match with what's present

        Returns:
            version: The version identifier

        """
        for version in VERSIONS:
            temp_look = os.path.join(self.root, version)

            if os.path.exists(temp_look):

                change_test = os.path.join(temp_look, "ChangeMaps")
                cover_test = os.path.join(temp_look, "CoverMaps")

                if os.path.exists(change_test) and os.path.exists(cover_test):

                    return version

                else:
                    continue

            else:
                continue

    def get_product_root_directories(self):
        """
        Construct the full path to the change/cover product subdirectories using the most recent version available.
        Store the full path in the products dict under keyword "root"

        Returns:
            None

        """
        for product in PRODUCTS.keys():
            PRODUCTS[product]["root"] = os.path.join(self.root, PRODUCTS[product]["type"],
                                                     PRODUCTS[product]["alias"])

            log.debug("MAPS VIEWER, %s root dir: %s" % (str(product), str(PRODUCTS[product]["root"])))

        return None

    def move_left(self):
        """
        Move the slider one increment to the left

        Returns:

        """
        try:
            val = self.ui.date_slider.value()
            val = val - 1
            self.ui.date_slider.setSliderPosition(val)

        except (ValueError, AttributeError, KeyError):
            pass

    def move_right(self):
        """
        Move the slider one increment to the right

        Returns:

        """
        try:
            val = self.ui.date_slider.value()
            val = val + 1
            self.ui.date_slider.setSliderPosition(val)

        except (ValueError, AttributeError, KeyError):
            pass

    def get_items(self):
        """
        Populate the Maps Menu with the available products

        Returns:
            None

        """
        # Get the subfolders
        product_folders = list()

        for x in os.listdir(self.root):
            if os.path.isdir(x) and (x == "ChangeMaps" or x == "CoverMaps"):
                product_folders.append(os.path.join(self.root, x))

        log.debug("MAPS VIEWER, product_folders: %s" % str(product_folders))

        sub_folders = list()

        for prod_folder in product_folders:
            for root, folders, files in os.walk(prod_folder):
                for folder in folders:
                    sub_folders.append(os.path.join(root, folder))

        log.debug("MAPS VIEWER, sub_folders: %s" % str(sub_folders))

    def show_image(self, key, imgs=None):
        """
        Display the image

        Args:
            key:
            imgs:

        Returns:

        """
        input_dir = self.action_mapper1[key][1]

        log.debug("MAPS VIEWER, show_image-> input_dir: %s" % input_dir)

        if imgs is None:
            imgs = glob.glob(input_dir + os.sep + "*.tif")

        log.debug("MAPS VIEWER, show_image-> imgs: %s" % str(imgs))

        self.pixel_map = QPixmap(imgs[0])

        self.graphics_view.set_image(self.pixel_map)

    def date_changed(self, value):
        """
        Display the current year,
        :param value: Parameter passed by the valueChanged(int) signal
        :type value: int
        :return:
        """
        self.ui.show_date.setText(str(value))

        # Grab the current extent of the scene view so that the next image that gets opened is in the same extent
        self.graphics_view.view_holder = QRectF(self.graphics_view.mapToScene(0, 0),
                                                self.graphics_view.mapToScene(self.graphics_view.width(),
                                                                              self.graphics_view.height()))

        try:
            temp1 = [img for img in self.img_list1 if str(value) in img][0]
            self.pixel_map = QPixmap(temp1)

            self.graphics_view.set_image(self.pixel_map)

            if self.graphics_view.view_holder:
                view_rect = self.graphics_view.viewport().rect()

                scene_rect = self.graphics_view.transform().mapRect(self.graphics_view.view_holder)

                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())

                self.graphics_view.scale(factor, factor)

        except (TypeError, IndexError, AttributeError):
            pass

    def get_product_specs(self, product):
        """
        Retrieve information on the selected product

        Returns:

        """
        cat = PRODUCTS[product]["type"]

        folder = PRODUCTS[product]["alias"]

        # A 16-bit product, needs extra work for display
        if product == "Change DOY":
            folder = "ChangeMaps-{}".format(self.version)

            temp_folder = self.root_dir + os.sep + folder

            if not os.path.exists(temp_folder):
                return False

            else:
                return cat, folder, temp_folder

        # Just want to show the raw output for the cover confidence
        if "Confidence" in product:
            folder = "CoverMaps-{}".format(self.version)

            temp_folder = self.root_dir + os.sep + folder

            if not os.path.exists(temp_folder):
                return False

            else:
                return cat, folder, temp_folder

        else:
            temp_folder = self.root_dir + os.sep + folder

            if not os.path.exists(temp_folder):
                return False

            else:
                return cat, folder, temp_folder

    def browse_map(self):
        """
        Load the mapped product

        Returns:
            None

        """
        # <str> Represents the currently selected text in the combo box
        product = self.ui.comboBox_map1.currentText()

        log.debug("MAPS VIEWER, browse_map-> product: %s" % product)

        # Grab the current extent of the scene view so that the next image that gets opened is in the same extent
        self.graphics_view.view_holder = QRectF(self.graphics_view.mapToScene(0, 0),
                                                self.graphics_view.mapToScene(self.graphics_view.width(),
                                                                              self.graphics_view.height()))

        if product is not "":

            try:
                self.img_list1 = glob.glob(PRODUCTS[product]["root"] + os.sep + "*.tif")

                temp = [img for img in self.img_list1 if str(self.ui.date_slider.value()) in img][0]

                self.pixel_map = QPixmap(temp)

                self.graphics_view.set_image(self.pixel_map)

                if self.graphics_view.view_holder:
                    view_rect = self.graphics_view.viewport().rect()

                    scene_rect = self.graphics_view.transform().mapRect(self.graphics_view.view_holder)

                    factor = min(view_rect.width() / scene_rect.width(),
                                 view_rect.height() / scene_rect.height())

                    self.graphics_view.scale(factor, factor)

            except IndexError:
                pass

    def resizeEvent(self, event):
        """
        Override the resizeEvent to make the images fit the QLabel size

        """
        try:
            sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

            self.graphics_view.setSizePolicy(sizePolicy)

            self.graphics_view.set_image(self.pixel_map)

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

        def check_lower(val, limit=5000):
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

        row_lr = check_lower(self.row)
        col_lr = check_lower(self.col)

        upper_left = QPointF(col_ul, row_ul)
        bottom_right = QPointF(col_lr, row_lr)

        rect = QRectF(upper_left, bottom_right)

        view_rect = self.graphics_view.viewport().rect()

        scene_rect = self.graphics_view.transform().mapRect(rect)

        factor = min(view_rect.width() / scene_rect.width(),
                     view_rect.height() / scene_rect.height())

        self.graphics_view.scale(factor, factor)

        self.graphics_view.centerOn(self.current_pixel)

        # Arbitrary number of times to zoom out with the mouse wheel before full extent is reset, based on a guess
        self.graphics_view._zoom = 18

        self.graphics_view.view_holder = QRectF(self.graphics_view.mapToScene(0, 0),
                                                self.graphics_view.mapToScene(self.width(),
                                                                              self.graphics_view.height()))

    def make_rect(self):
        """
        Create a rectangle on the image where the selected pixel location is located

        Returns:
            None

        """
        pen = QPen(Qt.magenta)
        pen.setWidthF(0.1)

        upper_left = QPointF(self.col, self.row)
        bottom_right = QPointF(self.col + 1, self.row + 1)

        self.current_pixel = QGraphicsRectItem(QRectF(upper_left, bottom_right))
        self.current_pixel.setPen(pen)

        self.graphics_view.scene.addItem(self.current_pixel)

    def exit(self):
        """
        Close the GUI
        :return:
        """
        self.close()
