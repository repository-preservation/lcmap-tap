"""Generate a matplotlib canvas and add it to a QWidget contained in a QMainWindow.  This will provide the
display and interactions for the PyCCD plots."""

from lcmap_tap.logger import log, exc_handler
from lcmap_tap.Plotting import POINTS, LINES

import sys
import datetime as dt
import numpy as np
import pkg_resources
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon, QPixmap
import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

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
        self.fig = fig

        FigureCanvas.__init__(self, self.fig)

        if len(fig.axes) >= 3:
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)
        else:
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        FigureCanvas.setSizePolicy(self, sizePolicy)

        FigureCanvas.updateGeometry(self)


class PlotWindow(QtWidgets.QMainWindow):

    selected_obs = QtCore.pyqtSignal(object)

    change_symbology = QtCore.pyqtSignal(object)

    def __init__(self, fig, axes, artist_map, lines_map, parent=None):
        """
        TODO Add a summary
        Args:
            fig:
            axes:
            artist_map:
            lines_map:
            parent:

        """
        super(PlotWindow, self).__init__(parent)

        icon = QIcon(QPixmap(pkg_resources.resource_filename("lcmap_tap", "/".join(("Auxiliary", "icon.PNG")))))

        self.setWindowIcon(icon)

        self.setWindowTitle('Plot Window')

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(2)

        self.artist_map = artist_map
        self.lines_map = lines_map
        # self.gui = gui

        self.prev_highlight = None
        self.ind = None
        self.artist = None
        self.x = None
        self.b = None  # The clicked axis (subplot name)
        self.artist_data = None

        self.fig = fig
        self.canvas = MplCanvas(fig=self.fig)
        self.canvas.draw()

        # <matplotlib.axes.Axes> All axes in the figure are linked via sharey=True, only need one axes object
        # to control zooming on all axes simultaneously.
        self.ax = axes.flatten()[0]

        # <tuple> Contains the original x-axes (i.e. date) limits in order (left, right)
        self.xlim_original = self.ax.get_xlim()

        # <dict> For containing the information pulled by the point_pick method defined below
        self.value_holder = dict()

        self.nav = NavigationToolbar(self.canvas, self.widget)

        self.widget.layout().addWidget(self.nav)

        self.widget.layout().addWidget(self.canvas)

        self.scroll = QtWidgets.QScrollArea(self.widget)

        self.scroll.setWidgetResizable(True)

        self.scroll.setWidget(self.canvas)

        self.widget.layout().addWidget(self.scroll)

        self.canvas.mpl_connect("pick_event", self.point_pick)

        # self.canvas.mpl_connect("pick_event", self.leg_pick)

        # self.canvas.mpl_connect("pick_event", self.highlight_pick)

        self.canvas.mpl_connect("axes_enter_event", self.enter_axes)

        self.canvas.mpl_connect("axes_leave_event", self.leave_axes)

        self.canvas.mpl_connect("scroll_event", self.zoom_event)

        self.show()

        self.resize(1200, 400)

        self.initial_legend()

    def initial_legend(self):
        """

        Returns:

        """

        def set_vis(visibility, line):
            """
            Change the transparency of the picked object in the legend so the user can see explicitly
            which items are turned on/off.
            TODO: Figure out how to make this work for the marker (no line) symbols
            Args:
                visibility: <bool> Whether or not the line is currently visible
                line: <matplotlib.collections.PathCollection> Represents the clicked symbol from the plot legend

            Returns:

            """
            if visibility:
                line.set_alpha(1.0)

            else:
                line.set_alpha(0.2)

            return None

        for legline in self.lines_map.keys():
            # The origlines is a list of lines mapped to the legline for that particular subplot
            origlines = self.lines_map[legline]

            # log.debug("method leg_pick, origlines referenced=%s" % str(origlines))

            for l in origlines:
                if type(l) is not list:

                    # Reference the opposite of the line's current visibility
                    vis = l.get_visible()

                    l.set_visible(vis)

                    set_vis(vis, legline)

                else:
                    for _l in l:
                        vis = _l.get_visible()

                        _l.set_visible(vis)

                        set_vis(vis, legline)

            # Redraw the canvas with the line or points turned on/off
            self.canvas.draw()

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
        mouse_event = event.mouseevent

        # This references which object on the plot was hit by the pick
        self.artist = event.artist

        # Only works using left-click (event.mouseevent.button==1)
        # and on any of the scatter point series (PathCollection artists)
        if isinstance(self.artist, PathCollection) and mouse_event.button == 1:
            # Return the index value of the artist (i.e. which data point in the series was hit)
            ind = event.ind

            # Retrieve the appropriate data series based on the clicked artist
            x = self.artist_map[self.artist][0]
            y = self.artist_map[self.artist][1]
            self.b = self.artist_map[self.artist][2]

            try:
                # Grab the date value at the clicked point
                click_x = dt.datetime.fromordinal(int(mouse_event.xdata))

                point_clicked = [click_x, mouse_event.ydata]

                # Retrieve the x-y data for the plotted point within a set tolerance to the
                # clicked point if there is one
                self.x = np.take(x, ind)  # The x-value in ordinal format

                nearest_x = dt.datetime.fromordinal(int(self.x))

                nearest_y = np.take(y, ind)

                self.artist_data = [nearest_x, nearest_y]

                self.value_holder["temp"] = [point_clicked, self.artist_data]

                # test_str = "{:%Y%m%d}".format(self.value_holder["temp"][1][0])

                # log.debug("Point clicked: %s" % point_clicked)
                # log.debug("Nearest artist: %s" % self.value_holder)
                # log.debug("Artist data: %s" % self.artist_data)
                # log.debug("Subplot: %s" % self.b)

                # selection_info = "Obs. Date: {:%Y-%b-%d}\n" \
                #                  "{}-Value: {}".format(self.value_holder['temp'][1][0],
                #                                        self.b,
                #                                        self.value_holder['temp'][1][1][0])

                selection_info = {'date': self.value_holder['temp'][1][0],
                                  'b': self.b,
                                  'value': self.value_holder['temp'][1][1][0]}

                self.selected_obs.emit(selection_info)

                # self.gui.ui.ListWidget_selected.addItem("Obs. Date: {:%Y-%b-%d}\n"
                #                                         "{}-Value: {}".format(
                #     self.value_holder['temp'][1][0],
                #     self.b,
                #     self.value_holder['temp'][1][1][0])
                # )

                self.highlight_pick()

            # I think the TypeError might occur when more than a single data point is returned with one click,
            # but need to investigate further.
            except TypeError:
                pass

        elif isinstance(self.artist, Line2D) and mouse_event.button == 1:
            try:
                self.leg_pick()

            except KeyError:
                pass

        elif isinstance(self.artist, Line2D) and mouse_event.button == 3:
            self.init_configure()

        else:
            # Do this so nothing happens when the other mouse buttons are clicked while over a plot
            return False, dict()

    def highlight_pick(self):
        """
        Change the symbology of the clicked point so that it is visible on the plot

        Returns:
            None

        """
        # Remove the highlight from the previously selected point
        try:
            self.prev_highlight.set_data([], [])

        except AttributeError:
            pass

        # <class 'matplotlib.lines.Line2D'> This points to the Line2D curve that will contain the highlighted point
        # Use index '0' because self.artist_map[b] is referencing a list of 1 item
        highlight = self.artist_map[self.b][0]

        self.prev_highlight = highlight

        log.debug("artist_data[0]: {}".format(self.artist_data[0]))
        log.debug("artist_data[1]: {}".format(self.artist_data[1]))

        highlight.set_data(self.artist_data[0], self.artist_data[1])

        self.canvas.draw()

    def leg_pick(self):
        """
        Define a picker method that allows toggling lines on/off by clicking them on the legend

        Returns:
            None

        """

        def set_vis(visibility, line):
            """
            Change the transparency of the picked object in the legend so the user can see explicitly
            which items are turned on/off.
            TODO: Figure out how to make this work for the marker (no line) symbols
            Args:
                visibility: <bool> Whether or not the line is currently visible
                line: <matplotlib.collections.PathCollection> Represents the clicked symbol from the plot legend

            Returns:

            """
            if visibility:
                line.set_alpha(1.0)

            else:
                line.set_alpha(0.2)

            return None

        legline = self.artist

        # log.debug("method leg_pick called, legline=%s" % str(legline))

        # The origlines is a list of lines mapped to the legline for that particular subplot
        origlines = self.lines_map[legline]

        # log.debug("method leg_pick, origlines referenced=%s" % str(origlines))

        for l in origlines:
            if type(l) is not list:
                # Reference the opposite of the line's current visibility
                vis = not l.get_visible()

                l.set_visible(vis)

                set_vis(vis, legline)

            else:
                for _l in l:
                    vis = not _l.get_visible()

                    _l.set_visible(vis)

                    set_vis(vis, legline)

        # Redraw the canvas with the line or points turned on/off
        self.canvas.draw()

    def init_configure(self):
        log.debug("Selected Legend Label: {}".format(self.artist.get_label()))

        self.label = self.artist.get_label()

        if self.label in POINTS or self.label in LINES:
            # self.symbol_selector = SymbologyWindow()
            #
            # self.symbol_selector.selected_marker.connect(self.connect_symbology)
            self.change_symbology.emit(self.label)

    def enter_axes(self, event=None):
        """
        Detect when the cursor enters a subplot area on the main canvas.  Install the overridden EventFilter
        which deactivates the mouse wheel scrolling on the QMainWindow
        Args:
            event: The 'axes_enter_event'

        Returns:
            None

        """
        if event:
            self.scroll.viewport().installEventFilter(self)

    def leave_axes(self, event=None):
        """
        Detect when the cursor leaves a subplot area on the main canvas.  Remove the overridden EventFilter
        to reactivate mouse wheel scrolling on the QMainWindow
        Args:
            event: The 'axes_leave_event'

        Returns:
            None

        """
        if event:
            self.scroll.viewport().removeEventFilter(self)

    def zoom_event(self, event=None, base_scale=2.):
        """
        Enable zooming in/out of the plots using the mouse scroll wheel.  Current affects only the x-axis by design.
        Source: https://gist.github.com/tacaswell/3144287

        Args:
            event: <scroll-event> Signal sent when the scroll wheel is used inside of a plot window
            base_scale: <float> Default is 2, the re-scaling factor.

        Returns:
            None
        """
        cur_xlim = self.ax.get_xlim()

        # <float> The x-axis value where the mouse scroll event occurs
        xdata = event.xdata

        # Decrease by scale factor (zoom in)
        if event.button == "up":
            scale_factor = 1 / base_scale

        # Increase by scale factor (zoom out)
        elif event.button == "down":
            scale_factor = base_scale

        else:
            scale_factor = 1

        try:
            # <float> X-Distance from cursor to current left-limit
            x_left_dist = xdata - cur_xlim[0]

            # <float> X-Distance from cursor to current right-limit
            x_right_dist = cur_xlim[1] - xdata

            # <float> The x-axis rescaled left-limit
            x_left = xdata - x_left_dist * scale_factor

            # <float> The x-axis rescaled right-limit
            x_right = xdata + x_right_dist * scale_factor

            if x_left >= self.xlim_original[0] and x_right <= self.xlim_original[1]:

                self.ax.set_xlim([x_left, x_right])

            elif x_left >= self.xlim_original[0] and x_right > self.xlim_original[1]:

                self.ax.set_xlim([x_left, self.xlim_original[1]])

            elif x_left < self.xlim_original[0] and x_right <= self.xlim_original[1]:

                self.ax.set_xlim([self.xlim_original[0], x_right])

            else:

                pass

            self.canvas.draw()

        # occurs using the scroll button outside of an axis, but still in the plot window
        except TypeError:
            pass

    def eventFilter(self, source, event):
        """
        Override the parent class eventFilter method to ignore the mouse scroll wheel when zooming in a plot

        Args:
            source:
            event:

        Returns:

        """
        if event.type() == QtCore.QEvent.Wheel and source is self.scroll.viewport():
            return True

        return super(PlotWindow, self).eventFilter(source, event)
