#!/usr/bin/env python

"""Provides the application's main window."""

import logging

from PySide import QtCore, QtGui

from cl.core import *
from mplayer.widget import MPlayerWidget

__ALL__ = [ "MainWindow" ]
LOG = logging.getLogger("pytee.main_window")


class MainWindow(QtGui.QWidget):
    """The application's main window."""

    __player = None
    """The player widget."""


    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        self.setLayout(main_layout)

        self.__player = MPlayerWidget()
        main_layout.addWidget(self.__player)

        button = QtGui.QToolButton()
        button.clicked.connect(self.__player.open)
        main_layout.addWidget(button)

        self.setup_hotkeys()
        self.resize(640, 480)

        self.__player.open()


    def setup_hotkeys(self):
        """Sets up the hotkeys."""

        class Handler_proxy:
            def __init__(self, handler, args):
                self.__handler = handler
                self.__args = args

            def __call__(self, checked):
                return self.__handler(*self.__args)

        hotkeys = {
            "O":                     "osd_toggle",
            "Space":                 "pause",
            "Left":                  "seek-3",
            "Right":                 "seek+3",
            "Up":                    "volume+10",
            "Down":                  "volume-10",

            "Q":                     "quit",
            "Escape":                "quit",
            QtGui.QKeySequence.Quit: "quit"
        }

        actions = {
            "quit": lambda: self.close()
        }

        for key_name, action_name in hotkeys.iteritems():
            args = ()

            for exception_name in ("seek", "volume"):
                if action_name.startswith(exception_name):
                    try:
                        args = ( int(action_name[len(exception_name):]), )
                    except ValueError:
                        raise Error(self.tr("Invalid action '{0}' for hotkey '{1}'."), action_name, key_name)

                    action_name = exception_name

                    break

            if isinstance(key_name, str):
                try:
                    key = getattr(QtCore.Qt, "Key_" + key_name)
                except AttributeError:
                    raise Error(self.tr("Invalid hotkey '{0}'."), key_name)
            else:
                key = key_name

            handler = actions.get(action_name) or self.__player.get_control_actions().get(action_name)
            if not handler:
                raise Error(self.tr("Invalid action '{0}' for hotkey '{1}'."), action_name, key_name)

            action = QtGui.QAction(self)
            action.setShortcut(key)
            action.triggered.connect(Handler_proxy(handler, args))
            self.addAction(action)

