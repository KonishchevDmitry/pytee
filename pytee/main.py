#!/usr/bin/env python

"""pytee's startup module."""

import sys

if sys.version_info < (2, 6):
    if __name__ == "__main__":
        sys.exit("Error: pytee needs python >= 2.6.")
    else:
        raise Exception("pytee needs python >= 2.6")

import os

# Setting up the module paths.
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, INSTALL_DIR)
sys.path.insert(1, os.path.join(INSTALL_DIR, "pysd"))

import logging
import signal

from PySide import QtCore, QtGui

from pytee.main_window import MainWindow
import cl.log
import cl.signals

LOG = logging.getLogger("pytee.main")


class LogFilter(logging.Filter):
    def filter(self, record):
        return not record.name == "subtitles.reader"


def main():
    """The application's main function."""

    debug_mode = True

    cl.log.setup(debug_mode, filter = LogFilter())
    cl.signals.setup()

    app = QtGui.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()
    cl.signals.connect(main_window.close)

    main_window.open(sys.argv[1])
    app.exec_()

    LOG.info("Exiting...")
    sys.exit()


if __name__ == "__main__":
    main()

