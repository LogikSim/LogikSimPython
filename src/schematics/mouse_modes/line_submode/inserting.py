#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
"""
Defines submode functionality when inserting lines
"""

from PySide import QtCore

from .submode_base import InsertLineSubModeBase, line_submode_filtered
import logicitems
from helper.timeit_mod import timeit
from helper.time_limited import time_limited, TimeReached
import algorithms.hightower as hightower


class InsertingLineSubMode(InsertLineSubModeBase):

    # time budget to search for lines
    _max_line_search_time = 0.3
    """While new lines are inserted."""

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        # use timer to only process most recent event
        self._update_line_timer = QtCore.QTimer()
        self._update_line_timer.timeout.connect(self.do_update_line)
        self._update_line_timer.setSingleShot(True)
        self._insert_line_start_end = None
        # stores two tuples with start and end coordinates as used in
        # mouseMoveEvent
        self._insert_line_start_end_last = None
        # stores temporarily inserted line route object
        self._temp_line_route = None

    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # prevent circular imports
        from .ready_to_insert import ReadyToInsertLineSubMode

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            self.update_line_anchor_indicator(event.pos())
            self.commit_inserted_temp_line()
            # if there is no anchor, immediately start inserting new lines
            if self._line_anchor is None:
                self._do_start_insert_lines(event.pos())
            else:  # otherwise stop for now
                self.setLinesubMode(ReadyToInsertLineSubMode)
        # right button
        elif event.button() is QtCore.Qt.RightButton:
            self.setLinesubMode(ReadyToInsertLineSubMode)

    @line_submode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        end = self.get_line_insertion_point(event.pos())
        start = self._insert_line_start

        self._insert_line_start_end = (start, end)
        self._update_line_timer.start()

    @line_submode_filtered
    @timeit
    def do_update_line(self):
        start, end = self._insert_line_start_end

        p_start = self.scene().to_grid(start)
        p_end = self.scene().to_grid(end)

        # compare to last call
        if (p_start, p_end) == self._insert_line_start_end_last:
            return
        self._insert_line_start_end_last = p_start, p_end

        # remove old route
        if self._temp_line_route is not None:
            self._temp_line_route.undo_insert()
            self._temp_line_route = None

        # create new route
        line_route = LineRouteBetweenPoints(self.scene(), start, end,
                                            self._max_line_search_time)
        try:
            line_route.route()
        except RouteNotFoundException:
            return

        # temporarily add route to scene
        line_route.do_temp_insert()
        self._temp_line_route = line_route

    def commit_inserted_temp_line(self):
        """Finalize inserted routed line."""
        if self._temp_line_route is None:
            return

        temp_line_route = self._temp_line_route
        self._temp_line_route = None

        def do():
            temp_line_route.do_insert()

        def undo():
            temp_line_route.undo_insert()

        self.scene().actions.execute(
            do, undo, "insert lines"
        )

    def linesub_leave(self):
        super().linesub_leave()
        # cleanup InsertingLine
        if self._temp_line_route is not None:
            self._temp_line_route.undo_insert()
            self._temp_line_route = None


class RouteNotFoundException(Exception):
    """No route can be found."""
    def __init__(self):
        super().__init__("Route not Found")


class EndpointTrees:
    """Store existing line-trees at the endpoints for routing."""
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __iter__(self):
        return iter((self.start, self.end))


