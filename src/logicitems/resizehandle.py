#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
"""
Defines tool handles used to resize item while the item is selected.

They are made to be attached as a child to that item during selection.
"""

from PySide import QtGui, QtCore

from .itembase import ItemBase


class ResizeHandle(ItemBase):
    def __init__(self, parent, horizontal, resize_callback):
        """
        A handle used to resize parent.

        horizontal (bool) - is handle horizontal or vertical
        resize_callback (callable(handle, delta) -
            called with delta change as QPointF as suggestion to resize parent
            handle is the object itself.
        """
        super().__init__(parent)
        self._horizontal = horizontal
        self._resize_callback = resize_callback

        self.setFlag(QtGui.QGraphicsItem.ItemIgnoresTransformations)
        self.setAcceptHoverEvents(True)

        # shape definition
        width = 6
        self._handle_rect = QtCore.QRectF(-width/2, -width/2, width, width)
        self._bounding_rect = QtCore.QRectF(-width, -width, 2*width, 2*width)

        # mouse state
        self._press_handle_pos = None
        self._press_cursor_pos = None

    def mousePressEvent(self, event):
        # do not call parent, to prevent item deselection
        if event.button() is QtCore.Qt.LeftButton:
            self._press_handle_pos = self.pos()
            self._press_cursor_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            delta = event.scenePos() - self.mapToScene(self._press_cursor_pos)
            if self._horizontal:
                delta.setY(0)
            else:
                delta.setX(0)
            self._resize_callback(self, delta)

    def boundingRect(self):
        return self._bounding_rect

    def paint(self, painter, options, widget):
        painter.setBrush(self._selection_color_fill)
        painter.setPen(self._selection_color_line)

        painter.drawRect(self._handle_rect)

    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        if self._horizontal:
            self.setCursor(QtCore.Qt.SizeHorCursor)
        else:
            self.setCursor(QtCore.Qt.SizeVerCursor)
