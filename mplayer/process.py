#!/usr/bin/env python

"""Provides a class that represents a running MPlayer process."""

import logging
import subprocess
import sys
import threading

from PySide import QtCore, QtGui

from cl.core import *

__all__ = [ "MPlayer" ]
LOG = logging.getLogger("mplayer.mplayer")


# TODO
class MPlayer(QtCore.QObject):
    """Represents a running MPlayer process."""

    started = QtCore.Signal()
    """Emitted on MPlayer start."""

    failed = QtCore.Signal(str)
    """Emitted with error string when MPlayer failed to start."""

    pos_changed = QtCore.Signal(int)
    """
    Emitted with time in milliseconds when current time position in playing
    movie changes.
    """


    __process = None
    """The MPlayer process."""

    __stdin = None
    """The process' stdin."""

    __stdout = None
    """The process' stdout."""


    __movie = None
    """A movie that is playing at this moment."""

    __osd_displaying = False
    """Is OSD displaying now?"""

    __update_timer = None
    """Timer for updating current MPlayer status."""


    def __init__(self, parent = None):
        super(MPlayer, self).__init__(parent)

        self.__update_timer = QtCore.QTimer(self)
        self.__update_timer.timeout.connect(self._update)
        self.__update_timer.start(100)


    def __del__(self):
        if self.__process:
            # TODO
            LOG.debug("Terminating the MPlayer process...")
            self.__process.terminate()


    def run(self, *args):
        """Runs MPlayer."""

        thread = threading.Thread(name = "MPlayer thread",
            target = self.__run, args = args)
        thread.setDaemon(True)
        thread.start()


    def get_movie(self):
        """Returns a movie that is playing at this moment."""

        return self.__movie


    def osd_toggle(self):
        """Toggles the OSD displaying."""

        self.__command("osd 1" if self.__osd_displaying else "osd 3")
        self.__osd_displaying = not self.__osd_displaying


    def pause(self):
        """Pauses the movie playing."""

        self.__command("pause")


    def seek(self, seconds):
        """Seeks for specified number of seconds."""

        self.__command("seek {0} 0".format(seconds))


    def volume(self, value):
        """Increase/decrease volume."""

        self.__command("volume {0} 0".format(value))


    def _update(self):
        """Called by timer to update current MPlayer status."""

        try:
            if self.__movie:
                if self.__get_property("pause", force_pausing = True, suppress_debug = True) == "no":
                    cur_pos = self.__get_property("time_pos", float, force_pausing = True, suppress_debug = True)
                    self.pos_changed.emit(int(cur_pos * 1000))
        except Exception, e:
            LOG.error("MPlayer current status update failed. %s", e)


    def __command(self, command, suppress_debug = False):
        """Sends a command to the MPlayer."""

        if not suppress_debug:
            LOG.debug("Sending command '%s' to the MPlayer...", command)

        self.__stdin.write(command + "\n")


    def __get_property(self, property_name, result_type = str, force_pausing = False, suppress_debug = False):
        """Requests a MPlayer property value."""

        self.__command("{0}get_property {1}".format(
            "pausing_keep_force " if force_pausing else "", property_name), suppress_debug)

        response_template = "ANS_{0}=".format(property_name)

        while True:
            line = self.__stdout.readline()
            if not line:
                # TODO
                raise Exception("EOF")

            if line.startswith(response_template):
                try:
                    return result_type(line[len(response_template):].rstrip())
                except ValueError:
                    # TODO
                    raise Error("Invalid return value type for property '{0}'.", property_name)
            else:
                sys.stdout.write(line)


    def __run(self, movie_path, window_id):
        """Runs MPlayer."""

        try:
            args = [
                "/usr/bin/mplayer",
                "-slave", "-quiet",
                "-input", "nodefault-bindings", "-noconfig", "all",
                "-vo", "xv,sdl,x11",
                "-ao", "alsa,oss,sdl,arts", "-framedrop", "-contrast", "0", "-brightness", "0", "-hue", "0", "-saturation", "0", "-identify",
                #"-vo", "gl2",
                #"-vo", "xv",
#                "-zoom",
                "-wid", str(window_id),
                movie_path
            ]

            LOG.debug("Running MPlayer: %s", args)

            self.__process = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, close_fds = True)
            self.__stdin = self.__process.stdin
            self.__stdout = self.__process.stdout

            aspect_ratio = self.__get_property("aspect", float)
            self.__movie = Movie(movie_path, aspect_ratio)

            LOG.debug("We successfully started MPlayer for movie %s.", self.__movie)
        except Exception, e:
            LOG.error("Running MPlayer %s failed: %s", e)
            self.failed.emit(str(e))
        else:
            self.started.emit()



class Movie:
    """Stores information about a movie."""

    # Path to the movie.
    __path = None

    # The movie aspect ratio.
    __aspect_ratio = None


    def __init__(self, path, aspect_ratio):
        self.__path = path
        self.__aspect_ratio = aspect_ratio


    def get_aspect_ratio(self):
        """Returns the movie aspect ratio."""

        return self.__aspect_ratio


    def __str__(self):
        return '{{ "path": "{0}", "aspect_ratio": {1} }}'.format(self.__path, self.__aspect_ratio)

