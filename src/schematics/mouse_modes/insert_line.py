#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines functionality when inserting lines.

It is based on the line_submode.
'''

from .line_submode.ready_to_insert import ReadyToInsertLineSubMode
from .line_submode.inserting import InsertingLineSubMode
from .modes_base import mouse_mode_filtered


class InsertLineMode(ReadyToInsertLineSubMode,
                     InsertingLineSubMode):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def mouse_enter(self):
        super().linesub_enter()
        self.setLinesubMode(ReadyToInsertLineSubMode)

    def mouse_leave(self):
        super().linesub_leave()
        # cleanup InsertLine
        self.setLineAnchorIndicator(None)
        self.setLinesubMode(None)

    @mouse_mode_filtered
    def abort_line_inserting(self):
        self.setLinesubMode(ReadyToInsertLineSubMode)
