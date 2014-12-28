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
        self._row_count = None
        self._layout_horizont = False
        # stores all inserted items
        self._items = []
        self._col_width = {}
        self._row_height = {}

    def roundToGrid(self, pos, y=None):
        if y is not None:
            pos = QtCore.QPointF(pos, y)
        return pos

    def restrict_to_cols(self, cols):
        self._col_count = cols
        self._layout_horizont = False
        self._rebuild_layout()

    def restrict_to_rows(self, rows):
        self._row_count = rows
        self._layout_horizont = True
        self._rebuild_layout()

    def _rebuild_layout(self):
        if self._col_count is None and self._row_count is None:
            return

        if self._layout_horizont:
            self._col_count = math.ceil(len(self._items) / self._row_count)

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
        item = item_class(metadata={'#inputs': len(self._items) % 10 + 2})
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

        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)

        self.setInteractive(False)
        # self.setAcceptDrops(True)

        self._layout_horizont = False

        for _ in range(100):
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

    def wheelEvent(self, event):
        if self._layout_horizont:
            # create event with horizontal wheel orientation
            fake_evt = QtGui.QWheelEvent(
                event.pos(), event.globalPos(), event.delta(), event.buttons(),
                event.modifiers(), QtCore.Qt.Orientation.Horizontal)
            super().wheelEvent(fake_evt)
        else:
            super().wheelEvent(event)

    def get_full_size(self, resize_event):
        """Get size without scrollbars."""
        full_width = resize_event.size().width()
        if self.verticalScrollBar().isVisible():
            full_width += self.verticalScrollBar().width()

        full_height = resize_event.size().height()
        if self.horizontalScrollBar().isVisible():
            full_height += self.horizontalScrollBar().height()

        return QtCore.QSize(full_width, full_height)

    def resizeEvent(self, event):
        print(event.size().height(), self.size().height(),
              self.get_full_size(event).height())
        full_size = self.get_full_size(event)
        self._layout_horizont = full_size.width() > full_size.height()
        if self._layout_horizont:
            self.resizeEvent_horizontal(event)
        else:
            self.resizeEvent_vertical(event)

    def resizeEvent_horizontal(self, event):
        size_w, size_h = event.size().width(), event.size().height()

        full_height = self.get_full_size(event).height()
        scroll_height = full_height - self.horizontalScrollBar().height()

        # set number of rows
        rows = max(1, (full_height - 10) // 50)
        self.scene().restrict_to_rows(rows)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scene_w, scene_h = (self.scene().sceneRect().width(),
                            self.scene().sceneRect().height())

        def get_preferred_scale(height):
            return height / scene_h

        def fit_width(height):
            scale = get_preferred_scale(height)  # width / scene_w
            width = math.ceil(scene_w * scale)
            return width <= size_w

        # scrollbar recursion (not fit without, but fit with scrollbar)
        if not fit_width(full_height) and fit_width(scroll_height):
            # fit height --> largest scale, such that no scrollbar is shown
            new_scale = size_w / scene_w
        else:
            # fit width
            new_scale = get_preferred_scale(size_h)

        rel_scale = new_scale / self.getAbsoluteScale()
        self.scale(rel_scale, rel_scale)

    def resizeEvent_vertical(self, event):
        size_w, size_h = event.size().width(), event.size().height()

        full_width = self.get_full_size(event).width()
        scroll_width = full_width - self.verticalScrollBar().width()

        # set number of cols
        cols = max(1, (full_width - 10) // 50)
        self.scene().restrict_to_cols(cols)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        scene_w, scene_h = (self.scene().sceneRect().width(),
                            self.scene().sceneRect().height())

        def get_preferred_scale(width):
            return width / scene_w

        def fit_height(width):
            scale = get_preferred_scale(width)  # width / scene_w
            height = math.ceil(scene_h * scale)
            return height <= size_h

        # scrollbar recursion (not fit without, but fit with scrollbar)
        if not fit_height(full_width) and fit_height(scroll_width):
            # fit height --> largest scale, such that no scrollbar is shown
            new_scale = size_h / scene_h
        else:
            # fit width
            new_scale = get_preferred_scale(size_w)

        rel_scale = new_scale / self.getAbsoluteScale()
        self.scale(rel_scale, rel_scale)

