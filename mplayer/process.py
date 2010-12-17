#!/usr/bin/env python

"""Provides a class that represents a running MPlayer process."""

import errno
import logging
import os
import signal
import subprocess
import sys
import threading
import time

from PySide import QtCore

from cl.core import EE, Error

__all__ = [ "MPlayer" ]
LOG = logging.getLogger("mplayer.mplayer")


def Only_running(func):
    """Calls the method only if MPlayer is running."""

    def decorator(self, *args, **kwargs):
        if self.running():
            return func(self, *args, **kwargs)
        else:
            raise Error(self.tr("MPlayer is not running."))

    return decorator


class MPlayer(QtCore.QObject):
    """Represents a running MPlayer process.

    Note: the current implementation doesn't allow to run MPlayer twice.
    """

    failed = QtCore.Signal(str)
    """Emitted with error string when MPlayer failed to start."""

    started = QtCore.Signal()
    """Emitted on MPlayer start."""

    pos_changed = QtCore.Signal(int)
    """
    Emitted with time in milliseconds when current time position in playing
    movie changes.
    """

    terminated = QtCore.Signal()
    """Emitted on MPlayer termination."""


    _started_signal = QtCore.Signal(str)
    """Emitted on MPlayer start (for internal usage)."""

    _failed_signal = QtCore.Signal(str)
    """Emitted with error string when MPlayer failed to start (for internal usage)."""


    __state = "stopped"
    """Current MPlayer status (stopped|staging|running)."""

    __lock = None
    """Lock for __state changing."""


    __process = None
    """The MPlayer process."""

    __movie = None
    """A movie which is playing at this moment."""

    __osd_displaying = False
    """Is OSD displaying now?"""

    __update_timer = None
    """Timer for updating current MPlayer status."""


    def __init__(self, parent = None):
        super(MPlayer, self).__init__(parent)

        self.__lock = threading.Lock()

        self._started_signal.connect(self._started)
        self._failed_signal.connect(self._failed)

        self.__update_timer = QtCore.QTimer(self)
        self.__update_timer.timeout.connect(self._update)
        self.__update_timer.start(100)


    def __del__(self):
        self.terminate()


    @Only_running
    def cur_pos(self):
        """Returns current time position in milliseconds."""

        cur_pos = self.__get_property("time_pos", float, force_pausing = True, suppress_debug = True)
        return int(cur_pos * 1000)


    @Only_running
    def get_movie(self):
        """Returns a movie that is playing at this moment."""

        return self.__movie


    @Only_running
    def osd_toggle(self):
        """Toggles the OSD displaying."""

        self.__command("osd 1" if self.__osd_displaying else "osd 3")
        self.__osd_displaying = not self.__osd_displaying


    @Only_running
    def pause(self):
        """Pauses the movie playing."""

        self.__command("pause")


    @Only_running
    def paused(self):
        """Returns True if the MPlayer is paused."""

        return self.__get_property("pause", force_pausing = True, suppress_debug = True) == "yes"


    def run(self, *args):
        """Runs MPlayer."""

        if self.__state != "stopped":
            raise Error(self.tr("MPlayer is already running."))

        self.__state = "staging"

        # We have run MPlayer in another thread, because it is not going to
        # start if our main loop is locked at this moment.

        thread = threading.Thread(name = "MPlayer thread",
            target = self.__run, args = args)
        thread.start()


    def running(self):
        """
        Checks whether MPlayer is running (the state when we can send commands
        to it.
        """

        return self.__state == "running"


    @Only_running
    def seek(self, seconds, absolute = False):
        """Seeks for specified number of seconds."""

        self.__command("seek {0} {1}".format(seconds, 2 if absolute else 0))


    def terminate(self):
        """Terminates the MPlayer process."""

        with self.__lock:
            prev_state = self.__state
            self.__state = "stopped"

        if self.__process is not None:
            self.__terminate(self.__process)
            self.__process = None

        if prev_state == "running":
            self.terminated.emit()


    @Only_running
    def volume(self, value):
        """Increase/decrease volume."""

        self.__command("volume {0} 0".format(value))


    def _failed(self, error):
        """Called when MPlayer fails to start."""

        if self.__state != "staging":
            LOG.debug("Ignoring 'failed' signal. We already have state %s.", self.__state)
            return

        self.terminate()
        self.failed.emit(error)


    def _started(self, movie_path):
        """Called on successful MPlayer start."""

        if self.__state != "staging":
            LOG.debug("Ignoring 'started' signal. We already have state %s.", self.__state)
            return

        try:
            aspect_ratio = self.__get_property("aspect", float, force_pausing = True)
        except Exception, e:
            self.terminate()
            LOG.error("%s", Error("MPlayer failed to open '{0}'.", movie_path).append(e))
            self.failed.emit(self.tr("MPlayer failed to open '{0}'.").format(movie_path))
        else:
            self.__movie = Movie(movie_path, aspect_ratio)
            self.__state = "running"
            LOG.debug("We successfully started MPlayer for movie '%s'.", self.__movie)
            self.started.emit()


    def _update(self):
        """Called by timer to update current MPlayer status."""

        try:
            if self.running():
                self.pos_changed.emit(self.cur_pos())
        except Exception, e:
            if self.running():
                LOG.exception("MPlayer current status update failed. %s", e)


    def __command(self, command, suppress_debug = False):
        """Sends a command to the MPlayer."""

        if not suppress_debug:
            LOG.debug("Sending '%s' command to the MPlayer...", command)

        try:
            self.__process.stdin.write(command + "\n")
        except Exception, e:
            LOG.debug("Error while sending a command to the MPlayer: %s.", EE(e))
            self.__connection_closed()


    def __connection_closed(self):
        """Called when MPlayer closes stdin or stdout."""

        # Assuming that MPlayer terminated due to movie finish.
        self.terminate()
        raise Error(self.tr("The movie finished."))


    def __get_property(self, property_name, result_type = str, force_pausing = False, suppress_debug = False):
        """Requests a MPlayer property value."""

        self.__command("{0}get_property {1}".format(
            "pausing_keep_force " if force_pausing else "", property_name), suppress_debug)

        while True:
            try:
                line = self.__process.stdout.readline()
                if not line:
                    raise Error("unexpected end of file")
            except Exception, e:
                LOG.debug("Error while reading a command response from the MPlayer: %s.", EE(e))
                self.__connection_closed()

            if line.startswith("ANS_"):
                response_template = "ANS_{0}=".format(property_name)

                if line.startswith(response_template):
                    value = line[len(response_template):].rstrip()
                    try:
                        return result_type(value)
                    except ValueError:
                        LOG.error("Property %s has an invalid value '%s'.", property_name, value)
                        raise Error(self.tr("Internal error."))
                else:
                    LOG.error("Invalid response for property %s received: %s.", property_name, line.rstrip())
                    raise Error(self.tr("Internal error."))
            else:
                try:
                    sys.stdout.write(line)
                except Exception, e:
                    LOG.error("Unable to write MPlayer output to stdout: %s.", EE(e))


    def __run(self, movie_path, window_id, start_from = 0, paused = False):
        """Runs MPlayer process."""

        args = [
            "/usr/bin/mplayer",

            "-nosub",
            "-framedrop",
            "-slave", "-quiet",
            "-input", "nodefault-bindings", "-noconfig", "all",

            "-ss", str(start_from),

            # Forcing XV driver usage to disable VDPAU which may cause
            # system hang-up.
            "-vo", "xv",

            # This option is needed because of some bugs in PulseAudio
            # implementation. Lack of this option can cause problems with
            # pausing - video will be paused but wont be able to be
            # unpaused.
            "-ao", "sdl",

            "-wid", str(window_id),

            movie_path
        ]

        LOG.debug("Running MPlayer: %s", args)

        process = None
        error = None

        try:
            try:
                process = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, close_fds = True)
            except Exception, e:
                raise Error(self.tr("Unable to start MPlayer:")).append(e)

            if paused:
                try:
                    process.stdin.write("pause\n")
                except Exception, e:
                    raise Error(self.tr("MPlayer failed to open '{0}'."), movie_path)
        except Exception, e:
            LOG.error("%s", EE(e))

            if process is not None:
               self.__terminate(process)

            if self.__state == "staging":
                self._failed_signal.emit(EE(e))
        else:
            with self.__lock:
                if self.__state == "staging":
                    self.__process = process
                    self._started_signal.emit(movie_path)
                else:
                    self.__terminate(process)


    def __terminate(self, process):
        """Terminates a MPlayer process."""

        pid = process.pid
        LOG.debug("Killing the MPlayer process %s...", pid)

        try:
            process.stdin.close()
        except Exception, e:
            LOG.error("Unable to close the MPlayer process stdin: %s.", EE(e))

        try:
            process.stdout.close()
        except Exception, e:
            LOG.error("Unable to close the MPlayer process stdin: %s.", EE(e))

        try:
            start_time = time.time()

            while time.time() - start_time < 1:
                try:
                    os.kill(pid, signal.SIGTERM)
                except EnvironmentError, e:
                    if e.errno == errno.ESRCH:
                        break
                    else:
                        raise

                time.sleep(0.1)
            else:
                LOG.debug("Killing the MPlayer process %s by SIGKILL...", pid)

                try:
                    os.kill(pid, signal.SIGKILL)
                except EnvironmentError, e:
                    if e.errno != errno.ESRCH:
                        raise
        except Exception, e:
            LOG.error("Unable to kill the MPlayer process %s: %s.", pid, EE(e))



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
        return unicode(str)


    def __unicode__(self):
        return u'{{ "path": "{0}", "aspect_ratio": {1} }}'.format(self.__path, self.__aspect_ratio)

