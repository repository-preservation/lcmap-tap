"""Use Leaflet JavaScript API to display an interactive web map within a QWidget"""

import sys
from PyQt5.QtCore import QDir, QObject, QUrl, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QApplication, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel


HTML = "index.html"


class Backend(QObject):
    pointChanged = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def pointClicked(self, x, y):
        self.pointChanged.emit(x, y)


class MapCanvas(QWidget):
    def __init__(self, parent=None):
        super(MapCanvas, self).__init__(parent)

        self.coord = dict()

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
        self.coord['lat'] = lat

        self.coord['lng'] = lng

        # Display the coordinate in the QTextEdit window
        self.text.append("Point {lat}, {lng}".format(lat=lat, lng=lng))

        return None

# For debugging and testing
if __name__ == '__main__':

    app = QApplication(sys.argv)

    w = MapCanvas()

    w.show()

    sys.exit(app.exec_())
