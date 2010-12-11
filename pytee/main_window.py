#!/usr/bin/env python

"""Provides the application's main window."""

import os
import logging

import pysd.pysd
from PySide import QtCore, QtGui

import cl.gui.messages
from cl.core import EE, Error

import mplayer.widget
from mplayer.widget import MPlayerWidget
from subtitles.widget import SubtitlesWidget

from pytee.config import Config
import pytee.constants as constants

__all__ = [ "MainWindow" ]
LOG = logging.getLogger("pytee.main_window")


class MainWindow(QtGui.QWidget):
    """The application's main window."""

    _open_signal = QtCore.Signal(str)
    """Opens a movie for playing.

    This signal is to guarantee that real open() method will be called in the
    main loop.
    """

    __config = None
    """The application's configuration."""

    __save_config_timer = None
    """Timer for saving the config."""


    __player = None
    """The player widget."""

    __subtitles = None
    """The subtitles displaying widget."""


    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle(constants.APP_NAME)

        main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.__config = Config()
        self.__save_config_timer = QtCore.QTimer(self)
        self.__save_config_timer.timeout.connect(self._save_config)
        self.__save_config_timer.start(self.__config.get_config_saving_interval() * 1000)

        self.__player = MPlayerWidget()
        main_layout.addWidget(self.__player, 1)

        self.__subtitles = SubtitlesWidget()
        main_layout.addWidget(self.__subtitles)

        self.__player.failed.connect(self._open_failed)
        self.__player.pos_changed.connect(self.__subtitles.set_pos)
        self.__player.finished.connect(self.close)

        self.setup_hotkeys()
        self.resize(800, 600)

        self._open_signal.connect(self._open, QtCore.Qt.QueuedConnection)


    def __del__(self):
        if self.__save_config_timer is not None:
            self.__save_config_timer.stop()

        self.__close()


    def closeEvent(self, event):
        """QWidget's closeEvent()."""

        self.hide()
        self._save_config()
        self.__close()


    def open(self, movie_path):
        """Opens a movie for playing."""

        self._open_signal.emit(movie_path)


    def setup_hotkeys(self):
        """Sets up the hotkeys."""

        class Handler_proxy:
            def __init__(self, handler, args):
                self.__handler = handler
                self.__args = args

            def __call__(self, checked):
                return self.__handler(*self.__args)

        hotkeys = {
            "Space":                 "pause",
            "Left":                  "seek-3",
            "Right":                 "seek+3",
            "Comma":                 "seek-30",
            "Period":                "seek+30",
            "M":                     "seek-300",
            "Slash":                 "seek+300",
            "Up":                    "volume+10",
            "Down":                  "volume-10",
            "O":                     "osd_toggle",

            "Return":                "toggle_full_screen",

            "J":                     "next_alternative",
            "K":                     "prev_alternative",
            "A":                     "switch_alternative",

            "Q":                     "quit",
            "Escape":                "quit",
            QtGui.QKeySequence.Quit: "quit"
        }

        actions = {
            "toggle_full_screen": lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen(),
            "quit":               lambda: self.close()
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


    def _open(self, movie_path):
        """Does all work that is needed to be done for opening a movie file."""

        movie_path = os.path.abspath(movie_path)
        LOG.info("Opening '%s'...", movie_path)

        try:
            last_pos = self.__config.get_movie_last_pos(movie_path)
        except Exception, e:
            LOG.error(Error("Unable to get last watched position for {0}:", movie_path).append(e))
            last_pos = 0
        finally:
            LOG.debug("Last watched position for '%s': %s.", movie_path, last_pos)

        try:
            if not os.path.exists(movie_path):
                raise Error(self.tr("File '{0}' doesn't exist."), movie_path)

            if not os.path.isfile(movie_path):
                raise Error(self.tr("The movie path '{0}' points to non-file object."), movie_path)

            alternatives = []
            subtitles = []

            try:
                alternatives, subtitles = self.__find_related_media_files(movie_path)
            except Exception, e:
                LOG.error("%s", Error(self.tr("Unable to get the movie's info:")).append(e))

                try:
                    movie_dir = os.path.dirname(movie_path)
                    file_name_prefix = os.path.splitext(os.path.basename(movie_path))[0]
                    subtitle_extensions = [ ext[1:] for ext in pysd.pysd.SUBTITLE_EXTENSIONS ]

                    for file_name in os.listdir(movie_dir):
                        if (
                            file_name.lower().startswith(file_name_prefix.lower()) and
                            os.path.splitext(file_name)[1].lower() in subtitle_extensions
                        ):
                            subtitles.append(( os.path.join(movie_dir, file_name), "unknown" ))
                except Exception, e:
                    LOG.error("Unable to find the movie's subtitles. "
                        "Error while reading the movie directory '%s': %s.", movie_dir, EE(e))

            LOG.debug("Found alternative movies: %s.", alternatives)
            LOG.debug("Found subtitles: %s.", subtitles)

            self.__subtitles.open(subtitles)
            self.__player.open(movie_path, alternatives, last_pos)
            self.setWindowTitle("{0} - {1}".format(constants.APP_NAME, movie_path))
        except Exception, e:
            self.close()
            cl.gui.messages.warning(self, self.tr("Unable to play the movie"), e)


    def _open_failed(self, error):
        """Called when the player failed to open a movie."""

        cl.gui.messages.warning(self, self.tr("Unable to play the movie"), error)
        self.close()


    def _save_config(self):
        """Saves all configuration data."""

        LOG.debug("Saving configuration data...")

        try:
            player_state = self.__player.cur_state()

            if player_state["state"] in (
                mplayer.widget.PLAYER_STATE_FAILED,
                mplayer.widget.PLAYER_STATE_FINISHED
            ):
                self.__config.mark_movie_as_watched(player_state["movie_path"])
            elif player_state["state"] == mplayer.widget.PLAYER_STATE_OPENED and player_state["cur_pos"] > 0:
                self.__config.save_movie_last_position(player_state["movie_path"], player_state["cur_pos"])
        except Exception, e:
            LOG.error(Error("Unable to save configuration data:").append(e))


    def __close(self):
        """Frees all allocated resources and stops all running processes."""

        self.setWindowTitle(constants.APP_NAME)

        if self.__subtitles is not None:
            self.__subtitles.close()

        if self.__player is not None:
            self.__player.close()


    def __find_related_media_files(self, movie_path):
        """
        Finds files related to the movie: the same episode with another
        translation and subtitle files.
        """

        tools = pysd.pysd.Tv_show_tools()
        movie_path = os.path.abspath(movie_path)
        movie_file_name = os.path.basename(movie_path)
        movie_dir_path = os.path.dirname(movie_path)
        movie_names, movie_season, movie_episode, movie_delimiter, movie_extra_info = \
            tools.get_info_from_filename(movie_file_name)
        movie_names = set(movie_names)

        media_extensions = set(( ext[1:] for ext in pysd.pysd.MEDIA_EXTENSIONS ))
        subtitle_extensions = set(( ext[1:] for ext in pysd.pysd.SUBTITLE_EXTENSIONS ))
        extensions = media_extensions | subtitle_extensions

        alternatives = []
        subtitles = []

        for file_name in os.listdir(movie_dir_path):
            path = os.path.join(movie_dir_path, file_name)
            extension = os.path.splitext(file_name)[1].lower()

            if file_name != movie_file_name and extension in extensions and os.path.isfile(path):
                try:
                    names, season, episode, delimiter, extra_info = tools.get_info_from_filename(file_name)
                    names = set(names)
                except pysd.pysd.Not_found:
                    continue

                if movie_names.intersection(names) and movie_season == season and movie_episode == episode:
                    if extension in subtitle_extensions:
                        subtitles.append((path, extra_info))
                    else:
                        alternatives.append(path)

        return alternatives, subtitles

