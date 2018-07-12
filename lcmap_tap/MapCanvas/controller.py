import json
import os
import decorator

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
# from PyQt5.QtCore import pyqtSignal, QUrl, QUrlQuery, QXmlStreamReader
# from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView, QWebEngineSettings
# from PyQt5.QtWidgets import QApplication

html_file = 'qwebmap.html'

with open(html_file, 'r', encoding='utf-8') as f:
    html_code = f.read()


class MapCanvas(QtWidgets.QMainWindow):
    def __init__(self):
        super(MapCanvas, self).__init__()

        self.window = QtWidgets.QWidget()

        self.web = QWebEngineView(self.window)

        self.web.setMinimumSize(800, 800)

        self.web.page().mainFrame().addToJavaScriptWindowObject('self', self)

        self.web.setHtml(html_code)

        self.text = QtWidgets.QTextEdit(self.window)

        self.layout = QtWidgets.QVBoxLayout(self.window)

        self.layout.addWidget(self.web)

        self.layout.addWidget(self.text)

        self.window.show()

    @pyqtSlot(float, float, int)
    def point_addition(self, lat, lng, i):
        if i == 0:
            self.text.clear()

        self.text.append("Point #{} ({}, {})".format(i, lat, lng))

        return None
