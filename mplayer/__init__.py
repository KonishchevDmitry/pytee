#!/usr/bin/env python

"""Provides a media player widget with MPlayer backend."""

import logging

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logging.getLogger("mplayer").addHandler(NullHandler())

