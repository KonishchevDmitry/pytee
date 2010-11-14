#!/usr/bin/env python

"""Core classes which is generally imported as from cl.core import *."""

from PySide import QtCore

__all__ = [ "Error", "LogicalError" ]


class Error(Exception):
    """The base class for all exceptions that our code throws."""

    def __init__(self, error, *args):
        Exception.__init__(self, error.format(*args) if len(args) else unicode(error))


    # TODO FIXME
    def append(self, error, *args):
        Exception.__init__(self, unicode(self) + " " + (error.format(*args) if len(args) else unicode(error)))
        return self


class LogicalError(Error):
    """Any logical error."""

    def __init__(self):
        Error.__init__(self, QtCore.QObject.tr("Logical error."))

