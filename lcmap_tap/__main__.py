
import sys
from lcmap_tap.logger import log, __version__
from PyQt5.QtWidgets import QApplication
from lcmap_tap.Controls.controls import MainControls
try:
    from pip._internal.operations import freeze
except ImportError:
    from pip.operations import freeze


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions
    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:

    """
    log.critical("Uncaught Exception: ", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = exc_handler


def main():
    log.debug('*** System Information ***')
    log.debug('Platform: %s' % sys.platform)
    log.debug('Python: %s' % str(sys.version).replace('\n', ''))
    log.debug('Pip: %s' % ', '.join(freeze.freeze()))
    log.info("Running lcmap-tap version %s" % __version__)

    # Create a QApplication object, necessary to manage the GUI control flow and settings
    app = QApplication(sys.argv)

    # session_id = "session_{}".format(MainControls.get_time())

    control_window = MainControls()

    if control_window:
        # Enter the main event loop, begin event handling for application widgets until exit() is called

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