class LineRouteBetweenPoints:
    def __init__(self, scene, start, end, max_line_search_time=None):
        self.scene = scene
        self.start = start
        self.end = end
        self.max_line_search_time = max_line_search_time

        # store start and end in grid coordinates
        self.p_start = self.scene.to_grid(start)
        self.p_end = self.scene.to_grid(end)

        # route result
        self._is_routed = False
        self._is_temp_inserted = False
        self._is_inserted = False  # when this is True, temp is also True
        self._new_line_tree = None
        # contains merged lines that can be removed when inserting new route
        self._merged_line_trees = []

    def _get_search_rect(self):
        # get rectangle with one space free around the scene
        bound_rect = self.scene.itemsBoundingRect()
        r_left, r_top = self.scene.to_grid(QtCore.QPointF(
            min(bound_rect.left(), self.start.x(), self.end.x()) - 1,
            min(bound_rect.top(), self.start.y(), self.end.y()) - 1))
        r_right, r_bottom = self.scene.to_grid(QtCore.QPointF(
            max(bound_rect.right(), self.start.x(), self.end.x()) + 2,
            max(bound_rect.bottom(), self.start.y(), self.end.y()) + 2))
        return ((r_left, r_top), (r_right, r_bottom))

    def _get_linetrees_at_point(self, scene_point):
        """Get line trees at given scene point as list."""
        return [item for item in self.scene.items(scene_point)
                if isinstance(item, logicitems.LineTree)]

    def _get_endpoint_trees(self):
        # save line trees at endpoints
        tree_start = self._get_linetrees_at_point(self.start)
        tree_end = self._get_linetrees_at_point(self.end)

        # can only merge two trees if start == end
        if len(tree_start) > 1 or len(tree_end) > 1:
            if self.p_start != self.p_end:
                raise RouteNotFoundException()
            # pick one, as they are the same
            assert len(tree_start) == 2
            endpoint_trees = EndpointTrees(*tree_start)
        else:
            if self.p_start == self.p_end:  # nothing todo
                raise RouteNotFoundException()
            endpoint_trees = EndpointTrees(
                tree_start[0] if len(tree_start) > 0 else None,
                tree_end[0] if len(tree_end) > 0 else None)
            # both the same? --> line already exists --> nothing todo
            if endpoint_trees.start is endpoint_trees.end is not None:
                raise RouteNotFoundException()

        return endpoint_trees

    def route(self):
        """
        Try to find route between given points.

        :raises RouteNotFoundException: when no route can be found.
        """
        assert not self._is_routed

        endpoint_trees = self._get_endpoint_trees()
        get_obj_at_point = GetHightowerObjectAtPoint(
            self.scene, self.p_start, self.p_end, endpoint_trees)
        # We only want to search for a limited amount of time
        time_limited_get_obj_at_point = time_limited(
            get_obj_at_point, self.max_line_search_time)
        search_rect = self._get_search_rect()

        try:
            res = hightower.hightower_line_search(
                self.p_start, self.p_end, time_limited_get_obj_at_point,
                search_rect, do_second_refinement=False)
        except TimeReached:
            raise RouteNotFoundException()
        if res is None:
            raise RouteNotFoundException()

        # remove parts of the path that are already part of
        #     adjacent line trees of the end points
        res = self._extract_new_path(res, endpoint_trees.start)
        res = self._extract_new_path(list(reversed(res)), endpoint_trees.end)

        # create line tree from result
        path = list(map(self.scene.to_scene_point, res))
        metadata = logicitems.LineTree.metadata_from_path(path)
        l_tree = self.scene.registry().instantiate_frontend_item(
            backend_guid=logicitems.LineTree.GUI_GUID(),
            additional_metadata=metadata)

        # merge start and end lines
        merged_trees = []
        for tree in endpoint_trees:
            if tree is not None:
                l_tree.merge_tree(tree)
                merged_trees.append(tree)

        # check numer of inputs
        if l_tree.numer_of_driving_inputs(self.scene) > 1:
            raise RouteNotFoundException()

        # store result
        self._is_routed = True
        self._new_line_tree = l_tree
        self._merged_line_trees = merged_trees

    def set_endpoint_anchors(self, value):
        """Set or unsets anchors for Connectors endpoints."""
        for item in self.scene.items(self.start) + self.scene.items(self.end):
            if isinstance(item, logicitems.ConnectorItem):
                item.set_anchored(value)

    def do_temp_insert(self):
        """
        Add new route to scene as temporary object.

        This is useful, when e.g. the old lines are still needed
        to draw line anchor indicators. Also in this mode no
        existing line is removed.
        """
        if self._is_inserted:
            self.undo_insert()
        if not self._is_routed or self._is_temp_inserted:  # nothing todo
            return

        # set endpoint connectors as anchored
        self.set_endpoint_anchors(True)

        # add routed tree
        self._new_line_tree.set_temporary(True)
        self.scene.addItem(self._new_line_tree)
        # we do not delete merged_trees here, otherwise line
        #     indicator is not drawn any more
        self._is_temp_inserted = True

    def do_insert(self):
        """ Add new route persistently. """
        if not self._is_routed or self._is_inserted:  # nothing todo
            return

        if not self._is_temp_inserted:
            self.do_temp_insert()

        # unset anchor on endpoint connectors
        self.set_endpoint_anchors(False)

        # remove merged line trees
        for linetree in self._merged_line_trees:
            self.scene.removeItem(linetree)
        # unset temporary flag
        self._new_line_tree.set_temporary(False)

        self._is_inserted = True

    def undo_insert(self):
        """ Undo previously inserted route (temporary or persistent). """
        if not self._is_routed:  # nothing todo
            return

        if self._is_inserted:
            # add merged line trees
            for linetree in self._merged_line_trees:
                self.scene.addItem(linetree)
            self._is_inserted = False
        if self._is_temp_inserted:
            # remove routed tree
            self.scene.removeItem(self._new_line_tree)
            self._is_temp_inserted = False
            # unset anchor
            self.set_endpoint_anchors(False)

    @staticmethod
    def _iter_line(line):
        """
        Iterate through all points on the line, except endpoint

        :param line: line given as tuple ((x1, y1), (x2, y2)) of int
        :result: iterator yielding all point (u,v) between p1 and p2.
            including both edges
        """
        # define two way range, including edges
        def fullrange2w(a, b):
            return range(a, b + (-1 if a > b else 1), -1 if a > b else 1)

        if line[0][1] == line[1][1]:
            for x in fullrange2w(line[0][0], line[1][0]):
                yield (x, line[0][1])
        else:
            for y in fullrange2w(line[0][1], line[1][1]):
                yield (line[0][0], y)

    def _extract_new_path(self, path, line_tree):
        """
        Returns new path branching from existing line_tree.

        Go through the path from the beginning and removes segments
        until they are not anymore part of the line tree.
        """
        res = path[:]
        if line_tree is not None:
            last_index = 0
            last_point = path[0]

            def helper():
                nonlocal last_index, last_point
                for i, line in enumerate(zip(path, path[1:])):
                    points = list(self._iter_line(line))
                    for segment in zip(points, points[1:]):
                        segment_line = QtCore.QLineF(
                            self.scene.to_scene_point(segment[0]),
                            self.scene.to_scene_point(segment[1]))
                        if line_tree.contains_line(segment_line):
                            last_index = i
                            last_point = segment[1]
                        else:
                            return

            helper()
            res[last_index] = last_point
            del res[:last_index]
        return res


