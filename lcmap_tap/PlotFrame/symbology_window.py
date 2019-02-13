"""Build a Qt Window with functionality to allow for setting custom symbology"""

from lcmap_tap.UserInterface.ui_symbology import Ui_MainWindow_symbology
from lcmap_tap.Plotting import POINTS

import os
import sys
import pkg_resources
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from lcmap_tap.logger import exc_handler

sys.excepthook = exc_handler


class MplCanvas(FigureCanvas):
    def __init__(self, fig):
        FigureCanvas.__init__(self, fig)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        FigureCanvas.setSizePolicy(self, sizePolicy)

        FigureCanvas.updateGeometry(self)


class SymbologyWindow(QtWidgets.QMainWindow):
    marker_names = [n for m, n in Line2D.markers.items() if n != 'nothing']

    line_names = [n for m, n in Line2D.lineStyles.items() if 'nothing' not in n]

    selected_marker = pyqtSignal(object)

    file_saver = pyqtSignal(object)

    file_loader = pyqtSignal(object)

    def __init__(self, marker, size, color, bg_color, target):
        super().__init__()

        self.target = target

        self.bg_color = bg_color

        self.ui = Ui_MainWindow_symbology()

        self.ui.setupUi(self)

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))

        self.fig = plt.figure()

        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.grid(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.setWindowIcon(icon)

        if self.target in POINTS:
            for name in self.marker_names:
                self.ui.comboBox_marker.addItem(name)

            for i in range(1, 101):
                self.ui.comboBox_size.addItem(str(i))

            init_marker = [n for s, n in Line2D.markers.items() if Line2D.markers[marker] is n][0]

        else:
            for name in self.line_names:
                self.ui.comboBox_marker.addItem(name)

            for i in np.arange(0, 5.25, 0.25):
                self.ui.comboBox_size.addItem(str(i))

            init_marker = [n for s, n in Line2D.lineStyles.items() if Line2D.lineStyles[marker] is n][0]

        for c in mcolors.CSS4_COLORS.keys():
            self.ui.comboBox_color.addItem(c)

            self.ui.comboBox_background.addItem(c)

        self.ui.comboBox_marker.setCurrentText(init_marker)

        self.ui.comboBox_size.setCurrentText(str(size))

        self.ui.comboBox_color.setCurrentText(color)

        self.ui.comboBox_background.setCurrentText(self.bg_color)

        self.ui.pushButton_preview.clicked.connect(self.preview)

        self.ui.pushButton_apply.clicked.connect(self.apply)

        self.markers = {func: m for m, func in Line2D.markers.items() if func != 'nothing'}

        self.lines = {func: m for m, func in Line2D.lineStyles.items() if 'nothing' not in func}

        self.ui.actionLoad.triggered.connect(self.load_file)

        self.ui.actionSave.triggered.connect(self.save_file)

        self.show()

    def preview(self):
        """
        Display a preview of the custom symbology

        Returns:

        """
        try:
            self.ax.cla()

            self.ax.grid(False)
            self.ax.set_xticks([])
            self.ax.set_yticks([])

            self.ui.horizontalLayout_preview.removeWidget(self.canvas)

        except AttributeError:
            pass

        bg_key = self.ui.comboBox_background.currentText()

        color_key = self.ui.comboBox_color.currentText()

        marker_key = self.ui.comboBox_marker.currentText()

        if self.target in POINTS:
            markersize_key = int(self.ui.comboBox_size.currentText())

            self.ax.plot(0.5, 0.5, color=color_key, marker=self.markers[marker_key], markersize=markersize_key,
                         linewidth=0)

            self.ax.patch.set_facecolor(bg_key)

        else:
            markersize_key = float(self.ui.comboBox_size.currentText())

            self.ax.axvline(x=0.5, color=color_key, marker=None, linestyle=self.lines[marker_key],
                            linewidth=markersize_key)

            self.ax.patch.set_facecolor(bg_key)

        plt.tight_layout()

        self.canvas = MplCanvas(fig=self.fig)

        self.canvas.draw()

        try:
            self.ui.horizontalLayout_preview.removeWidget(self.ui.frame)

        except Exception:
            pass

        self.ui.horizontalLayout_preview.addWidget(self.canvas)

    def apply(self):
        """
        Emit the new customized symbol parameters

        """
        color = self.ui.comboBox_color.currentText()

        new_bg = self.ui.comboBox_background.currentText()

        if self.target in POINTS:
            marker = self.markers[self.ui.comboBox_marker.currentText()]

            markersize = int(self.ui.comboBox_size.currentText())

        else:
            marker = self.lines[self.ui.comboBox_marker.currentText()]

            markersize = float(self.ui.comboBox_size.currentText())

        new_symbol = {'color': color,
                      'marker': marker,
                      'markersize': markersize,
                      'background': new_bg}

        self.selected_marker.emit(new_symbol)

    def load_file(self):
        in_file = QtWidgets.QFileDialog.getOpenFileName(self, filter='*.yml')

        self.file_loader.emit(self.check_filename(in_file))

    def save_file(self):
        out_file = QtWidgets.QFileDialog.getSaveFileName(self, filter='.yml')

        self.file_saver.emit(self.check_filename(out_file))

    @staticmethod
    def check_filename(parts):
        if os.path.splitext(parts[0])[-1] is '':
            filename = parts[0] + parts[1]

        else:
            filename = parts[0]

        return filename
