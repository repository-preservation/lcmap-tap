
from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *


class Browser(QApplication):
    def __init__(self):
        QApplication.__init__(self, [])
        self.window = QWidget()
        self.window.setWindowTitle("")

        self.web = QWebEngineView(self.window)

        self.web.setMinimumSize(800,800)

        self.web.setHtml(open('test.html', 'r', encoding='utf-8').read())

        self.text = QTextEdit(self.window)

        self.layout = QVBoxLayout(self.window)

        self.layout.addWidget(self.web)

        self.layout.addWidget(self.text)

        self.window.show()

        self.exec_()

    @pyqtSlot(float, float, int)
    def polygoncomplete(self, lat, lng, i):
        # if i == 0:
        #     self.text.clear()
        self.text.append("Point #{} ({}, {})".format(i, lat, lng))

Browser()