class GetHightowerObjectAtPoint:
    """
    Function object which returns which kind of hightower object can be found
    at the given point. Meant to be used while inserting a line.
    """
    def __init__(self, scene, p_start, p_end, endpoint_trees):
        """
        Creates a new callable function object.

        :param scene: Scene operation is taking place in
        :param p_start: Starting point of the line segment being inserted in
            grid coordinates as tuple (int, int).
        :param p_end: Ending point of the line segment being inserted in
            grid coordinates as tuple (int, int).
        :param endpoint_trees: line-trees at p_start and p_end given
            as EndpointTrees object.
        """
        self.scene = scene
        self.p_start = p_start
        self.p_end = p_end
        self.endpoint_trees = endpoint_trees

    def _is_start_of_linetree(self, point, item):
        """
        Is this point the start of a linetree?

        Must not have cycles, so we have to consider existing line-trees.
        Otherwise it can happen that the found path overlapping the edges
        of the endpoint trees. Furthermore we don't want to categorically
        exclude them for router, since routing over an edge from A to B:
        (<------A------>     B)  would not be possible in this simple case.
        That is why we ignore the lines and first edges

        :param point: Point in grid coordinates currently being checked.
        :param item: Item to check for
        :return: true in case it can be ignored for routing
        """
        if item in self.endpoint_trees:
            p_pivot = {self.endpoint_trees.start: self.p_start,
                       self.endpoint_trees.end: self.p_end}[item]
            pivot_to_point_line = QtCore.QLineF(
                self.scene.to_scene_point(p_pivot),
                self.scene.to_scene_point(point))
            return item.contains_line(pivot_to_point_line)
        return False

    def __call__(self, point):
        """
        Returns which kind of hightower object can be found at the given point.
        Meant to be used while inserting a line.

        :param point: Point to check in grid coordinates as tuple (int, int).
        :return: hightower object found at position.
        """

        scene_point = self.scene.to_scene_point(point)
        items = self.scene.items(scene_point)
        found_passable_line = False
        found_line_edge = False

        for item in items:
            if isinstance(item, logicitems.LineAnchorIndicator):
                continue
            if isinstance(item, logicitems.LineEdgeIndicator):
                continue
            elif isinstance(item, logicitems.ConnectorItem) and \
                    item.endPoint() == scene_point and \
                    point in (self.p_start, self.p_end):
                continue
            elif isinstance(item, logicitems.LineTree):
                if self._is_start_of_linetree(point, item):
                    continue
                if item.is_edge(scene_point):
                    found_line_edge = True
                else:
                    found_passable_line = True
                continue

            return hightower.Solid

        if found_line_edge:
            return hightower.LineEdge
        elif found_passable_line:
            return hightower.PassableLine

        return None
