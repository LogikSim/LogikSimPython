#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

'''
Contains helper functions that are helpful for creating unit-tests.
'''

from PySide import QtGui, QtCore
from PySide.QtTest import QTest

class CallTrack:
    """
    Class for tracking calls to its slot function.
    Primarily meant for testing signal and slot functionality.
    Usage:
    >>> log = CallTrack()
    >>> foo.my_signal.connect(log.slot)
    >>> # Do sth. to trigger signal
    >>> log() # Returns list of call tuple arguments (unpacked for 1 argument)
    """

    def __init__(self):
        self.calls = []

    def slot(self, *args):
        if len(args) == 1:
            # Unpack for one
            self.calls.append(args[0])
        else:
            self.calls.append(args)

    def __call__(self):
        return self.calls

def delayed_perform_on_modal(what, delay=100):
    """
    Meant to be used for interacting with modal dialogs during testing.

    Can be used to queue a call of the given what function before the dialog
    opens. After the given time expires that what function will be called
    with the currently active window.

    :param what: Function handed the active window
    :param delay: Delay before calling what with active modal widget in ms
    :return Created single shot timer
    """
    return QtCore.QTimer.singleShot(delay, lambda: perform_on_modal(what))

def perform_on_modal(what):
    """
    Meant to be used for interacting with modal dialogs during testing.

    If queued via QTimer.singleShot's before the dialog opens will
    pass the active window to the given "what" function. E.g. this
    allows dismissing a modal dialog even though it blocks normal
    test execution with it's own event loop.

    :param what: Function handed the active modal widget
    """
    app = QtGui.QApplication.instance()
    active = app.activeModalWidget()
    if active:
        what(active)
