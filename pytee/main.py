#!/usr/bin/env python

"""pytee's startup module."""

import os
import sys

# Setting up paths to modules.
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, INSTALL_DIR)
sys.path.insert(1, os.path.join(INSTALL_DIR, "pysd"))

import logging
from PySide import QtCore, QtGui

from pytee.main_window import MainWindow
from cl.core import *

debug_mode = True

class LogFilter(logging.Filter):
    def filter(self, record):
        return not record.name == "subtitles.reader"

import cl.log
cl.log.setup(debug_mode, filter = LogFilter())

LOG = logging.getLogger("pytee.main")

import signal
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
signal.siginterrupt(signal.SIGCHLD, False)
signal.siginterrupt(signal.SIGPIPE, False)
for i in xrange(1, 100):
    try:
        signal.siginterrupt(i, False)
    except:
        pass


def main():
    """The application's main function."""

    app = QtGui.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    main_window.open(sys.argv[1])
    app.exec_()

    LOG.info("Exiting...")
    sys.exit()


if __name__ == "__main__":
    main()

