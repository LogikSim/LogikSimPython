#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines submode functionality when inserting lines
'''

import time

from .submode_base import InsertLineSubModeBase, line_submode_filtered
import logicitems
from helper.timeit_mod import timeit
import algorithms.hightower as hightower

from PySide import QtCore


class InsertingLineSubMode(InsertLineSubModeBase):
    """ while new lines are inserted """
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        
        self._update_line_timer = QtCore.QTimer()
        self._update_line_timer.timeout.connect(self.do_update_line)
        self._update_line_timer.setSingleShot(True)
        self._insert_line_start_end = None
        # stores two tuples with start and end coordinates as used in
        # mouseMoveEvent
        self._insert_line_start_end_last = None
    
    def _do_end_insert_lines(self):
        """ insert lines """
        if self._inserted_lines is not None:
            # remove already merged lines at endpoints
            self.scene().removeItem(self._inserted_lines)
            for point in self._insert_line_start_end:
                line = self._get_line_at_point(point)
                if line is not None:
                    self.scene().removeItem(line)
            self.scene().addItem(self._inserted_lines)
        
        self._inserted_lines = None
        self._insert_line_start_end_last = None
    
    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # prevent circular imports
        from .ready_to_insert import ReadyToInsertLineSubMode
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            anchor = self.find_line_anchor_at_view_pos(event.pos())
            self._do_end_insert_lines()
            if anchor is None:
                self._do_start_insert_lines(event.pos(), anchor)
            else:
                self.setLinesubMode(ReadyToInsertLineSubMode)
        # right button
        elif event.button() is QtCore.Qt.RightButton:
            self.setLinesubMode(ReadyToInsertLineSubMode)
    
    @line_submode_filtered
    def mouseMoveEvent(self, event):
        #QtGui.QApplication.instance().processEvents()
        
        super().mouseMoveEvent(event)
        
        gpos = self.mapToSceneGrid(event.pos())
        anchor = self._mouse_move_anchor
        end = gpos if anchor is None else anchor
        start = self._insert_line_start
        
        self._insert_line_start_end = (start, end)
        self._update_line_timer.start()
    
    
    def _get_line_at_point(self, scene_point):
        """ get line at given scene point """
        items = self.scene().items(scene_point)
        for item in items:
            if isinstance(item, logicitems.LineTree):
                # we assume that there is only one line at each point
                return item
    
    @timeit
    def do_update_line(self):
        start, end = self._insert_line_start_end
        
        #
        # new graph based search
        #
        
        spacing = self.scene().get_grid_spacing()
        def to_grid(scene_point):
            """ Converts points in self.scene to grid points used here.
            
            The functions always rounds down """
            return int(scene_point / spacing)
        def to_scene(grid_point):
            """ Converts grid points used here to points in self.scene """
            return grid_point * spacing
        
        def to_scene_point(grid_point):
            """ Converts grid tuple to QPointF in scene coordinates """
            return QtCore.QPointF(*map(to_scene, grid_point))
        
        p_start = to_grid(start.x()), to_grid(start.y())
        p_end = to_grid(end.x()), to_grid(end.y())
        
        # compare to last call
        if (p_start, p_end) == self._insert_line_start_end_last:
            return
        self._insert_line_start_end_last = p_start, p_end
        
        # remove old results
        if self._inserted_lines is not None:
            self.scene().removeItem(self._inserted_lines)
        self._inserted_lines = None
        
        bound_rect = self.scene().itemsBoundingRect()
        r_left = to_grid(min(bound_rect.left(), start.x(), end.x())) - 1
        r_top = to_grid(min(bound_rect.top(), start.y(), end.y())) - 1
        r_right = to_grid(max(bound_rect.right(), start.x(), end.x())) + 2
        r_bottom = to_grid(max(bound_rect.bottom(), 
                                     start.y(), end.y())) + 2
        
        # save lines at endpoints
        endpoint_lines = (self._get_line_at_point(start), 
                          self._get_line_at_point(end))
        
        # if both are the same --> line already exists --> nothing todo
        if endpoint_lines[0] is endpoint_lines[1] is not None:
            return
        
        # only try to find path for max. 100 ms
        max_time = [time.time() + 0.3]
        class TimeReached(Exception):
            pass
        def get_obj_at_point(point):
            if time.time() > max_time[0]:
                raise TimeReached()
            
            scene_point = to_scene_point(point)
            items = self.scene().items(scene_point)
            found_passable_line = False
            found_line_edge = False
            for item in items:
                if item is self._line_anchor_indicator:
                    continue
                if isinstance(item, logicitems.ConnectorItem) and \
                        point in (p_start, p_end):
                    continue
                if isinstance(item, logicitems.LineTree):
                    if item in endpoint_lines:
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
        
        search_rect = ((r_left, r_top), (r_right, r_bottom))
        
        try:
            res = hightower.hightower_line_search(p_start, p_end, 
                                                  get_obj_at_point, 
                                                  search_rect, 
                                                  do_second_refinement=False)
        except TimeReached:
            return
        
        if res is None:
            return
        
        def iter_line(line):
            """
            Iterate through all points on the line, except endpoint
            """
            # define two way range
            range2w = lambda a, b: range(a, b, -1 if a > b else 1)
            if line[0][1] == line[1][1]:
                for x in range2w(line[0][0], line[1][0]):
                    yield (x, line[0][1])
            else:
                for y in range2w(line[0][1], line[1][1]):
                    yield (line[0][0], y)
        
        def extract_new_path(path, line_tree):
            """
            Returns new path branching from existing line_tree.
            
            It is assumed that the path starts from the line_tree.
            """
            res = path[:]
            if line_tree is not None:
                last_index = 0
                last_point = path[0]
                for i, line in enumerate(zip(path, path[1:])):
                    for point in iter_line(line):
                        if line_tree.contains(to_scene_point(point)):
                            last_index = i
                            last_point = point
                res[last_index] = last_point
                del res[:last_index]
            return res
        res = extract_new_path(res, endpoint_lines[0])
        res = extract_new_path(list(reversed(res)), endpoint_lines[1])
        
        # add result
        lines = []
        for line in zip(res, res[1:]):
            start = to_scene_point(line[0])
            end = to_scene_point(line[1])
            lines.append(QtCore.QLineF(start, end))
        l_tree = logicitems.LineTree(lines)
        # try to merge start end end lines
        #   we don't delete them yet, rather we delete them when finally
        #   inserting the new line
        for line in endpoint_lines:
            if line is not None:
                l_tree.add_lines(line.lines())
        self.scene().addItem(l_tree)
        self._inserted_lines = l_tree
        
    
    def linesub_leave(self):
        super().linesub_leave()
        # cleanup InsertingLine
        if self._inserted_lines is not None:
            self.scene().removeItem(self._inserted_lines)
        self._inserted_lines = None

