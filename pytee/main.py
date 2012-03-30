#!/usr/bin/env python

"""pytee's startup module."""

import sys

import constants

if sys.version_info < (2, 6):
    if __name__ == "__main__":
        sys.exit(u"Error: {0} needs python >= 2.6.".format(constants.APP_NAME))
    else:
        raise Exception(u"{0} needs python >= 2.6".format(constants.APP_NAME))

import os

# Setting up the module paths.
INSTALL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, INSTALL_DIR)
sys.path.insert(1, os.path.join(INSTALL_DIR, "pysd"))

import getopt
import logging
import signal

from PySide import QtCore, QtGui

import pycl.log
import pycl.main
import pycl.misc
import pycl.signals
from pycl.core import EE, Error, LogicalError

import pycl.gui.messages

from pytee.main_window import MainWindow

LOG = logging.getLogger("pytee.main")


class LogFilter(logging.Filter):
    """Filters all application logs."""

    def filter(self, record):
        return not record.name == "subtitles.reader"


def main():
    """The application's main function."""

    app = QtGui.QApplication(sys.argv)

    try:
        pycl.main.set_environment()
        pycl.signals.setup()

        # Setting up the application icon -->
        app_icon = QtGui.QIcon()

        for size in (24, 48):
            app_icon.addFile(os.path.join(INSTALL_DIR, "icons", "{0}x{0}".format(size), "apps", "{0}.png".format(constants.APP_UNIX_NAME)))
        app_icon.addFile(os.path.join(INSTALL_DIR, "icons", "scalable", "apps", "{0}.svg".format(constants.APP_UNIX_NAME)))

        app.setWindowIcon(app_icon)
        # Setting up the application icon <--

        debug_mode = False

        # Parsing command line options -->
        try:
            argv = [ pycl.misc.to_unicode(arg) for arg in sys.argv ]

            cmd_options, cmd_args = getopt.gnu_getopt(argv[1:],
                "dh", [ "debug-mode", "help" ] )

            for option, value in cmd_options:
                if option in ("-d", "--debug-mode"):
                    debug_mode = True
                elif option in ("-h", "--help"):
                    print app.tr(
                        """{0} [OPTIONS] MOVIE_PATH\n\n"""
                         """Options:\n"""
                         """ -d, --debug-mode  enable debug mode\n"""
                         """ -h, --help        show this help"""
                    ).format(argv[0])
                    sys.exit(0)
                else:
                    raise LogicalError()

            if len(cmd_args) != 1:
                raise Error(app.tr("You should pass a path to a movie as command line arguments."))

            movie_path = cmd_args[0]
        except Exception as e:
            raise Error(app.tr("Command line option parsing error:")).append(e)
        # Parsing command line options <--

        pycl.log.setup(debug_mode, filter = LogFilter())

        # Starting the application -->
        main_window = MainWindow()
        pycl.signals.connect(main_window.close)
        if pycl.signals.received():
            sys.exit(1)
        main_window.show()

        main_window.open(movie_path)
        # Starting the application <--
    except Exception as e:
        pycl.gui.messages.error(None, app.tr("Unable to start {0}").format(constants.APP_NAME), e)
        sys.exit(1)

    try:
        app.exec_()
    except Exception as e:
        pycl.gui.messages.error(None, app.tr("{0} crashed").format(constants.APP_NAME), e)
        sys.exit(1)

    LOG.info("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()

