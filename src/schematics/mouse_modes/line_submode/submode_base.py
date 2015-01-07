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

from PySide import QtGui

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
        self._line_anchor = None
        # shape used for mouse collision tests while searching for
        # line anchors (must be float!)
        self._mouse_collision_line_radius = 5.
        self._mouse_collision_connector_radius = 10.

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

    def get_line_anchor_at_view_pos(self, pos):
        """
        returns nearest anchor to pos in scene coordinates or None

        :param pos: coordinate in view coordinates
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

        r_min, r_max = sorted((self._mouse_collision_line_radius,
                               self._mouse_collision_connector_radius))
        # first try to find item on smaller radius
        item = self.find_nearest_item_at_pos(
            pos, r_min, functools.partial(anchor_filter, radius=r_min))
        # if nothing found, try to find item on larger radius
        if item is None:
            item = self.find_nearest_item_at_pos(
                pos, r_max, functools.partial(anchor_filter, radius=r_max))
        anchor_pos = None
        if isinstance(item, logicitems.LineTree):
            # find nearest point on line (in scene coordinates)
            scene_pos = self.mapToScene(pos)
            anchor_pos = item.get_nearest_point(scene_pos)
        elif isinstance(item, logicitems.ConnectorItem):
            # return anchor point for connectors
            anchor_pos = item.anchorPoint()
        if anchor_pos is not None:
            return logicitems.LineAnchorIndicator(anchor_pos, item)

    def update_line_anchor_indicator(self, pos):
        """ pos - scene pos or None """
        # delete old
        if self._line_anchor is not None:
            self.scene().removeItem(self._line_anchor)
            self._line_anchor = None
        # create new
        if pos is not None:
            item = self.get_line_anchor_at_view_pos(pos)
            if item is not None:
                self.scene().addItem(item)
                self._line_anchor = item

    def get_line_insertion_point(self, view_pos):
        """
        Get position where lines should be inserted.

        Either returns anchor point or given position.

        :param pos: Requested mouse pos for insertion in view coordinates.
        """
        if self._line_anchor is not None:
            return self._line_anchor.get_start_pos()
        else:
            return self.mapToSceneGrid(view_pos)

    def _do_start_insert_lines(self, view_pos, anchor=None):
        # TODO: update anchor?
        self._insert_line_start = self.get_line_insertion_point(view_pos)

    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.update_line_anchor_indicator(event.pos())
