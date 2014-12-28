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
import collections

from PySide import QtGui, QtCore

import schematics
from symbols import AndItem
from logicitems import LogicItem


class ItemListScene(schematics.GridScene):
    # tile size of preview in grid points
    _tile_size = 5
    # tile margin in grid points
    _tile_margin = 0.5
    # tile spacing in grid points
    _tile_spacing = 1

    def __init__(self, *args, **kargs):
        super(ItemListScene, self).__init__(*args, **kargs)

        self.set_grid_enabled(False)

        # top level widget is needed to layout all other items
        self._top_widget = QtGui.QGraphicsWidget()
        self.addItem(self._top_widget)
        margin = self.get_grid_spacing() * self._tile_margin
        self._top_widget.setContentsMargins(*[margin] * 4)

        # number of columns visible
        self._col_count = None
        # stores all inserted items
        self._items = []
        self._col_width = {}
        self._row_height = {}

    def roundToGrid(self, pos, y=None):
        if y is not None:
            pos = QtCore.QPointF(pos, y)
        return pos

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
        grid = self.get_grid_spacing()
        layout.setSpacing(grid * self._tile_spacing)

        self._col_width = collections.defaultdict(int)
        self._row_height = collections.defaultdict(int)

        next_index = 0, 0
        for item in self._items:
            row, col = next_index

            size = item.sizeHint(QtCore.Qt.MinimumSize, QtCore.QSizeF(0, 0))
            self._col_width[col] = max(self._col_width[col],
                                       size.width() / grid)
            self._row_height[row] = max(self._row_height[row],
                                        size.height() / grid)
            layout.addItem(item, row, col, QtCore.Qt.AlignCenter)

            col += 1
            next_index = row + col // self._col_count, col % self._col_count

        self._top_widget.updateGeometry()
        self.setSceneRect(QtCore.QRectF(self._top_widget.pos(),
                                        self._top_widget.size()))

    def add_item(self, item_class):
        # add item to scene
        item = item_class(metadata={'#inputs': len(self._items) + 2})
        item.set_temporary(True)
        self.addItem(item)
        self._items.append(item)

        # scale item to tile
        rect = item.boundingRect()
        tile_size = self.get_grid_spacing() * self._tile_size
        scale = min(1, tile_size / rect.width(), tile_size / rect.height())
        item.setScale(scale)

        self._rebuild_layout()

    def get_item_at_pos(self, pos):
        """Returns item in tile or None at given position."""
        gpos = pos / self.get_grid_spacing()

        def get_tile_index(grid_coord, size_list):
            tile_start = self._tile_margin
            for index in size_list:
                if tile_start <= grid_coord <= tile_start + size_list[index]:
                    return index
                tile_start += size_list[index] + self._tile_spacing

        row = get_tile_index(gpos.y(), self._row_height)
        col = get_tile_index(gpos.x(), self._col_width)

        if row is None or col is None:
            return None
        try:
            return self._items[row * self._col_count + col]
        except IndexError:
            return None


class LibraryView(schematics.GridView):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setScene(ItemListScene(self))

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)

        self.setInteractive(False)
        # self.setAcceptDrops(True)

        for _ in range(10):
            self.scene().add_item(AndItem)  # TestRect)

    def mousePressEvent(self, event):
        # get item in tile
        item = self.scene().get_item_at_pos(self.mapToScene(event.pos()))
        if item is None:
            return

        mimeData = QtCore.QMimeData()
        mimeData.setData('application/x-components', str(item._input_count))

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.exec_()

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
