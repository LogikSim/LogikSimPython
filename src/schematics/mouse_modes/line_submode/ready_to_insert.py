#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines submode functionality when ready to insert lines.
'''

from .submode_base import InsertLineSubModeBase, line_submode_filtered

from PySide import QtCore


class ReadyToInsertLineSubMode(InsertLineSubModeBase):
    """ ready to insert line """
    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            self._do_start_insert_lines(event.pos())
            
            # prevent circular imports
            from .inserting import InsertingLineSubMode
            self.setLinesubMode(InsertingLineSubMode)

