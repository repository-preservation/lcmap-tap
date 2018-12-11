"""Build a Qt Window with functionality to allow for setting custom symbology"""

import sys
import numpy as np
import pkg_resources
# from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from lcmap_tap.logger import exc_handler, log

sys.excepthook = exc_handler


def split_list(a_list):
    """
    Source: https://matplotlib.org/gallery/lines_bars_and_markers/marker_reference.html
    Args:
        a_list (list): Input list to split in half

    Returns:
        Tuple[list, list]
    """
    i_half = len(a_list) // 2

    return a_list[:i_half], a_list[i_half:]


def nice_repr(text):
    # Source: https://matplotlib.org/gallery/lines_bars_and_markers/marker_reference.html
    return repr(text).lstrip('u')


def format_axes(ax):
    # Source: https://matplotlib.org/gallery/lines_bars_and_markers/marker_reference.html
    ax.margins(0.2)
    ax.set_axis_off()
    ax.invert_yaxis()


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
    points = np.ones(3)  # Draw 3 points for each line

    text_style = dict(horizontalalignment='right', verticalalignment='center',
                      fontsize=12, fontdict={'family': 'monospace'})

    marker_style = dict(linestyle=':', color='0.8', markersize=10,
                        mfc="C0", mec="C0", picker=3)

    selected_marker = pyqtSignal(object)

    def __init__(self, target, parent=None):
        """
        TODO Add a summary
        """
        super(SymbologyWindow, self).__init__(parent)

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))

        self.setWindowIcon(icon)

        self.setWindowTitle('Select Symbology')

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)

        self.target = target

        self.fig, self.axes = plt.subplots(ncols=2)

        self.markers = [m for m, func in Line2D.markers.items() if func != 'nothing']

        self.lines = [l for l, func in Line2D.lineStyles.items() if func != 'nothing']

        self.data = dict()

        log.debug("lines: {}".format(self.lines))

        for ax, markers in zip(self.axes, split_list(self.markers)):
            self.data[ax] = dict()

            for y, marker in enumerate(markers):
                ax.text(-0.5, y, nice_repr(marker), **self.text_style)

                ax.plot(y * self.points, marker=marker, label=y, **self.marker_style)

                self.data[ax][str(y)] = marker

                format_axes(ax)

        self.fig.suptitle('Select Marker Symbol', fontsize=14)

        plt.tight_layout()

        self.canvas = MplCanvas(fig=self.fig)

        self.canvas.draw()

        self.widget.layout().addWidget(self.canvas)

        self.scroll = QtWidgets.QScrollArea(self.widget)

        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.canvas)

        self.widget.layout().addWidget(self.scroll)

        self.setMinimumSize(15, 15)

        self.canvas.mpl_connect("pick_event", self.point_pick)

        self.resize(700, 700)

        self.show()

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
#     s = SymbologyWindow()
#
#     if s:
#         # Enter the main event loop, begin event handling for application widgets until exit() is called
#
#         sys.exit(app.exec_())
#
#
# if __name__ == "__main__":
#     main()
