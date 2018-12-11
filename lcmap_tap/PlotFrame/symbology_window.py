"""Build a Qt Window with functionality to allow for setting custom symbology"""

import sys
import pkg_resources
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from lcmap_tap.logger import exc_handler, log

sys.excepthook = exc_handler


class MplCanvas(FigureCanvas):
    """
    TODO: Add summary line
    """

    def __init__(self, fig):
        """
        TODO: Add Summary
        Args:
            fig:
        """
        FigureCanvas.__init__(self, fig)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        FigureCanvas.setSizePolicy(self, sizePolicy)

        FigureCanvas.updateGeometry(self)


class SymbologyWindow(QtWidgets.QMainWindow):
    text_style = dict(horizontalalignment='right', verticalalignment='center',
                      fontsize=12, fontdict={'family': 'monospace'})

    marker_style = dict(linestyle=':', color='0.8', markersize=10,
                        mfc="C0", mec="C0", picker=6)

    marker_names = [n for m, n in Line2D.markers.items() if n != 'nothing']

    selected_marker = pyqtSignal(object)

    def __init__(self, parent=None):
        """
        TODO Add a summary
        """
        super(SymbologyWindow, self).__init__(parent)

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))

        self.fig = plt.figure()

        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.grid(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.setWindowIcon(icon)

        self.setWindowTitle('Select Symbology')

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        self.main_QVBoxLayout = QtWidgets.QVBoxLayout()
        self.main_QVBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.main_QVBoxLayout.setSpacing(10)

        self.widget.setLayout(self.main_QVBoxLayout)

        # --- Create Combo Boxes -----------------------
        self.symbol_comboBox = QtWidgets.QComboBox()

        for name in self.marker_names:
            self.symbol_comboBox.addItem(name)

        self.size_comboBox = QtWidgets.QComboBox()

        for i in range(1, 101):
            self.size_comboBox.addItem(str(i))

        self.size_comboBox.setCurrentIndex(13)

        self.color_comboBox = QtWidgets.QComboBox()

        for c in mcolors.CSS4_COLORS.keys():
            self.color_comboBox.addItem(c)
        # ----------------------------------------------

        self.preview_QPushButton = QtWidgets.QPushButton('Preview', self.widget)
        self.preview_QPushButton.clicked.connect(self.preview)

        self.apply_QPushButton = QtWidgets.QPushButton('Apply', self.widget)
        self.apply_QPushButton.clicked.connect(self.apply)

        self.combo_HBoxLayout = QtWidgets.QHBoxLayout()
        self.combo_HBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.combo_HBoxLayout.setSpacing(10)

        self.button_HBoxLayout = QtWidgets.QHBoxLayout()
        self.button_HBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.button_HBoxLayout.setSpacing(20)

        self.combo_HBoxLayout.addWidget(self.symbol_comboBox)
        self.combo_HBoxLayout.addWidget(self.size_comboBox)
        self.combo_HBoxLayout.addWidget(self.color_comboBox)

        self.button_HBoxLayout.addWidget(self.preview_QPushButton)
        self.button_HBoxLayout.addWidget(self.apply_QPushButton)

        self.main_QVBoxLayout.addLayout(self.combo_HBoxLayout)

        self.main_QVBoxLayout.addLayout(self.button_HBoxLayout)

        self.markers = {func: m for m, func in Line2D.markers.items() if func != 'nothing'}

        self.resize(300, 400)

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

            self.widget.layout().removeWidget(self.canvas)

        except AttributeError:
            pass

        color_key = self.color_comboBox.currentText()

        marker_key = self.symbol_comboBox.currentText()

        markersize_key = int(self.size_comboBox.currentText())

        self.ax.plot(0.5, 0.5, color=color_key, marker=self.markers[marker_key], markersize=markersize_key, linewidth=0)

        plt.tight_layout()

        self.canvas = MplCanvas(fig=self.fig)

        self.canvas.draw()

        self.widget.layout().addWidget(self.canvas)

    def apply(self):
        """Emit the new customized symbol parameters"""
        color = self.color_comboBox.currentText()

        marker = self.markers[self.symbol_comboBox.currentText()]

        markersize = int(self.size_comboBox.currentText())

        new_symbol = {'color': color,
                      'marker': marker,
                      'markersize': markersize}

        self.selected_marker.emit(new_symbol)

    def point_pick(self, event=None):
        """
        Define a picker method to grab data off of the plot wherever the mouse cursor is clicked

        Args:
            event: A mouse-click event
                   event.button == 1 <left-click>
                   event.button == 2 <wheel-click>
                   event.button == 3 <right-click>

        Returns:
            The x_data and y_data for the selected artist using a mouse click event

        """
        # Reference useful information about the pick location
        # mouse_event = event.mouseevent

        # This references which object on the plot was hit by the pick
        self.artist = event.artist

        event_axis = self.artist.axes

        # log.debug('Event axis: {}'.format(event_axis))

        event_label = self.artist.get_label()

        # log.debug('event_label: {}'.format(event_label))
        #
        # log.debug('mouse_event: {}'.format(mouse_event))
        #
        # log.debug('Marker: {}'.format(self.data[event_axis][event_label]))

        self.selected_marker.emit(self.data[event_axis][event_label])

# def main():
#     # Create a QApplication object, necessary to manage the GUI control flow and settings
#     app = QApplication(sys.argv)
#
#     # session_id = "session_{}".format(MainControls.get_time())
#
#     s = SymbologyWindow(None)
#
#     if s:
#         # Enter the main event loop, begin event handling for application widgets until exit() is called
#
#         sys.exit(app.exec_())
#
#
# if __name__ == "__main__":
#     main()
