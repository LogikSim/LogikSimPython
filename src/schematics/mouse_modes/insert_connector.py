#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines functionality when inserting connectors.
'''

from PySide import QtCore

from .modes_base import GridViewMouseModeBase, mouse_mode_filtered
import logicitems


class InsertConnectorMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # stores start position and connector while inserting connectors
        self._insert_connector_start = None
        self._inserted_connector = None

    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            self._insert_connector_start = gpos
            self._inserted_connector = logicitems.ConnectorItem(gpos, gpos)
            self.scene().addItem(self._inserted_connector)

    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        # left button
        if event.buttons() & QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            self._inserted_connector.setLine(self._insert_connector_start,
                                             gpos)

    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            # cleanup null size connectors
            if not self._inserted_connector.is_valid():
                self.scene().removeItem(self._inserted_connector)
            self._inserted_connector = None
