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
from time import time, sleep


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

    def __init__(self, tracked_member="slot", result_fu=None):
        """
        :param tracked_member: Name of member to remember calls for
        """
        self.calls = []
        self.result_fu = result_fu
        setattr(self, tracked_member, self.__tracker)

    def __tracker(self, *args):
        if len(args) == 1:
            # Unpack for one
            self.calls.append(args[0])
        else:
            self.calls.append(args)

        if self.result_fu is not None:
            return self.result_fu(*args)

    def __call__(self):
        return self.calls


def try_repeatedly(fun, timeout=5, delay=0.05):
    """
    Repeatedly executes fun until it returns true or a timeout occurs.

    :param fun: Parameterless function to execute. Returns true on success.
    :param timeout: Time in seconds to try before returning unsuccessful
    :param delay: Delay between tries.
    :return True if successful once, false if not
    """
    start = time()
    while time() - start < timeout:
        if fun():
            return True
        sleep(delay)

    return False


def delayed_perform_on_modal(what, delay=10):
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
    app.processEvents()
    active = app.activeModalWidget()
    if active:
        what(active)
