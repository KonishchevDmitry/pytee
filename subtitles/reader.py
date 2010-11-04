#!/usr/bin/env python

"""Provides a function for reading subtitle files."""

import logging
import re

from PySide import QtCore

from cl import constants
from cl.core import *

__all__ = [ "read" ]
LOG = logging.getLogger("subtitles.reader")

FILE_LINE_MAX_SIZE = 1024
"""Maximum line size for a subtitle file."""


# TODO
class SubtitleReader(QtCore.QObject):
    def read(self, path, language):
        """Reads a subtitle file."""

        try:
            LOG.debug("Reading subtitle '%s' (%s):", path, language)
            subtitles = []

            with open(path) as file:
                repeat = False
                state = "id"
                last_line = ""
                line_num = 0
                eof = False

                id_re = re.compile(r"^(\d+)$")
                timings_re = re.compile(r"^(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{1,3})\s*-->\s*(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{1,3})$")

                while not eof:
                    if repeat:
                        repeat = False
                    else:
                        line = file.readline(FILE_LINE_MAX_SIZE)
                        if(len(line) >= FILE_LINE_MAX_SIZE):
                            raise Error(self.tr("Too big line length (>= {0}). May be it is not subtitle file?"), FILE_LINE_MAX_SIZE)

                        if line:
                            line = line.strip()
                            line_num += 1
                        else:
                            eof = True

                    if state == "id":
                        if line:
                            match = id_re.match(line)
                            if not match:
                                raise Error(self.tr("Invalid subtitle id '{0}' at line {1}."), line, line_num)

                            id = int(line)
                            LOG.debug("Id: %s.", id)

                            state = "timings"

                    elif state == "timings":
                        if line:
                            match = timings_re.match(line)
                            if not match:
                                raise Error(self.tr("Invalid subtitle timings '{0}' at line {1}."), line, line_num)

                            start_time = (
                                int(match.group(1)) * constants.HOUR_SECONDS +
                                int(match.group(2)) * constants.MINUTE_SECONDS +
                                int(match.group(3))
                            ) * 1000 + int(match.group(4))

                            end_time = (
                                int(match.group(5)) * constants.HOUR_SECONDS +
                                int(match.group(6)) * constants.MINUTE_SECONDS +
                                int(match.group(7))
                            ) * 1000 + int(match.group(8))

                            LOG.debug("Timings: %s - %s.", start_time, end_time)

                            state = "subtitle"
                            text = ""
                        else:
                            if eof:
                                raise Error(self.tr("Unexpected end of file."))
                            else:
                                raise Error(self.tr("Invalid subtitle timings at line {0}."), line_num)

                    elif state == "subtitle":
                        if eof or not last_line and id_re.match(line):
                            text = text.strip()

                            if text:
                                subtitles.append({
                                    "id":         id,
                                    "start_time": start_time,
                                    "end_time":   end_time,
                                    "text":       text
                                })
                                state = "id"
                                repeat = True
                            else:
                                if eof:
                                    raise Error(self.tr("Unexpected end of file."))
                                else:
                                    raise Error(self.tr("Missing subtitle text for subtitle {0} at line {1}."), id, line_num)
                        else:
                            LOG.debug("Text: %s", line)

                            if text:
                                text += "\n"
                            text += line

                    else:
                        raise LogicalError()

                    if not repeat:
                        last_line = line

            if not subtitles:
                raise Error(self.tr("File is empty."))
        except Exception, e:
            raise Error(self.tr("Error while reading subtitle file '{0}'. {1}"), path, e)


read = SubtitleReader().read

