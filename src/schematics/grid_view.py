#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines static view for a GridScene.
'''

from PySide import QtGui, QtCore


class GridView(QtGui.QGraphicsView):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def getAbsoluteScale(self):
        """Get absolute magnification scale of the scene."""
        return QtGui.QStyleOptionGraphicsItem.levelOfDetailFromTransform(
            self.viewportTransform())

    def resizeEvent(self, event):
        super().resizeEvent(event)
#        # workaround to immediately apply changes after maximize / restore
#        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
#        self.viewport().update()
