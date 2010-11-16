#!/usr/bin/env python

"""Provides the application's main window."""

import os
import logging

import pysd
from PySide import QtCore, QtGui

from cl.core import *
from mplayer.widget import MPlayerWidget
from subtitles.widget import SubtitlesWidget

__all__ = [ "MainWindow" ]
LOG = logging.getLogger("pytee.main_window")


class MainWindow(QtGui.QWidget):
    """The application's main window."""

    __player = None
    """The player widget."""

    __subtitles = None
    """The subtitles displaying widget."""


    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.__player = MPlayerWidget()
        main_layout.addWidget(self.__player, 1)

        self.__subtitles = SubtitlesWidget()
        main_layout.addWidget(self.__subtitles)

        self.__player.pos_changed.connect(self.__subtitles.set_pos)

        # TODO
#        button = QtGui.QToolButton()
#        button.clicked.connect(self.__player.open)
#        main_layout.addWidget(button)

        self.setup_hotkeys()
        self.resize(640, 480)

# TODO
#        self.open()


    def open(self):

        # TODO FIXME
        try:
            movie_path = "/my_files/temp/Scrubs - 2x20.avi"
            import sys
            movie_path = sys.argv[1]

            alternatives, subtitles = self.__find_related_media_files(movie_path)
            LOG.debug("Found alternative movies: %s.", alternatives)
            LOG.debug("Found subtitles: %s.", subtitles)
            self.__subtitles.load(subtitles)

    #        movie_path = "/my_files/english/Lie To Me/Lie.To.Me.s03e03.rus.LostFilm.TV.avi"

            self.__player.open([ movie_path ] + alternatives)
        except Exception, e:
            print "ZZZZZZZZZZZZZZZZZZZZZ", e
            LOG.exception(">>>>>>>>>>>>>>>>>> %s", e)


    def setup_hotkeys(self):
        """Sets up the hotkeys."""

        class Handler_proxy:
            def __init__(self, handler, args):
                self.__handler = handler
                self.__args = args

            def __call__(self, checked):
                return self.__handler(*self.__args)

        hotkeys = {
            # TODO
            "O":                     "osd_toggle",
            "Space":                 "pause",
            "Left":                  "seek-3",
            "Right":                 "seek+3",
            "Up":                    "volume+10",
            "Down":                  "volume-10",

            # TODO
            "G":                     "open",

            "A":                     "switch_alternative",
            # TODO
#            "J":                     "next_alternative",
#            "K":                     "prev_alternative",

            "Q":                     "quit",
            "Escape":                "quit",
            QtGui.QKeySequence.Quit: "quit"
        }

        actions = {
            "open":               lambda: self.open(),
            "switch_alternative": lambda: self.__player.switch_alternative(),
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


    def __find_related_media_files(self, movie_path):
        """
        Finds files related to the movie: the same episode with another
        translation and subtitle files.
        """

        tools = pysd.Tv_show_tools()
        movie_path = os.path.abspath(movie_path)
        movie_file_name = os.path.basename(movie_path)
        movie_dir_path = os.path.dirname(movie_path)
        movie_names, movie_season, movie_episode, movie_delimiter, movie_extra_info = \
            tools.get_info_from_filename(movie_file_name)
        movie_names = set(movie_names)

        media_extensions = set(( ext[1:] for ext in pysd.MEDIA_EXTENSIONS ))
        subtitle_extensions = set(( ext[1:] for ext in pysd.SUBTITLE_EXTENSIONS ))
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
                except pysd.Not_found:
                    continue

                if movie_names.intersection(names) and movie_season == season and movie_episode == episode:
                    if extension in subtitle_extensions:
                        subtitles.append((path, extra_info))
                    else:
                        alternatives.append(path)

        return alternatives, subtitles

