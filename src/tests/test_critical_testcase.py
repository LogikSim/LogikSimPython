#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

import threading
from unittest import skip

import tests.helpers

from PySide import QtGui, QtCore


class ExcTimerObj(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.throw_exception)
        timer.setSingleShot(True)
        timer.start()
        self.fired = False

    def throw_exception(self, *args, **kargs):
        self.fired = True
        raise Exception("test")


class TestCriticalTest(tests.helpers.CriticalTestCase):

    @skip
    def test_uncaught_exception(self):
        app = QtGui.QApplication.instance()
        if app is None:
            app = QtGui.QApplication([])

        obj = ExcTimerObj()

        while not obj.fired:
            app.processEvents()

    @skip
    def test_uncaught_thread_exception(self):
        def throw_exception():
            raise Exception("test")
        thread = threading.Thread(target=throw_exception)
        thread.start()
        thread.join()

    @skip
    def test_unjoined_thread(self):
        def infinite_loop():
            while True:
                pass
        thread = threading.Thread(target=infinite_loop)
        thread.setDaemon(True)
        thread.start()
