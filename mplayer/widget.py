"""Provides MPlayer Qt widget."""

import logging

from PySide import QtCore, QtGui

from pycl.core import EE, Error

import pycl.gui.messages
import pycl.main

from mplayer.process import MPlayer

LOG = logging.getLogger("mplayer.widget")


PLAYER_STATE_CLOSED = "closed"
"""No movie is opened now."""

PLAYER_STATE_OPENING = "opening"
"""Player is opening a movie."""

PLAYER_STATE_FAILED = "failed"
"""Player failed to open a movie."""

PLAYER_STATE_OPENED = "opened"
"""Player has opened a movie and playing it now."""

PLAYER_STATE_FINISHED = "finished"
"""Player has finished playing a movie."""


def _movie_control(func):
    """Wraps methods that controls a movie playing."""

    def decorator(self, *args):
        LOG.info("Player control: %s%s.", func.func_name,
            "({0})".format(args[0]) if len(args) == 1 else args)

        try:
            if self.opened():
                return func(self, *args)
            else:
                raise Error(self.tr("No movie is opened."))
        except Exception as e:
            LOG.warning("Player control request rejected. %s", EE(e))

    return decorator

_player_control = _movie_control
"""Wraps methods that controls a whole player."""


class MPlayerWidget(QtGui.QWidget):
    """MPlayer Qt widget."""

    pos_changed = QtCore.Signal(int)
    """
    Emitted with time in milliseconds when current time position in the main
    movie changes.
    """

    failed = QtCore.Signal(str)
    """Emitted if the player has failed to open a movie."""

    finished = QtCore.Signal()
    """
    Emitted if the main movie finished its playing and the player has closed
    due to this.
    """


    __movie_path = None
    """Path to the playing movie."""

    __state = PLAYER_STATE_CLOSED
    """Current state name."""


    __players = None
    """Running MPlayer instances."""

    __cur_id = None
    """Index of currently active MPlayer instance."""

    __cur_alt_id = None
    """Index of currently selected alternative movie."""

    __display_widgets = None
    """Widgets that display the video."""


    __redraw_timer = None
    """Timer for movie image redrawing."""


    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(0, 0, 0))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.__players = []
        if not pycl.main.is_osx():
            self.__display_widgets = []


    def __del__(self):
        self.close()


    def close(self):
        """Closes all opened movies."""

        if self.__players is not None:
            for player in self.__players[:]:
                self.__close_movie(player)

        if self.__redraw_timer is not None:
            self.__redraw_timer.stop()
            self.__redraw_timer = None

        self.__state = PLAYER_STATE_CLOSED


    def cur_state(self):
        """Returns current player state."""

        state = { "state": self.__state }

        if self.__state in (
            PLAYER_STATE_OPENING,
            PLAYER_STATE_FAILED,
            PLAYER_STATE_OPENED,
            PLAYER_STATE_FINISHED
        ):
            state["movie_path"] = self.__movie_path

            if self.__state == PLAYER_STATE_OPENED:
                player = self.__player()

                if player.running():
                    try:
                        state["cur_pos"] = player.cur_pos()
                    except Exception as e:
                        if player.running():
                            LOG.error("Unable to get current playing position for movie '%s': %s", state["movie_path"], e)

                            # Not available yet
                            state["cur_pos"] = -1
                        else:
                            # Assuming that we've finished playing the movie.
                            state["cur_pos"] = 0
                else:
                    # Assuming that we've finished playing the movie.
                    state["cur_pos"] = 0

        return state


    def get_control_actions(self):
        """Returns a dictionary of all control handlers.

        It may be useful for setting up hotkeys.
        """

        return {
            "osd_toggle":         lambda: self.osd_toggle(),
            "pause":              lambda: self.pause(),
            "seek":               lambda seconds: self.seek(seconds),
            "volume":             lambda value: self.volume(value),
            "prev_alternative":   lambda: self.previous_alternative(),
            "next_alternative":   lambda: self.next_alternative(),
            "switch_alternative": lambda: self.switch_alternative()
        }


    @_player_control
    def next_alternative(self):
        """Switches to the next alternative movie."""

        self.__cur_alt_id += 1
        if self.__cur_alt_id >= len(self.__players):
            self.__cur_alt_id = min(1, len(self.__players) - 1)

        self.__switch_to(self.__cur_alt_id)


    def open(self, movie_path, alternatives, last_pos = 0):
        """Opens a movie and optional alternative movies for playing."""

        self.close()

        try:
            self.__movie_path = movie_path
            self.__state = PLAYER_STATE_OPENING

            # Rewind a few seconds back
            last_pos = max(0, last_pos // 1000 - 3)

            self.__cur_id = 0
            self.__cur_alt_id = int(bool(len(alternatives)))

            for movie_id, movie_path in enumerate([ movie_path ] + alternatives):
                player = MPlayer()

                player.failed.connect(self._mplayer_failed)
                player.started.connect(self._mplayer_started)
                player.pos_changed.connect(self._pos_changed)
                player.terminated.connect(self._mplayer_terminated, QtCore.Qt.QueuedConnection)

                if pycl.main.is_osx():
                    display_widget = None
                else:
                    display_widget = QtGui.QWidget(self)
                    display_widget.setVisible(False)

                try:
                    player.run(movie_path, last_pos * (movie_id == 0),
                        bool(movie_id), display_widget)
                except Exception as e:
                    if display_widget is not None:
                        display_widget.setParent(None)

                    if movie_id:
                        pycl.gui.messages.warning(self,
                            self.tr("Unable to play the movie."),
                            Error(self.tr("Unable to play '{0}':"), movie_path).append(EE(e)), block = False)
                    else:
                        raise Error(self.tr("Unable to play '{0}':"), movie_path).append(e)
                else:
                    if display_widget is not None:
                        self.__display_widgets.append(display_widget)
                    self.__players.append(player)

            if pycl.main.is_osx():
                self.__redraw_timer = QtCore.QTimer(self)
                self.__redraw_timer.timeout.connect(self.repaint)
                self.__redraw_timer.start(1000 / 24)
        except:
            self.close()
            raise


    def opened(self):
        """Returns True if any movie is opened."""

        return bool(self.__players)


    @_movie_control
    def osd_toggle(self):
        """Toggles the OSD displaying."""

        self.__player().osd_toggle()


    @_movie_control
    def pause(self):
        """Pauses the movie playing."""

        self.__player().pause()

    if pycl.main.is_osx():
        def paintEvent(self, event):
            """Qt's paintEvent handler."""

            if self.opened() and self.__player().running():
                dimensions = self.__get_display_dimensions(
                    self.__player().get_movie().get_aspect_ratio())

                painter = QtGui.QPainter(self)
                painter.drawImage(QtCore.QRectF(*dimensions),
                    self.__player().get_movie_image())
            else:
                super(MPlayerWidget, self).paintEvent(event)


    @_player_control
    def previous_alternative(self):
        """Switches to the previous alternative movie."""

        self.__cur_alt_id -= 1
        if self.__cur_alt_id < 1:
            self.__cur_alt_id = len(self.__players) - 1

        self.__switch_to(self.__cur_alt_id)


    if not pycl.main.is_osx():
        def resizeEvent(self, event):
            """QWidget's resize event handler."""

            for player in self.__players:
                if player.running():
                    self.__scale_display_widget(self.__display_widget(player),
                        player.get_movie().get_aspect_ratio())


    @_movie_control
    def seek(self, seconds):
        """Seeks for specified number of seconds."""

        self.__player().seek(seconds)


    @_player_control
    def switch_alternative(self):
        """
        Switches to alternative movie if the main movie is playing now, or
        switches to the main movie if an alternative movie is playing now.
        """

        if self.__cur_id:
            self.__switch_to(0)
        else:
            self.__switch_to(min(self.__cur_alt_id, len(self.__players) - 1))


    @_movie_control
    def volume(self, value):
        """Increase/decrease volume."""

        self.__player().volume(value)


    def _mplayer_failed(self, error):
        """Called when MPlayer failed to open a movie."""

        player = self.sender()

        if self.__is_main_movie(player):
            self.close()
            self.__state = PLAYER_STATE_FAILED
            self.failed.emit(error)
        else:
            if self.__player() is player:
                self.__switch_to(0)
            self.__close_movie(player)


    def _mplayer_started(self):
        """Called when MPlayer successfully started."""

        player = self.sender()

        if not pycl.main.is_osx():
            display_widget = self.__display_widget(player)
            self.__scale_display_widget(display_widget,
                player.get_movie().get_aspect_ratio())

            if self.__player() is player:
                display_widget.setVisible(True)

        if self.__is_main_movie(player):
            self.__state = PLAYER_STATE_OPENED


    def _mplayer_terminated(self):
        """Called on MPlayer termination."""

        player = self.sender()
        if player not in self.__players:
            return

        if not pycl.main.is_osx():
            self.__display_widget(player).setVisible(False)

        if self.__is_main_movie(player):
            self.__state = PLAYER_STATE_FINISHED
            self.finished.emit()


    def _pos_changed(self, pos):
        """
        Emitted with time in milliseconds when current time position in playing
        movie changes.
        """

        if self.sender() is self.__player() and self.__is_main_movie():
            self.pos_changed.emit(pos)


    def __close_movie(self, player):
        """Closes a movie."""

        movie_id = self.__players.index(player)

        player.terminate()
        del self.__players[movie_id]

        if not pycl.main.is_osx():
            self.__display_widgets[movie_id].setParent(None)
            del self.__display_widgets[movie_id]


    def __get_display_dimensions(self, aspect_ratio):
        """Returns dimensions of the player's display."""

        width = self.width()
        height = self.height()

        display_width = int(height * aspect_ratio)
        if display_width <= width:
            display_height = height
        else:
            display_width = width
            display_height = int(width / aspect_ratio)

        x = (width - display_width) // 2
        y = (height - display_height) // 2

        return x, y, display_width, display_height


    def __is_main_movie(self, player = None):
        """Returns True is player is the main movie player."""

        if player is None:
            return not self.__cur_id
        else:
            return player is self.__players[0]


    if not pycl.main.is_osx():
        def __display_widget(self, player = None):
            """Returns a display widget corresponding to the player."""

            if player is None:
                player = self.__player()

            return self.__display_widgets[self.__players.index(player)]


    def __player(self):
        """Returns currently active MPlayer instance."""

        return self.__players[self.__cur_id]


    if not pycl.main.is_osx():
        def __scale_display_widget(self, widget, aspect_ratio):
            """Scales the display widget according to the movies aspect ratio."""

            x, y, display_width, display_height = self.__get_display_dimensions(aspect_ratio)
            widget.resize(display_width, display_height)
            widget.move(x, y)


    def __switch_to(self, movie_id):
        """Switches to a movie with the specified id."""

        if self.__cur_id == movie_id:
            return

        LOG.debug("Switching to the movie %s from %s.", movie_id, self.__cur_id)

        try:
            if self.__player().running():
                if not self.__player().paused():
                    self.__player().pause()
        except Exception as e:
            LOG.debug("Unable to pause current movie. %s", EE(e))

        if not pycl.main.is_osx():
            self.__display_widget().setVisible(False)

        seek_to = -1
        if self.__is_main_movie():
            try:
                seek_to = self.__player().cur_pos()
            except Exception as e:
                LOG.debug("Unable to get movie's current position. %s", EE(e))

        self.__cur_id = movie_id
        if self.__player().running():
            try:
                if seek_to < 0:
                    self.__player().pause()
                else:
                    self.__player().seek(float(seek_to) / 1000, True)
            except Exception as e:
                LOG.debug("Unable to continue playing of the target movie. %s", EE(e))

        if not pycl.main.is_osx():
            self.__display_widget().setVisible(self.__player().running())

