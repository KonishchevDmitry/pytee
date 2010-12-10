#!/usr/bin/env python

"""Provides a Qt widgets for displaying movie's subtitles."""

import logging

from PySide import QtCore, QtGui

from cl.core import EE

import cl.gui.messages

import subtitles.reader as subtitle_reader

__all__ = [ "SubtitlesWidget" ]
LOG = logging.getLogger("subtitles.widget")


class SubtitlesWidget(QtGui.QWidget):
    """A Qt widget for displaying a set of movie's subtitles."""

    __cur_pos = 0
    """Current position in the playing movie."""

    __subtitles = None
    """Subtitles to display."""

    __cur_text = None
    """QLabel with text of a current subtitle."""

    __subtitle_layout = None
    """QLayout with subtitles."""

    __subtitle_widgets = None
    """Widgets that displays subtitles."""


    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.setVisible(False)
        main_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.__subtitles = []

        # Text of a current subtitle -->
        self.__cur_text = QtGui.QLabel()
        self.__cur_text.setAlignment(QtCore.Qt.AlignCenter)
        self.__cur_text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        font = self.__cur_text.font()
        font.setPointSize(12)
        self.__cur_text.setFont(font)

        main_layout.addWidget(self.__cur_text)
        # Text of a current subtitle <--

        self.__subtitle_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        main_layout.addLayout(self.__subtitle_layout)

        self.__subtitle_widgets = []


    def close(self):
        """Closes previously opened subtitles."""

        self.__cur_pos = 0
        self.__subtitles = []
        self.__cur_text.setText("")

        for widget in self.__subtitle_widgets:
            self.__subtitle_layout.removeWidget(widget)
        self.__subtitle_widgets = []

        self.setVisible(False)


    def open(self, subtitles):
        """Opens subtitles for displaying in the widget.

        subtitles -- a list of tuples (subtitle_path, subtitle_language)
        """

        self.close()

        # Reading the subtitle files -->
        errors = []

        for subtitle in sorted(subtitles, cmp = self.__subtitle_cmp):
            try:
                subtitle_data = subtitle_reader.read(*subtitle)
            except Exception, e:
                errors.append(EE(e))
            else:
                self.__subtitles.append({
                    "cur_id":    -1,
                    "find_from": -1,
                    "data":      subtitle_data
                })

        if errors:
            cl.gui.messages.warning(self,
                self.tr("Unable to open subtitles"), "\n".join(errors), block = False )
        # Reading the subtitle files <--

        # Choosing the proper alignment -->
        if len(self.__subtitles) == 3:
            alignment = (
                QtCore.Qt.AlignRight,
                QtCore.Qt.AlignCenter,
                QtCore.Qt.AlignLeft
            )
        elif len(self.__subtitles) == 2:
            alignment = (
                QtCore.Qt.AlignRight,
                QtCore.Qt.AlignLeft
            )
        else:
            alignment = ( QtCore.Qt.AlignCenter for i in xrange(0, len(self.__subtitles)) )
        # Choosing the proper alignment <--

        # Creating the widgets -->
        for subtitle, text_alignment in zip(self.__subtitles, alignment):
            widget = SubtitleWidget(subtitle["data"], text_alignment)
            self.__subtitle_widgets.append(widget)
            self.__subtitle_layout.addWidget(widget)
        # Creating the widgets <--

        self.__update(self.__cur_pos)
        self.setVisible(bool(self.__subtitles))


    def set_pos(self, cur_pos):
        """Sets current position in the playing movie."""

        if self.__cur_pos != cur_pos:
            self.__update(cur_pos)
            self.__cur_pos = cur_pos


    def __lookup(self, subtitles, pos, find_from = -1):
        """Finds a subtitle for the specified position.

        Returns a tuple (id, nearest_id) where id may be -1 if there is no
        subtitle for this time position.
        """

        cur_id = max(0, find_from)
        direction = 1 if subtitles[cur_id]["start_time"] <= pos else -1

        while cur_id >= 0 and cur_id < len(subtitles):
            subtitle = subtitles[cur_id]

            if subtitle["start_time"] <= pos <= subtitle["end_time"]:
                return (cur_id, cur_id)
            elif subtitle["end_time"] < pos and direction < 0 or subtitle["start_time"] > pos and direction > 0:
                cur_id += direction * -1
                break

            cur_id += direction

        return (-1, min(max(0, cur_id), len(subtitles) - 1))


    def __subtitle_cmp(self, a, b):
        """Used to sort the subtitle list."""

        a_path, a_lang = a
        b_path, b_lang = b

        return (
            ( a_lang not in ("en", "eng") ) - ( b_lang not in ("en", "eng") ) or
            cmp(a_lang, b_lang) or
            cmp(a_path.lower(), b_path.lower())
        )


    def __update(self, pos):
        """Updates the GUI."""

        for subtitle_id, subtitles in enumerate(self.__subtitles):
            cur_id, subtitles["find_from"] = \
                self.__lookup(subtitles["data"], pos, subtitles["find_from"])
            subtitles["cur_id"] = cur_id

            if cur_id >= 0:
                subtitles = subtitles["data"][cur_id]

                if not subtitle_id:
                    self.__cur_text.setText(subtitles["text"].replace("\n", " "))

            self.__subtitle_widgets[subtitle_id].set_active_subtitle(cur_id)


