#!/usr/bin/env python

"""Provides a function for reading subtitle files."""

import codecs
import logging
import os
import re

from PySide import QtCore

import pysd

from cl import constants
from cl.core import *

__all__ = [ "read" ]
LOG = logging.getLogger("subtitles.reader")

MAX_FILE_SIZE = constants.MEGABYTE
"""Maximum size of a subtitle file."""

MAX_FILE_LINE_SIZE = constants.KILOBYTE
"""Maximum size of a subtitle file line."""


class SubtitleReader(QtCore.QObject):
    """A class which implements all logic for reading subtitle files."""

    __encodings = { "rus": [ "cp1251" ] }
    """Language-specific encodings."""


    def read(self, path, language):
        """Reads a subtitle file."""

        try:
            subtitles = []

            LOG.debug("Reading subtitle file '%s' (%s):", path, language)

            if os.path.getsize(path) >= MAX_FILE_SIZE:
                raise Error(self.tr("Too big file size. May be it is not a subtitle file?"))

            return self.__read(path, self.__determine_encoding(path, language))
        except Exception, e:
            raise Error(self.tr("Error while reading subtitle file '{0}':"), path).append(e)


    def __determine_encoding(self, path, language):
        """Tries to determine the subtitle file encoding.

        Returns None if fail.
        """

        if len(language) == 2:
            language = pysd.LANGUAGES.get(language, "unknown")

        encodings = self.__encodings.get(language, [])
        encodings = encodings + [ "utf8" ]

        for encoding in encodings:
            try:
                with codecs.open(path, encoding = encoding) as file:
                    file.read()
            except ValueError:
                pass
            else:
                return encoding

        return None


    def __read(self, path, encoding):
        """Reads a subtitle file."""

        subtitles = []

        with codecs.open(path, encoding = encoding) if encoding else open(path) as file:
            # Cut off UTF-8 byte order mark which confuses re module
            data = file.read(1)
            if data[:1] != u"\ufeff":
                file.seek(0)

            repeat = False
            state = "id"
            last_line = ""
            line_num = 0
            eof = False

            id_re = re.compile(r"^\s*(\d+)\s*$")
            timings_re = re.compile(r"^\s*(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{1,3})\s*-->\s*(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{1,3})\s*$")

            while not eof:
                if repeat:
                    repeat = False
                else:
                    line = file.readline(MAX_FILE_LINE_SIZE)
                    if(len(line) >= MAX_FILE_LINE_SIZE):
                        raise Error(self.tr("Too big file line length (>= {0}). May be it is not a subtitle file?"), MAX_FILE_LINE_SIZE)

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
                            # TODO
#                            pass
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

        return subtitles


read = SubtitleReader().read

