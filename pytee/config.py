#!/usr/bin/env python

"""Provides a class for reading and writing the application's configuration."""

import errno
import logging
import os
import shutil
import sqlite3
import time

from cl.core import Error

from pytee import constants

__all__ = [ "Config" ]
LOG = logging.getLogger("pytee.config")


class Config:
    """Configuration file object."""

    __db = None
    """Database for storing the configuration data."""


    __config_saving_interval = constants.MINUTE_SECONDS
    """Interval with which we should save the configuration data."""

    __last_pos_lifetime = 4 * constants.WEEK_SECONDS
    """Time after which we forget a movie's last position."""


    def __init__(self):
        config_dir = os.path.expanduser("~/." + constants.APP_UNIX_NAME)
        db_path = os.path.join(config_dir, "config.sqlite")

        try:
            try:
                os.makedirs(config_dir)
            except EnvironmentError, e:
                if e.errno != errno.EEXIST:
                    raise

            self.__db = sqlite3.connect(db_path)

            self.__db.execute("""
                CREATE TABLE IF NOT EXISTS last_pos (
                    file_path TEXT PRIMARY KEY,
                    file_name TEXT,
                    position INTEGER,
                    last_update INTEGER
                )
            """)

            self.__db.execute(
                "DELETE FROM last_pos WHERE last_update <= ?",
                ( int(time.time()) - self.__last_pos_lifetime, ))

            self.__db.execute("VACUUM")
            self.__db.commit()
        except Exception, e:
            raise Error("Unable to open database '{0}'.", db_path)


    def __del__(self):
        if self.__db is not None:
            try:
                self.__db.close()
            except Exception, e:
                LOG.error(Error("Unable to close the database:").append(e))


    def get_config_saving_interval(self):
        """Returns interval with which we should save the configuration data."""

        return self.__config_saving_interval


    def get_movie_last_pos(self, movie_path):
        """Returns a movie's last position."""

        movie = self.__db.execute("""
            SELECT
                position
            FROM
                last_pos
            WHERE
                file_path = ?""", (movie_path,)).fetchone()

        if movie is None:
            movie = self.__db.execute("""
                SELECT
                    position
                FROM
                    last_pos
                WHERE
                    file_name = ?""",
                (os.path.basename(movie_path),)).fetchone()

        if movie is None:
            movie = (0,)

        return movie[0]


    def mark_movie_as_watched(self, movie_path):
        """Marks a movie as watched (forgets its last position)."""

        LOG.debug("Marking movie '%s' as watched.", movie_path)

        self.__db.execute("""
            DELETE FROM last_pos WHERE file_path = ?""", (movie_path,))
        self.__db.commit()


    def save_movie_last_position(self, movie_path, position):
        """Saves last position for a movie."""

        LOG.debug("Saving last position (%s) for movie '%s'.", position, movie_path)

        self.__db.execute("""
            INSERT OR REPLACE INTO last_pos
                (file_path, file_name, position, last_update)
            VALUES
                (?, ?, ?, ?)
        """, (movie_path, os.path.basename(movie_path), position, int(time.time())))
        self.__db.commit()

