#!/usr/bin/env python

"""Provides MPlayer Qt widget."""

import logging

from PySide import QtCore, QtGui

from mplayer.process import MPlayer

__ALL__ = [ "MPlayerWidget" ]
LOG = logging.getLogger("mplayer.widget")


def Control(func):
    """Logs all control method calls."""

    def decorator(self, *args):
        LOG.info("Player control: %s%s.", func.func_name,
            "({0})".format(args[0]) if len(args) == 1 else args)
        return func(self, *args)

    return decorator


class MPlayerWidget(QtGui.QWidget):
    """MPlayer Qt widget."""

    __mplayer = None
    """Running MPlayer instance."""

    __display_widget = None
    """Widget that displays the video."""


    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.__display_widget = QtGui.QWidget(self)
        self.__display_widget.setHidden(True)


    def get_control_actions(self):
        """Returns a dictionary of all control handlers.

        It may be useful for setting up hotkeys.
        """

        return {
            "osd_toggle": lambda: self.osd_toggle(),
            "pause":      lambda: self.pause(),
            "seek":       lambda seconds: self.seek(seconds),
            "volume":     lambda value: self.volume(value)
        }


    # TODO
    def open(self):
        movie_path = "/my_files/video/pub/Prison Break/prison.break.s02.rus.hdtvrip.novafilm.tv/prison.break.s02e03.rus.hdtvrip.novafilm.tv.avi"

        self.__mplayer = MPlayer()
        self.__mplayer.started.connect(self._mplayer_started)
        self.__mplayer.failed.connect(self._mplayer_failed)
        self.__mplayer.run(movie_path, self.__display_widget.winId())


    def paintEvent(self, event):
        """QWidget paint event handler"""

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawRect(0, 0, self.width(), self.height())


    @Control
    def osd_toggle(self):
        """Toggles the OSD displaying."""

        self.__mplayer.osd_toggle()


    @Control
    def pause(self):
        """Pauses the movie playing."""

        self.__mplayer.pause()


    def resizeEvent(self, event):
        """QWidget resize event handler"""

        if self.__opened():
            self.__scale_display_widget()


    @Control
    def seek(self, seconds):
        """Seeks for specified number of seconds."""

        self.__mplayer.seek(seconds)


    @Control
    def volume(self, value):
        """Increase/decrease volume."""

        self.__mplayer.volume(value)


    def _mplayer_failed(self, error):
        """Called when MPlayer failed to start."""

        LOG.error("Starting MPlayer failed: %s", error)
        self.__mplayer = None


    def _mplayer_started(self):
        """Called on MPlayer start."""

        self.__scale_display_widget()
        self.__display_widget.setHidden(False)


    def __opened(self):
        """Returns True if any movie is opened at this moment."""

        return self.__mplayer and self.__mplayer.get_movie()


    def __scale_display_widget(self):
        """Scales the display widget according to the movies aspect ratio."""

        width = self.width()
        height = self.height()
        aspect_ratio = self.__mplayer.get_movie().get_aspect_ratio()

        display_width = int(height * aspect_ratio)
        if display_width <= width:
            display_height = height
        else:
            display_height = int(width // aspect_ratio)
            display_width = width

        self.__display_widget.resize(display_width, display_height)
        self.__display_widget.move(
            (width - display_width) // 2,
            (height - display_height) // 2
        )