class SubtitleWidget(QtGui.QTextEdit):
    """Displays a subtitle file."""

    __been_showed = False
    """Did this widget been showed."""


    __cur_subtitle = None
    """ID of the current subtitle."""

    __text_mappings = None
    """Maps subtitle id to its position in the QTextEdit."""

    __char_format_default = None
    """Default character format."""

    __char_format_active = None
    """Character format for currently active subtitle."""


    def __init__(self, subtitles, text_alignment, parent = None):
        QtGui.QTextEdit.__init__(self, parent)

        self.__cur_subtitle = -1
        self.__text_mappings = []

        self.__char_format_default = QtGui.QTextCharFormat()
        self.__char_format_default.setFontPointSize(10)
        self.__char_format_active = QtGui.QTextCharFormat()
        self.__char_format_active.setFontPointSize(10)
        self.__char_format_active.setFontWeight(QtGui.QFont.Bold)

        self.setReadOnly(True)
        self.document().setUndoRedoEnabled(False)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Filling up the widget -->
        cursor = self.textCursor()

        block_format = cursor.blockFormat()
        block_format.setAlignment(text_alignment)

        for subtitle in subtitles:
            if self.__text_mappings:
                cursor.insertBlock()
            self.__text_mappings.append(cursor.position())
            cursor.insertHtml(subtitle["text"].replace("\n", "<br>"))

        cursor.movePosition(QtGui.QTextCursor.Start)
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)

        cursor.setBlockFormat(block_format)
        cursor.setCharFormat(self.__char_format_default)
        # Filling up the widget <--

        self.setMaximumHeight(150)


    def showEvent(self, event):
        "QWidget's showEvent."""

        QtGui.QTextEdit.showEvent(self, event)

        # We have to scroll widget at first time it has been showed - it does
        # not scrolls until it has no X window.
        if not self.__been_showed:
            self.__been_showed = True
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().minimum())
            self.verticalScrollBar().setValue(self.verticalScrollBar().minimum())
            self.__scroll_to_active()



    def __scroll_to_active(self):
        """Scrolls to the current subtitle."""

        if self.__cur_subtitle < 0:
            return

        cursor = self.textCursor()
        cursor.setPosition(self.__text_mappings[self.__cur_subtitle])

        if self.__cur_subtitle < len(self.__text_mappings) - 1:
            cursor.setPosition(self.__text_mappings[self.__cur_subtitle + 1], QtGui.QTextCursor.KeepAnchor)
        else:
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

        cursor.setPosition(self.__text_mappings[self.__cur_subtitle])
        self.setTextCursor(cursor)


    def set_active_subtitle(self, id):
        """Sets current subtitle."""

        if self.__cur_subtitle == id:
            return

        if self.__cur_subtitle >= 0:
            self.__set_subtitle_format(self.__cur_subtitle, self.__char_format_default)

        if id >= 0:
            self.__set_subtitle_format(id, self.__char_format_active)

        self.__cur_subtitle = id
        self.__scroll_to_active()


    def __set_subtitle_format(self, id, format):
        """Sets a character format for a specified subtitle."""

        cursor = self.textCursor()
        cursor.setPosition(self.__text_mappings[id])

        if id != len(self.__text_mappings) - 1:
            cursor.setPosition(self.__text_mappings[id + 1], QtGui.QTextCursor.KeepAnchor)
        else:
            cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)

        cursor.setCharFormat(format)

