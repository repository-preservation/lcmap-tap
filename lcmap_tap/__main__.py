import sys

from PyQt5.QtWidgets import QApplication

from lcmap_tap.Controls.controls import PlotControls


def main():
    """

    :return:
    """
    app = QApplication(sys.argv)

    control_window = PlotControls()

    sys.exit(app.exec_())


if __name__ == "__main__":

    # app = QApplication(sys.argv)

    # control_window = PlotControls()

    # sys.exit(app.exec_())

    main()
