#!/usr/bin/env python

"""
Provides tools for reading subtitle files and widgets for subtitle
displaying.
"""

import logging

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logging.getLogger("subtitles").addHandler(NullHandler())

