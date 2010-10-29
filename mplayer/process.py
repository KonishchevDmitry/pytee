#!/usr/bin/env python

"""Provides a class that represents a running MPlayer process."""

import logging
import subprocess
import sys
import threading

from PySide import QtCore, QtGui

__ALL__ = [ "MPlayer" ]
LOG = logging.getLogger("mplayer.mplayer")


class MPlayer(QtCore.QObject):
    """Represents a running MPlayer process."""

    # Emitted on MPlayer start.
    started = QtCore.Signal()

    # Emitted with error string when MPlayer failed to start.
    failed = QtCore.Signal(str)


    # The MPlayer process.
    __process = None

    # The process' stdin.
    __stdin = None

    # The process' stdout.
    __stdout = None


    # A movie that is playing at this moment.
    __movie = None


    def __init__(self, parent = None):
        super(MPlayer, self).__init__(parent)


    def __del__(self):
        if self.__process:
            # TODO
            LOG.debug("Terminating the MPlayer process...")
            self.__process.terminate()


    def run(self, *args):
        """Runs MPlayer."""

        thread = threading.Thread(name = "MPlayer starting thread",
            target = self.__run, args = args)
        thread.setDaemon(True)
        thread.start()


    def get_movie(self):
        """Returns a movie that is playing at this moment."""

        return self.__movie


    def __command(self, command):
        """Sends a command to the MPlayer."""

        self.__stdin.write(command + "\n")


    def __get_property(self, property_name):
        """Requests a MPlayer property value."""

        self.__command("get_property " + property_name)

        response_template = "ANS_{0}=".format(property_name)

        while True:
            line = self.__stdout.readline()
            if not line:
                # TODO
                raise Exception("EOF")

            if line.startswith(response_template):
                return line[len(response_template):]
            else:
                sys.stdout.write(line)


    def __run(self, movie_path, window_id):
        """Runs MPlayer."""

        try:
            args = [
                "/usr/bin/mplayer",
                "-slave", "-quiet",
                "-input", "nodefault-bindings", "-noconfig", "all",
                "-vo", "xv",
                "-wid", str(window_id),
                movie_path
            ]

            LOG.debug("Running MPlayer: %s", args)

            self.__process = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
            self.__stdin = self.__process.stdin
            self.__stdout = self.__process.stdout

            try:
                aspect_ratio = float(self.__get_property("aspect"))
            except ValueError, e:
                raise Error("Unable to determine the movie's aspect ratio.")

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

