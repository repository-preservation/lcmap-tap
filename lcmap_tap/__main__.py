import sys
from lcmap_tap.logger import log
from PyQt5.QtWidgets import QApplication
from lcmap_tap.Controls.controls import MainControls


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions
    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:

    """
    # if issubclass(exc_type, KeyboardInterrupt):
    #     sys.__excepthook__(exc_type, exc_value, exc_traceback)
    #     return

    log.critical("Uncaught Exception: ", exc_info=(exc_type, exc_value, exc_traceback))


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
