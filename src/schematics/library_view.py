#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
The item list view is used to show all available logic elements.
'''

import math

from PySide import QtGui, QtCore

import schematics


class TestRect(QtGui.QGraphicsRectItem, QtGui.QGraphicsLayoutItem):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsRectItem.__init__(self, *args, **kargs)
        QtGui.QGraphicsLayoutItem.__init__(self, *args, **kargs)

        self.setRect(0, 0, 100, 100)
        self.setPen(QtGui.QPen(QtCore.Qt.black))
        self.setBrush(QtCore.Qt.white)

    def setGeometry(self, rect):
        self.setRect(rect)

    def sizeHint(self, which, constraint):
        return self.rect().size()


class ItemListScene(schematics.GridScene):
    def __init__(self, *args, **kargs):
        super(ItemListScene, self).__init__(*args, **kargs)
        self.set_grid_enabled(False)

        # top level widget is needed to layout all other items
        self._top_widget = QtGui.QGraphicsWidget()
        self.addItem(self._top_widget)
        # self._top_widget.setGeometry(0, 0, 250, 250)

        # number of columns visible
        self._col_count = None
        # stores all inserted items
        self._items = []

    def get_col_count(self, cols):
        return self._col_count

    def set_col_count(self, cols):
        assert isinstance(cols, int) and cols > 0
        self._col_count = cols
        self._rebuild_layout()

    def _rebuild_layout(self):
        if self._col_count is None:
            return

        layout = QtGui.QGraphicsGridLayout()
        self._top_widget.setLayout(layout)  # widget takes ownership of layout

        next_index = 0, 0
        for item in self._items:
            row, col = next_index
            layout.addItem(item, row, col)  # QtCore.Qt.AlignCenter)
            col += 1
            next_index = row + col // self._col_count, col % self._col_count

        self._top_widget.updateGeometry()
        self.setSceneRect(self.itemsBoundingRect())

    def add_item(self, item_class):
        item = item_class()
        self.addItem(item)
        self._items.append(item)
        self._rebuild_layout()


class LibraryView(schematics.GridView):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setScene(ItemListScene(self))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        for _ in range(10):
            self.scene().add_item(TestRect)

    def resizeEvent(self, event):
        size_w, size_h = event.size().width(), event.size().height()
        full_width = size_w
        if self.verticalScrollBar().isVisible():
            full_width += self.verticalScrollBar().width()
        scroll_width = full_width - self.verticalScrollBar().width()

        # set number of cols
        cols = max(1, full_width // 50)
        self.scene().set_col_count(cols)
        scene_w, scene_h = (self.scene().sceneRect().width(),
                            self.scene().sceneRect().height())

        def fit_height(width):
            scale = width / scene_w
            height = math.ceil(scene_h * scale)
            return height <= size_h

        # scrollbar recursion (not fit without, but fit with scrollbar)
        if not fit_height(full_width) and fit_height(scroll_width):
            # fit height --> largest scale, such that no scrollbar is shown
            new_scale = size_h / scene_h
        else:
            # fit width
            new_scale = size_w / scene_w

        rel_scale = new_scale / self.getAbsoluteScale()
        self.scale(rel_scale, rel_scale)
