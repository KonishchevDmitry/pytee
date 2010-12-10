#!/usr/bin/env python

"""Provides a class for reading and writing the application's configuration."""

import logging
# TODO FIXME: debian package

__all__ = [ "Config" ]
LOG = logging.getLogger("pytee.config")


class Config:
    """Configuration file object."""

    def mark_movie_as_watched(self, movie_path):
        """Marks a movie as watched (forgets its last position)."""

        LOG.debug("Marking movie '%s' as watched.", movie_path)

    def save_movie_last_position(self, movie_path, position):
        """Saves last position for a movie."""

        LOG.debug("Saving last position (%s) for movie '%s'.", position, movie_path)

