#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
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

    """ while new lines are inserted """

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
        # contains merged lines that can be removed when inserting lines
        # stored in _inserted_lines
        self._merged_line_trees = []

    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        # prevent circular imports
        from .ready_to_insert import ReadyToInsertLineSubMode

        # left button
        if event.button() is QtCore.Qt.LeftButton:
            anchor = self.find_line_anchor_at_view_pos(event.pos())
            self._commit_inserted_lines()
            # if there is no anchor, immediately start inserting new lines
            if anchor is None:
                self._do_start_insert_lines(event.pos(), anchor)
            else:  # otherwise stop for now
                self.setLinesubMode(ReadyToInsertLineSubMode)
        # right button
        elif event.button() is QtCore.Qt.RightButton:
            self.setLinesubMode(ReadyToInsertLineSubMode)

    @line_submode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        gpos = self.mapToSceneGrid(event.pos())
        anchor = self._mouse_move_anchor
        end = gpos if anchor is None else anchor
        start = self._insert_line_start

        self._insert_line_start_end = (start, end)
        self._update_line_timer.start()

    def _get_linetrees_at_point(self, scene_point):
        """ get line trees at given scene point as list """
        return [item for item in self.scene().items(scene_point)
                if isinstance(item, logicitems.LineTree)]

    @line_submode_filtered
    @timeit
    def do_update_line(self):
        start, end = self._insert_line_start_end

        #
        # new graph based search
        #
        to_grid = self.scene().to_grid
        to_scene_point = self.scene().to_scene_point

        p_start = to_grid(start.x()), to_grid(start.y())
        p_end = to_grid(end.x()), to_grid(end.y())

        # compare to last call
        if (p_start, p_end) == self._insert_line_start_end_last:
            return
        self._insert_line_start_end_last = p_start, p_end

        # remove old results
        self._undo_temp_insert_lines()

        # get rectangle with one space free around the scene
        bound_rect = self.scene().itemsBoundingRect()
        r_left = to_grid(min(bound_rect.left(), start.x(), end.x())) - 1
        r_top = to_grid(min(bound_rect.top(), start.y(), end.y())) - 1
        r_right = to_grid(max(bound_rect.right(), start.x(), end.x())) + 2
        r_bottom = to_grid(max(bound_rect.bottom(),
                               start.y(), end.y())) + 2

        # save line trees at endpoints
        tree_start = self._get_linetrees_at_point(start)
        tree_end = self._get_linetrees_at_point(end)

        # can only merge two trees if start == end
        if len(tree_start) > 1 or len(tree_end) > 1:
            if (p_start == p_end):
                # pick one, as they are the same
                endpoint_trees = tree_start
            else:
                return
        else:
            if (p_start == p_end):
                return
            endpoint_trees = [tree_start[0] if len(tree_start) > 0 else None,
                              tree_end[0] if len(tree_end) > 0 else None]

        # if both trees are the same --> line already exists --> nothing todo
        if endpoint_trees[0] is endpoint_trees[1] is not None:
            return

        get_obj_at_point = GetHightowerObjectAtPoint(self.scene(),
                                                     p_start, p_end,
                                                     tree_start, tree_end,
                                                     endpoint_trees,
                                                     self._line_anchor_indicator)

        # We only want to search for a limited amount of time
        time_limited_get_obj_at_point = time_limited(get_obj_at_point, self._max_line_search_time)

        search_rect = ((r_left, r_top), (r_right, r_bottom))

        try:
            res = hightower.hightower_line_search(p_start, p_end,
                                                  time_limited_get_obj_at_point,
                                                  search_rect,
                                                  do_second_refinement=False)
        except TimeReached:
            res = None

        if res is None:
            return

        # remove parts of the path that are already part of
        # adjacent line trees of the end points

        def iter_line(line):
            """
            Iterate through all points on the line, except endpoint
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

        def extract_new_path(path, line_tree):
            """
            Returns new path branching from existing line_tree.

            Go through the path from the beginning and removes segments
            until they are not anymore part of the line tree
            """
            res = path[:]
            if line_tree is not None:
                last_index = 0
                last_point = path[0]

                def helper():
                    nonlocal last_index, last_point
                    for i, line in enumerate(zip(path, path[1:])):
                        points = list(iter_line(line))
                        for segment in zip(points, points[1:]):
                            segment_line = QtCore.QLineF(
                                to_scene_point(segment[0]),
                                to_scene_point(segment[1]))
                            if line_tree.contains_line(segment_line):
                                last_index = i
                                last_point = segment[1]
                            else:
                                return

                helper()
                res[last_index] = last_point
                del res[:last_index]
            return res

        res = extract_new_path(res, endpoint_trees[0])
        res = extract_new_path(list(reversed(res)), endpoint_trees[1])

        # create line tree from result
        path = list(map(to_scene_point, res))
        l_tree = logicitems.LineTree(path)

        # merge start and end lines
        merged_trees = []
        for tree in endpoint_trees:
            if tree is not None:
                l_tree.merge_tree(tree)
                merged_trees.append(tree)

        # temporarily add them to scene
        self._do_temp_insert_lines(l_tree, merged_trees)

    def _do_temp_insert_lines(self, l_tree, merged_trees):
        """ insert given line tree and remove merged trees """
        self.scene().addItem(l_tree)
        # we do not delete merged_trees, otherwise line
        # indicator is not drawn any more

        self._inserted_lines = l_tree
        self._merged_line_trees = merged_trees

    def _undo_temp_insert_lines(self):
        """ undo previously inserted lines and restore merged trees """
        if self._inserted_lines is not None:
            self.scene().removeItem(self._inserted_lines)

        self._inserted_lines = None
        self._merged_line_trees = []

    def _commit_inserted_lines(self):
        """ insert lines currently drawn persistently """
        if self._inserted_lines is None:
            return

        # go back to neutral state, before inserting
        inserted_lines = self._inserted_lines
        merged_trees = self._merged_line_trees
        self._undo_temp_insert_lines()

        def do():
            self._do_temp_insert_lines(inserted_lines, merged_trees)
            for linetree in merged_trees:
                self.scene().removeItem(linetree)
            self._inserted_lines = None
            self._merged_line_trees = []
            self._insert_line_start_end_last = None

        def undo():
            self._inserted_lines = inserted_lines
            self._merged_line_trees = merged_trees
            self._undo_temp_insert_lines()
            for linetree in merged_trees:
                self.scene().addItem(linetree)

        self.scene().actions.execute(
            do, undo, "insert lines"
        )

    def linesub_leave(self):
        super().linesub_leave()
        # cleanup InsertingLine
        self._undo_temp_insert_lines()


class GetHightowerObjectAtPoint:
    """
    Function object which returns which kind of hightower object can be found at the given point.
    Meant to be used while inserting a line.
    """
    def __init__(self, scene, p_start, p_end, tree_start, tree_end, endpoint_trees, line_anchor_indicator):
        """
        Creates a new callable function object.

        :param scene: Scene operation is taking place in
        :param p_start: Starting point of the line segment being inserted in grid coordinates
        :param p_end: Ending point of the line segment being inserted in grid coordinates
        :param tree_start: Line-trees at p_start location (if any)
        :param tree_end: Line-trees at p_end location (if any)
        :param endpoint_trees: Unique line-trees at p_start and p_end
        :param line_anchor_indicator: Line anchor indicator singleton
        """
        self.p_start = p_start
        self.p_end = p_end
        self.tree_start = tree_start
        self.tree_end = tree_end
        self.endpoint_trees = endpoint_trees
        self.scene = scene
        self.line_anchor_indicator = line_anchor_indicator

    def _is_self_line_edge(self, point, item):
        """
        Must not have cycles so we can not allow overlapping the edges
        of the trees the line we are drawing belongs to. A special case
        is if what we are drawing is fully contained in the tree in which
        case overlapping edges is just fine.

        :param point: Point in grid coordinates currently being checked.
        :param item: Item to check for
        :return: True if self line-edge we want to filter. False otherwise.
        """
        if item in self.tree_start and point != self.p_start:
            start_to_point_line = QtCore.QLineF(self.scene.to_scene_point(self.p_start),
                                                self.scene.to_scene_point(point))

            return not self.tree_start[0].contains_line(start_to_point_line)

        if item in self.tree_end and point != self.p_end:
            point_to_end_line = QtCore.QLineF(self.scene.to_scene_point(point),
                                              self.scene.to_scene_point(self.p_end))

            return not self.tree_end[0].contains_line(point_to_end_line)

        return False

    def __call__(self, point):
        """
        Returns which kind of hightower object can be found at the given point.
        Meant to be used while inserting a line.

        :param point: Point to check in grid coordinates.
        :return: hightower object found at position.
        """

        scene_point = self.scene.to_scene_point(point)
        items = self.scene.items(scene_point)
        found_passable_line = False
        found_line_edge = False

        for item in items:
            if item is self.line_anchor_indicator:
                continue
            elif isinstance(item, logicitems.ConnectorItem) and point in (self.p_start, self.p_end):
                continue
            elif isinstance(item, logicitems.LineTree):
                if item in self.endpoint_trees:
                    if self._is_self_line_edge(point, item):
                        return hightower.Solid
                elif item.is_edge(scene_point):
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
