
import sys

from PyQt5.QtWidgets import QApplication
from Controls.controls import PlotControls

if __name__ == "__main__":

    app = QApplication(sys.argv)

    control_window = PlotControls()

    sys.exit(app.exec_())
