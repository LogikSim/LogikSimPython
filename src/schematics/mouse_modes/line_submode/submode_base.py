#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Creates the inserting lines submode and its baseclass.
'''

import functools

from PySide import QtGui, QtCore

from ..modes_base import (GridViewMouseModeBase, mouse_mode_filtered)
import modes
import logicitems


LineSubModeBase, line_submode_filtered = modes.generate_mode_base(
    GridViewMouseModeBase, 'linesub')


class InsertLineSubModeBase(LineSubModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # store start position and new line items while inserting lines
        self._insert_line_start = None
        self._line_anchor_indicator = None
        # shape used for mouse collision tests while searching for
        # line anchors (must be float!)
        self._mouse_collision_line_radius = 5.
        self._mouse_collision_connector_radius = 10.
        # used to store anchor in mouseMoveEvent
        self._mouse_move_anchor = None

    def find_nearest_item_at_pos(self, pos, radius, filter_func=None):
        """
        returns nearest item in circle defined by x, y and diameter regarding
        it's origin using binary search

        bool filter(item, path) - function used to exclude items from search
            all valid positions should be contained in path, a QPainterPath
            in scene coordiantes
        """

        def get_items(radius):
            path = QtGui.QPainterPath()
            path.addEllipse(pos, radius, radius)
            items = self.items(path)
            if filter_func is not None:
                return list(filter(
                    functools.partial(filter_func,
                                      path=self.mapToScene(path)), items))
            else:
                return items

        r_min, r_max = 0, radius
        max_resolution = 0.5
        items, pivot = get_items(r_max), r_max
        while len(items) != 1 and (r_max - r_min) > max_resolution:
            pivot = r_min + (r_max - r_min) / 2.
            items = get_items(pivot)
            if len(items) == 0:
                r_min = pivot
            else:
                r_max = pivot
        if len(items) == 0 and pivot != r_max:
            items = get_items(r_max)
        if len(items) > 0:
            return items[0]

    def find_line_anchor_at_view_pos(self, pos, y=None):
        """
        returns nearest anchor to pos in scene coordinates or None

        pos - coordinate in view coordinates
        """

        def anchor_filter(item, path, radius):
            # line items
            if radius <= self._mouse_collision_line_radius and \
                    isinstance(item, logicitems.LineTree) and \
                    not item.is_temporary():
                return True
            # connector items
            elif radius <= self._mouse_collision_connector_radius and \
                    isinstance(item, logicitems.ConnectorItem) and \
                    item is not self._inserted_connector:
                return path.contains(item.anchorPoint())

        if y is not None:
            pos = QtCore.QPoint(pos, y)
        r_min, r_max = sorted((self._mouse_collision_line_radius,
                               self._mouse_collision_connector_radius))
        # first try to find item on smaller radius
        item = self.find_nearest_item_at_pos(
            pos, r_min, functools.partial(anchor_filter, radius=r_min))
        # if nothing found, try to find item on larger radius
        if item is None:
            item = self.find_nearest_item_at_pos(
                pos, r_max, functools.partial(anchor_filter, radius=r_max))
        # find nearest point on line (in scene coordinates)
        if isinstance(item, logicitems.LineTree):
            scene_pos = self.mapToScene(pos)
            return item.get_nearest_point(scene_pos)
        # return anchor point for connectors
        if isinstance(item, logicitems.ConnectorItem):
            return item.anchorPoint()

    def setLineAnchorIndicator(self, pos):
        """ pos - scene pos or None """
        if pos is None:
            if self._line_anchor_indicator is not None:
                self.scene().removeItem(self._line_anchor_indicator)
                self._line_anchor_indicator = None
        else:
            if self._line_anchor_indicator is None:
                # create new
                item = logicitems.LineAnchorIndicator(pos)
                self.scene().addItem(item)
                self._line_anchor_indicator = item
            else:
                # move existing
                self._line_anchor_indicator.setPos(pos)

    def _do_start_insert_lines(self, view_pos, anchor=None):
        # find anchor
        if anchor is None:
            anchor = self.find_line_anchor_at_view_pos(view_pos)
        start = self.mapToSceneGrid(view_pos) if anchor is None else anchor
        # store start position
        self._insert_line_start = start

    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        self._mouse_move_anchor = \
            self.find_line_anchor_at_view_pos(event.pos())
        self.setLineAnchorIndicator(self._mouse_move_anchor)
