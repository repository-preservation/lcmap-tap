
from PyQt5 import QtCore, QtWidgets

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib


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
    def __init__(self, fig, parent = None):

        super(PlotWindow, self).__init__(parent)

        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        # self.widget.setLayout(QtWidgets.QGridLayout())
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0, 0, 0, 0)
        self.widget.layout().setSpacing(0)

        self.canvas = MplCanvas(fig=fig)

        self.canvas.draw()

        self.nav = NavigationToolbar(self.canvas, self.widget)
        self.widget.layout().addWidget(self.nav)

        self.widget.layout().addWidget(self.canvas)

        self.scroll = QtWidgets.QScrollArea(self.widget)
        self.scroll.setWidgetResizable(True)


        self.scroll.setWidget(self.canvas)

        self.widget.layout().addWidget(self.scroll)

        self.canvas.fig.tight_layout(h_pad=6.0)
        # self.canvas.fig.subplots_adjust(top=0.80, bottom=0.18, left=0.05, right=0.95)

        self.show()