#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Connectors of Logic Items where lines be attached.
'''

from PySide import QtGui, QtCore


class SmoothGrahpicsLineItem(QtGui.QGraphicsLineItem):
    def shouldAntialias(self, painter):
        # enable antialiasing for tilted lines
        inv_transform, invertable = painter.worldTransform().inverted()
        if invertable:
            angle = inv_transform.map(self.line()).angle()
            straight = abs(angle % 90 - 45) == 45
            return not straight
        else:
            return True

    def isHorizontalOrVertical(self):
        vline = self.line().p2() - self.line().p1()
        return vline.x() == 0 or vline.y() == 0

    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing,
                              self.shouldAntialias(painter))
        QtGui.QGraphicsLineItem.paint(self, painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)


class ConnectorItem(SmoothGrahpicsLineItem):
    def __init__(self, *args, **kargs):
        SmoothGrahpicsLineItem.__init__(self, *args, **kargs)
        self.setPen(QtGui.QPen(QtCore.Qt.black))

    def anchorPoint(self):
        """
        returns position where lines can connect to
        """
        return self.line().p2()

    def setLine(self, line):
        """
        line defines: start, anchor
        """
        SmoothGrahpicsLineItem.setLine(self, line)
