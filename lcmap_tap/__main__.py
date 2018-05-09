import sys
import traceback
from lcmap_tap.logger import log
from PyQt5.QtWidgets import QApplication
from lcmap_tap.Controls.controls import MainControls


def exc_handler(type, value, tb):
    """
    Customized handling of top-level exceptions
    Args:
        type: exception class
        value: exception instance
        tb: traceback object

    Returns:

    """
    log.warning("Uncaught Exception Type: {}".format(str(type)))
    log.warning("Uncaught Exception Value: {}".format(str(value)))
    log.warning("Uncaught Exception Traceback: {}".format(traceback.print_tb(tb)))


sys.excepthook = exc_handler

def main():
    # Create a QApplication object, necessary to manage the GUI control flow and settings
    app = QApplication(sys.argv)

    # session_id = "session_{}".format(MainControls.get_time())

    control_window = MainControls()

    if control_window:
        # Enter the main event loop, begin event handling for application widgets until exit() is called

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
