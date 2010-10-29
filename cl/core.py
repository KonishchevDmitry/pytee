#!/usr/bin/env python

"""Core classes which is generally imported as from cl.core import *."""

from PySide import QtCore


class Error(Exception):
    """The base class for all exceptions that our code throws."""

    def __init__(self, error, *args):
        Exception.__init__(self, error.format(*args) if len(args) else str(error))


class Logical_error(Error):
    """Any logical error."""

    def __init__(self):
        Error.__init__(self, QtCore.QObject.tr("Logical error."))

