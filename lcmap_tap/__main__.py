import sys

from PyQt5.QtWidgets import QApplication

from lcmap_tap.Controls.controls import MainControls


def main():
    # session_id = "session_{}".format(MainControls.get_time())

    app = QApplication(sys.argv)

    control_window = MainControls()

    if control_window:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
