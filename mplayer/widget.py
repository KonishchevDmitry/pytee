#!/usr/bin/env python

"""Provides MPlayer Qt widget."""

import logging

from PySide import QtCore, QtGui

from mplayer.process import MPlayer

__all__ = [ "MPlayerWidget" ]
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

    pos_changed = QtCore.Signal(int)
    """
    Emitted with time in milliseconds when current time position in playing
    movie changes.
    """

    __players = None
    """Running MPlayer instances."""

    # TODO
    __cur_id = -1
    """Index of currently active MPlayer instance."""

    __display_widgets = None
    """Widgets that display the video."""


    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.__players = []
        self.__display_widgets = []


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
    def open(self, movie_paths):
        for movie_path in movie_paths:
            player = MPlayer()
            self.__players.append(player)
            player.started.connect(self._mplayer_started)
            player.failed.connect(self._mplayer_failed)
            # TODO
            player.pos_changed.connect(self._pos_changed)

            display_widget = QtGui.QWidget(self)
            self.__display_widgets.append(display_widget)
            display_widget.lower()

            player.run(movie_path, display_widget.winId())


    @Control
    def osd_toggle(self):
        """Toggles the OSD displaying."""

        self.__player().osd_toggle()


    def paintEvent(self, event):
        """QWidget paint event handler"""

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.drawRect(0, 0, self.width(), self.height())


    @Control
    def pause(self):
        """Pauses the movie playing."""

        self.__player().pause()
# TODO
#        self.__display_widget.raise_()


    def resizeEvent(self, event):
        """QWidget resize event handler"""

        # TODO
        if self.__opened():
            for player in self.__players:
                self.__scale_display_widget(self.__display_widget(player), player.get_movie().get_aspect_ratio())


    @Control
    def seek(self, seconds):
        """Seeks for specified number of seconds."""

        self.__player().seek(seconds)


    @Control
    def switch_alternative(self):
        """
        Switches to alternative movie if the main movie is playing now, or
        switches to the main movie if an alternative movie is playing now.
        """

        # TODO
        if self.__cur_id:
            self.__switch_to(0)
        else:
            self.__switch_to(1)


    @Control
    def volume(self, value):
        """Increase/decrease volume."""

        self.__player().volume(value)


    def _mplayer_failed(self, error):
        """Called when MPlayer failed to start."""

        LOG.error("Starting MPlayer failed: %s", error)
        player = self.sender()

        if self.__is_main_movie(player):
            self.__close()
        else:
            self.__close_movie(player)


    def _mplayer_started(self):
        """Called on MPlayer start."""

        player = self.sender()
        display_widget = self.__display_widget(player)
        self.__scale_display_widget(display_widget, player.get_movie().get_aspect_ratio())

        if self.__is_main_movie(player):
            # TODO
            display_widget.setHidden(False)
            self.__cur_id = 0


    def _pos_changed(self, pos):
        """
        Emitted with time in milliseconds when current time position in playing
        movie changes.
        """

        if self.sender() is self.__player():
            self.pos_changed.emit(pos)


    def __close(self):
        """Closes all movies."""

        for player in self.__players[:]:
            self.__close_movie(player)


    def __close_movie(self, player):
        """Closes a movie."""

        movie_id = self.__players.index(player)
        # TODO terminate
        del self.__players[movie_id]
        # TODO destroy
        del self.__display_widgets[movie_id]


    def __is_main_movie(self, player = None):
        """Returns True is player is the main movie player."""

        if player is None:
            return not self.__cur_id
        else:
            return player is self.__players[0]


    def __display_widget(self, player = None):
        """Returns a display widget corresponding to the player."""

        if player is None:
            player = self.__player()

        return self.__display_widgets[self.__players.index(player)]


    def __player(self):
        """Returns currently active MPlayer instance."""

        # TODO
        if self.__cur_id >= 0:
            return self.__players[self.__cur_id]


    def __opened(self):
        """Returns True if any movie is opened at this moment."""

        return self.__player() and self.__player().get_movie()


    def __scale_display_widget(self, widget, aspect_ratio):
        """Scales the display widget according to the movies aspect ratio."""

        width = self.width()
        height = self.height()

        display_width = int(height * aspect_ratio)
        if display_width <= width:
            display_height = height
        else:
            display_height = int(width // aspect_ratio)
            display_width = width

        widget.resize(display_width, display_height)
        widget.move(
            (width - display_width) // 2,
            (height - display_height) // 2
        )


    def __switch_to(self, movie_id):
        """Switches to a movie with the specified id."""

        if not self.__player().paused():
            self.__player().pause()
        self.__display_widget().setHidden(True)

        if self.__is_main_movie():
            cur_pos = self.__player().cur_pos()
            self.__cur_id = movie_id
            # TODO
            self.__player().seek(float(cur_pos) / 1000, True)
        else:
            self.__cur_id = movie_id
            self.__player().pause()

        self.__display_widget().setHidden(False)

