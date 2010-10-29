#!/usr/bin/env python

# PyQt tutorial 3


import logging
import sys
from PySide import QtCore, QtGui

for log in ("player", "cl", "mplayer"):
    LOG = logging.getLogger(log)
    handler = logging.StreamHandler(sys.stderr)
    LOG.addHandler(handler)
    LOG.setLevel(logging.DEBUG)

from mplayer.widget import MPlayerWidget

import signal
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
signal.siginterrupt(signal.SIGCHLD, False)
signal.siginterrupt(signal.SIGPIPE, False)
for i in xrange(1, 100):
    try:
        signal.siginterrupt(i, False)
    except:
        pass
app = QtGui.QApplication(sys.argv)

main_window = QtGui.QWidget()
#window = QtGui.QWidget()
#window.resize(200, 120)
#
#quit = QtGui.QPushButton("Quit", window)
#quit.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
#quit.setGeometry(10, 40, 180, 40)
#QtCore.QObject.connect(quit, QtCore.SIGNAL("clicked()"),
#                       app, QtCore.SLOT("quit()"))


mainLayout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
main_window.show()
window = MPlayerWidget()
mainLayout.addWidget(window)
button = QtGui.QToolButton()
button.clicked.connect(window.open)
mainLayout.addWidget(button)
window.show()

main_window.setLayout(mainLayout)
main_window.resize(640, 480)

sys.exit(app.exec_())
