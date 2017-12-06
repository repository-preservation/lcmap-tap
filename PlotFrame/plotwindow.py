
import numpy as np
import datetime as dt

from PyQt5 import QtWidgets

import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.collections import PathCollection

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class MplCanvas(FigureCanvas):
    def __init__(self, fig):
        self.fig = fig

        FigureCanvas.__init__(self, self.fig)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)

        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        FigureCanvas.setSizePolicy(self, sizePolicy)

        FigureCanvas.updateGeometry(self)


class PlotWindow(QtWidgets.QMainWindow):
    def __init__(self, fig, artist_map, gui, scenes, parent=None):

        super(PlotWindow, self).__init__(parent)

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)

        self.fig = fig
        self.canvas = MplCanvas(fig=self.fig)
        self.canvas.draw()

        # Create a mutable object to contain the information pulled by the point_pick method
        self.value_holder = {}

        # Define a picker method to grab data off of the plot wherever the mouse cursor is when clicked
        def point_pick(event):
            """
            Return the x_data and y_data for the selected artist using a mouse click event
            :param event:
            :return:
            """
            # References useful information about the pick location
            mouseevent = event.mouseevent

            # This references which object on the plot was hit by the pick
            artist = event.artist

            # Only works using left-click (event.mouseevent.button==1)
            # and on any of the scatter point series (PathCollection artists)
            if isinstance(artist, PathCollection) and mouseevent.button == 1:
                # Return the index value of the artist (i.e. which data point in the series was hit)
                ind = event.ind

                # Retrieve the appropriate data series based on the clicked artist
                x = artist_map[artist][0]
                y = artist_map[artist][1]

                try:
                    # Grab the date value at the clicked point
                    click_x = dt.datetime.fromordinal(int(mouseevent.xdata))

                    point_clicked = [click_x, mouseevent.ydata]

                    # Retrieve the x-y data for the plotted point within a set tolerance to the
                    # clicked point if there is one
                    nearest_x = dt.datetime.fromordinal(int(np.take(x, ind)))
                    nearest_y = np.take(y, ind)

                    artist_data = [nearest_x, nearest_y]

                    print(f"point clicked: {point_clicked}\n"
                          f"nearest artist: {self.value_holder}")

                    self.value_holder["temp"] = [point_clicked, artist_data]

                    test_str = "{:%Y%m%d}".format(self.value_holder["temp"][1][0])

                    for id in scenes:
                        if test_str in id:
                            self.value_holder["temp"].append(id)

                            gui.ui.plainTextEdit_click.appendPlainText("Scene ID: {}".format(id))

                    # Show the picked information in a text box on the GUI
                    gui.ui.plainTextEdit_click.appendPlainText(
                        "Obs. Date: {:%Y-%b-%d} \nY-Value: {}\n".format(self.value_holder['temp'][1][0],
                                                               self.value_holder['temp'][1][1][0]))

                # I think the TypeError might occur when more than a single data point is returned with one click,
                # but need to investigate further.
                except TypeError:
                    pass

            else:
                # Do this so nothing happens when the other mouse buttons are clicked while over a plot
                return False, dict()

        self.nav = NavigationToolbar(self.canvas, self.widget)

        self.widget.layout().addWidget(self.nav)

        self.widget.layout().addWidget(self.canvas)

        self.scroll = QtWidgets.QScrollArea(self.widget)
        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.canvas)

        self.widget.layout().addWidget(self.scroll)

        self.canvas.fig.tight_layout(h_pad=6.0)

        self.canvas.mpl_connect("pick_event", point_pick)

        self.show()
