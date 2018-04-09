import os
import glob
import matplotlib

matplotlib.use("Qt5Agg")

from PyQt5 import QtCore  # , QtWidgets, QtGui
from PyQt5.QtGui import QPixmap  # , QImage, QActionEvent
from PyQt5.QtWidgets import QMainWindow, QSlider  # QFileDialog, QSizePolicy, QLabel, QAction

# import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from lcmap_tap.Visualization.ui_maps_viewer import Ui_MapViewer


class MplCanvas(FigureCanvas):
    def __init__(self, fig):
        self.fig = fig

        FigureCanvas.__init__(self, self.fig)

        FigureCanvas.updateGeometry(self)


class MapsViewer(QMainWindow):
    products = {"Change DOY": {"type": "ChangeMaps",
                               "alias": "ChangeMap_color",
                               "root": ""},

                "Change Magnitude": {"type": "ChangeMaps",
                                     "alias": "ChangeMagMap_color",
                                     "root": ""},

                "Change QA": {"type": "ChangeMaps",
                              "alias": "QAMap_color",
                              "root": ""},

                "Segment Length": {"type": "ChangeMaps",
                                   "alias": "SegLength_color",
                                   "root": ""},

                "Time Since Last Change": {"type": "ChangeMaps",
                                           "alias": "LastChange_color",
                                           "root": ""},

                "Primary Land Cover": {"type": "CoverMaps",
                                       "alias": "CoverPrim_color",
                                       "root": ""},

                "Secondary Land Cover": {"type": "CoverMaps",
                                         "alias": "CoverSec_color",
                                         "root": ""},

                "Primary Land Cover Confidence": {"type": "CoverMaps",
                                                  "alias": "CoverConfPrim_color",
                                                  "root": ""},

                "Secondary Land Cover Confidence": {"type": "CoverMaps",
                                                    "alias": "CoverConfSec_color",
                                                    "root": ""}
                }

    # versions listed from highest to lowest priority
    versions = ["v2017.08.18", "v2017.8.18", "v2017.6.20-a", "v2017.6.20", "v2017.6.8", "v1.4.0"]

    def __init__(self, tile, begin_year=1984, end_year=2015, root=r"Z:\bulk\tiles"):

        super(MapsViewer, self).__init__()

        self.tile = tile

        self.root_dir = root + os.sep + self.tile + os.sep + "eval"

        self.version = self.get_version()

        self.get_product_root_directories()

        self.ui = Ui_MapViewer()

        self.ui.setupUi(self)

        self.img_list1 = list()

        self.img_list2 = list()

        self.img_list3 = list()

        self.pixel_map1 = None

        self.pixel_map2 = None

        self.pixel_map3 = None

        self.ui.date_slider.setMinimum(begin_year)

        self.ui.date_slider.setMaximum(end_year)

        self.ui.date_slider.setTickPosition(QSlider.TicksBothSides)

        self.ui.date_slider.setTickInterval(1)

        # This show's the left-most value of the time slider initially, 1984
        self.ui.show_date.setText(str(self.ui.date_slider.value()))

        self.ui.move_left.clicked.connect(self.move_left)

        self.ui.move_right.clicked.connect(self.move_right)

        self.ui.date_slider.valueChanged.connect(self.date_changed)

        # self.ui.comboBox.activated.connect(self.show_image)

        self.ui.comboBox_map1.currentIndexChanged.connect(self.browse_map1)

        self.ui.comboBox_map2.currentIndexChanged.connect(self.browse_map2)

        self.ui.comboBox_map3.currentIndexChanged.connect(self.browse_map3)

        self.init_ui()

    def init_ui(self):
        """
        Display the GUI
        :return:
        """
        self.show()

    def get_version(self) -> str:
        """
        Determine which version of pyccd products to use
        Returns:
            version: The version identifier
        """
        for version in self.versions:
            temp_look = self.root_dir + os.sep + version

            if os.path.exists(temp_look):

                change_test = temp_look + os.sep + "ChangeMaps"
                cover_test = temp_look + os.sep + "CoverMaps"

                if os.path.exists(change_test) and os.path.exists(cover_test):

                    return version

                else:
                    continue

            else:
                continue

    def get_product_root_directories(self):
        """
        Construct the full path to the change/cover product subdirectories using the most recent version available.
        Store the full path in the self.products dict under keyword "root"

        Returns:
            None

        """
        for product in self.products.keys():
            self.products[product]["root"] = self.root_dir + os.sep + self.version + os.sep + \
                                             self.products[product]["type"] + os.sep + self.products[product]["alias"]

        return None

    def move_left(self):
        """
        Move the slider one increment to the left
        :return:
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
        :return:
        """
        try:
            val = self.ui.date_slider.value()
            val = val + 1
            self.ui.date_slider.setSliderPosition(val)

        except (ValueError, AttributeError, KeyError):
            pass

    # def root_browse(self):
    #     """
    #     Select a root menu that contains the different mapped products in subfolders
    #     :return:
    #     """
    #     self.root_dir = QFileDialog.getExistingDirectory(self)
    #
    #     self.get_items()

    def get_items(self):
        """
        Populate the Maps Menu with the available products
        :return:
        """
        # Get the subfolders
        product_folders = []
        for root, folders, files in os.walk(self.root_dir):
            for folder in folders:
                if folder == "ChangeMaps" or folder == "CoverMaps":
                    product_folders.append(os.path.join(root, folder))

        sub_folders = []
        for prod_folder in product_folders:
            for root, folders, files in os.walk(prod_folder):
                for folder in folders:
                    sub_folders.append(os.path.join(root, folder))

    def show_image(self, key, imgs=None):
        """
        Display the image

        Args:
            key:
            imgs:

        Returns:

        """

        input_dir = self.action_mapper1[key][1]

        if imgs is None:
            imgs = glob.glob(input_dir + os.sep + "*.tif")

        self.pixel_map1 = QPixmap(imgs[0])

        self.ui.map1_QLabel.setPixmap(self.pixel_map1.scaled(self.ui.map1_QLabel.size(),
                                                             QtCore.Qt.KeepAspectRatio,
                                                             transformMode=QtCore.Qt.SmoothTransformation))

    def date_changed(self, value):
        """
        Display the current year,
        :param value: Parameter passed by the valueChanged(int) signal
        :type value: int
        :return:
        """
        self.ui.show_date.setText(str(value))

        try:
            temp1 = [img for img in self.img_list1 if str(value) in img][0]
            self.pixel_map1 = QPixmap(temp1)
            self.ui.map1_QLabel.setPixmap(self.pixel_map1.scaled(self.ui.map1_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))
        except (TypeError, IndexError, AttributeError):
            pass

        try:
            temp2 = [img for img in self.img_list2 if str(value) in img][0]
            self.pixel_map2 = QPixmap(temp2)
            self.ui.map2_QLabel.setPixmap(self.pixel_map2.scaled(self.ui.map2_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))
        except (TypeError, IndexError, AttributeError):
            pass

        try:
            temp3 = [img for img in self.img_list3 if str(value) in img][0]
            self.pixel_map3 = QPixmap(temp3)
            self.ui.map3_QLabel.setPixmap(self.pixel_map3.scaled(self.ui.map3_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))

        except (TypeError, IndexError, AttributeError):
            pass

    def get_product_specs(self, product):
        """
        Retrieve information on the selected product

        Returns:

        """
        cat = self.products[product]["type"]

        folder = self.products[product]["alias"]

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

    def browse_map1(self, index: int):
        """
        Load the mapped product for Map 1
        Args:
            index: comboBox index, signal automatically sent

        Returns:
            None
        """
        # <str> Represents the currently selected text in the combo box
        product = self.ui.comboBox_map1.currentText()

        try:
            self.img_list1 = glob.glob(self.products[product]["root"] + os.sep + "*.tif")

            temp = [img for img in self.img_list1 if str(self.ui.date_slider.value()) in img][0]

            self.pixel_map1 = QPixmap(temp)

            self.ui.map1_QLabel.setPixmap(self.pixel_map1.scaled(self.ui.map1_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))

        except IndexError:
            pass

    def browse_map2(self, index):
        """
        Load the mapped product for Map 2
        Args:
            index: comboBox index, signal automatically sent

        Returns:
            None
        """
        # <str> Represents the currently selected text in the combo box
        product = self.ui.comboBox_map2.currentText()

        try:
            self.img_list2 = glob.glob(self.products[product]["root"] + os.sep + "*.tif")

            temp = [img for img in self.img_list2 if str(self.ui.date_slider.value()) in img][0]

            self.pixel_map2 = QPixmap(temp)

            self.ui.map2_QLabel.setPixmap(self.pixel_map2.scaled(self.ui.map2_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))
        except IndexError:
            pass

    def browse_map3(self, index):
        """
        Load the mapped product for Map 3
        Args:
            index: comboBox index, signal automatically sent

        Returns:
            None
        """
        # <str> Represents the currently selected text in the combo box
        product = self.ui.comboBox_map3.currentText()

        try:
            self.img_list3 = glob.glob(self.products[product]["root"] + os.sep + "*.tif")

            temp = [img for img in self.img_list3 if str(self.ui.date_slider.value()) in img][0]

            self.pixel_map3 = QPixmap(temp)

            self.ui.map3_QLabel.setPixmap(self.pixel_map3.scaled(self.ui.map3_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))
        except IndexError:
            pass

    def resizeEvent(self, event):
        """
        Override the resizeEvent to make the images fit the QLabel size

        """
        try:
            self.ui.map1_QLabel.setPixmap(self.pixel_map1.scaled(self.ui.map1_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))

            self.ui.map2_QLabel.setPixmap(self.pixel_map2.scaled(self.ui.map2_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))

            self.ui.map3_QLabel.setPixmap(self.pixel_map3.scaled(self.ui.map3_QLabel.size(),
                                                                 QtCore.Qt.KeepAspectRatio,
                                                                 transformMode=QtCore.Qt.SmoothTransformation))

        except AttributeError:
            pass

    def exit(self):
        """
        Close the GUI
        :return:
        """
        self.close()
