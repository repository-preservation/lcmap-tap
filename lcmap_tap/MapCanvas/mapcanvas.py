"""Use Leaflet JavaScript API to display an interactive web map within a QWidget"""

from lcmap_tap.RetrieveData.retrieve_geo import GeoInfo
from lcmap_tap.logger import log

import sys
import pkg_resources

from PyQt5.QtCore import QDir, QObject, QUrl, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

HTML = pkg_resources.resource_filename('lcmap_tap', '/'.join(('MapCanvas', 'index.html')))


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions

    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:
        None

    """
    log.critical("Uncaught Exception: ", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = exc_handler


class Backend(QObject):
    pointChanged = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def pointClicked(self, x, y):
        self.pointChanged.emit(x, y)


class MapCanvas(QWidget):
    def __init__(self, gui, parent=None):
        super(MapCanvas, self).__init__(parent)

        self.gui = gui

        self.setMinimumSize(400, 400)

        self.text = QTextEdit(self)

        self.map_view = QWebEngineView()

        self.backend = Backend(self)

        self.backend.pointChanged.connect(self.onPointChanged)

        self.channel = QWebChannel(self)

        self.channel.registerObject('backend', self.backend)

        self.map_view.page().setWebChannel(self.channel)

        # Open the index.html that loads the leaflet JS code
        self.file = QDir.current().absoluteFilePath(HTML)

        self.map_view.load(QUrl.fromLocalFile(self.file))

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(self.map_view)

        self.layout.addWidget(self.text)

        # self.show()

    @pyqtSlot(float, float)
    def onPointChanged(self, lat, lng):
        """
        Retrieve the coordinate values in decimal degrees from the leaflet map

        Args:
            lat: Latitude of mouse-click
            lng: Longitude of mouse-click

        Returns:
            None

        """
        coords = GeoInfo.get_geocoordinate(xstring=str(lng), ystring=str(lat))

        log.info("New point selected from locator map: %s" % str(coords))

        # Convert to meters before updating the coordinate text on the GUI
        if self.gui.units[self.gui.selected_units]["unit"] == "meters":
            _coords = GeoInfo.unit_conversion(coords, src="lat/long", dest="meters")

            self.gui.ui.x1line.setText(str(_coords.x))

            self.gui.ui.y1line.setText(str(_coords.y))

        # Update the X and Y coordinates in the GUI with the new point
        else:
            self.gui.ui.x1line.setText(str(coords.x))

            self.gui.ui.y1line.setText(str(coords.y))

        self.gui.check_values()

        # Clear the list of previously clicked ARD observations because they can't be referenced in the new time-series
        self.gui.ui.clicked_listWidget.clear()

        # Display the coordinate in the QTextEdit window below the map
        self.text.append("Point {lat}, {lng}".format(lat=lat, lng=lng))

        return None
