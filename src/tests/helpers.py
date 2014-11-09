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
