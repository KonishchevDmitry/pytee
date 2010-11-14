#!/usr/bin/env python

# PyQt tutorial 3


import logging
import sys
import os
from PySide import QtCore, QtGui

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pysd"))
from pytee.main_window import MainWindow
from cl.core import *

for log in ("player", "cl", "mplayer", "pytee", "subtitles.widget", "subtitles.readeR"):
    LOG = logging.getLogger(log)
    handler = logging.StreamHandler(sys.stderr)
    LOG.addHandler(handler)
    LOG.setLevel(logging.DEBUG)


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
    app.exec_()

    LOG.info("Exiting...")
    sys.exit()


if __name__ == "__main__":
    main()

