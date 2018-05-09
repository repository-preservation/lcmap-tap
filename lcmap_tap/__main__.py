import sys
from lcmap_tap.logger import log
from PyQt5.QtWidgets import QApplication
from lcmap_tap.Controls.controls import MainControls


def exc_handler(exception):
    log.exception("Exception Occurred: {}".format(str(exception[1])))


def main():
    # Create a QApplication object, necessary to manage the GUI control flow and settings
    app = QApplication(sys.argv)

    sys.excepthook = exc_handler

    # session_id = "session_{}".format(MainControls.get_time())

    control_window = MainControls()

    if control_window:
        # Enter the main event loop, begin event handling for application widgets until exit() is called

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
