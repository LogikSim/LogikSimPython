#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Lines are connected in trees from one output to multiple inputs.
'''

import itertools

from PySide import QtGui, QtCore


class LineTree(QtGui.QGraphicsItem):
    _debug_painting = False
    
    """ A collection of simple lines grouped together """
    def __init__(self, lines):
        QtGui.QGraphicsItem.__init__(self)
        """lines is list of QLines"""
        self._lines = None  # list with all lines
        self._edges = None  # set with all edges as tuples
        self._shape = None  # shape path
        self._rect = None   # bounding rect
        self._edge_indicators = None # list of points for edge indicators
        
        #self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        
        self._update_lines(lines)
    
    def _update_lines(self, lines):
        """ Updates internal storage when lines change """
        self._lines = lines
        
        # extract all edges
        self._edges = set()
        for line in lines:
            self._edges.add(line.p1().toTuple())
            self._edges.add(line.p2().toTuple())
            
        # identify line edge indicator
        self._edge_indicators = []
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                int_type, int_point = line1.intersect(line2)
                if int_type is QtCore.QLineF.IntersectType.BoundedIntersection:
                    # exclude edges
                    if not (int_point in [line1.p1(), line1.p2()] and 
                            int_point in [line2.p1(), line2.p2()]):
                        self._edge_indicators.append(int_point)
        
        self._update_shape()
    
    def _update_shape(self):
        self.prepareGeometryChange()
        bounding_rect = None
        shape_path = QtGui.QPainterPath()
        shape_path.setFillRule(QtCore.Qt.WindingFill)
        for line in self._lines:
            l_bounding_rect = QtCore.QRectF(line.p1(), line.p2()).\
                    normalized().adjusted(-25, -25, 25, 25)
            shape_path.addRect(l_bounding_rect)
            if bounding_rect is None:
                bounding_rect = l_bounding_rect
            else:
                bounding_rect = bounding_rect.united(l_bounding_rect)
        self._shape = shape_path
        self._rect = bounding_rect
    
    def add_lines(self, new_lines):
        """
        Add lines to tree.
        """
        res = self.lines() + new_lines
        
        # find point where both trees are meeting each other
        p_collisions = []
        for line in new_lines:
            if line.p1().toTuple() in self._edges:
                p_collisions.append(line.p1())
            elif line.p2().toTuple() in self._edges:
                p_collisions.append(line.p2())
        def remove_duplicates(l):
            ret = []
            for item in l:
                if item not in ret:
                    ret.append(item)
            return ret
        p_collisions = remove_duplicates(p_collisions)
        assert len(p_collisions) <= 1, "expect that trees touch only once"
        for p_col in p_collisions:
            # find two lines which are involved in collision
            l_collision = [line for line in res 
                          if p_col in [line.p1(), line.p2()]]
            assert 2 <= len(l_collision) <= 3, "expecting no double edge"
            def is_horizontal(line):
                return line.p1().y() == line.p2().y()
            def to_rect(line):
                return QtCore.QRectF(line.p1(), line.p2())
            def to_line(rect):
                return QtCore.QLineF(rect.topLeft(), rect.bottomRight())
            # if both have same orientation combine them
            for line_pair in itertools.permutations(l_collision, 2):
                if is_horizontal(line_pair[0]) == is_horizontal(line_pair[1]):
                    new_line = to_line(
                            to_rect(line_pair[0]).united(to_rect(line_pair[1])))
                    res.remove(line_pair[0])
                    res.remove(line_pair[1])
                    res.append(new_line)
                    break
        
        self._update_lines(res)
    
    def lines(self):
        """ return lines """
        return self._lines
        
    def boundingRect(self):
        return self._rect
    
    def shape(self):
        return self._shape
    
    def is_edge(self, scene_point):
        """ Is there an edge at scene_point """
        return scene_point.toTuple() in self._edges
    
    def paint(self, painter, option, widget=None):
        painter.setPen(QtGui.QPen(QtCore.Qt.red))
        for line in self._lines:
            painter.drawLine(line)
            
        # draw edge indicators
        painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
        for edge in self._edge_indicators:
            painter.drawEllipse(edge, 20, 20)
        
        # paint all lines - debuging
        if self._debug_painting:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 128)))
            for line in self._lines:
                rect = QtCore.QRectF(line.p1(), line.p2()).\
                        normalized().adjusted(-25, -25, 25, 25)
                painter.drawRect(rect)
            for edge in self._edge_indicators:
                painter.drawEllipse(edge, 50, 50)
        
    def _get_nearest_point_of_line(self, scene_point, line):
        grid_point = self.scene().roundToGrid(scene_point)
        vline = line.p2() - line.p1()
        def constrain_to_range(x, l1, l2):
            return max(min(x, max(l1, l2)), min(l1, l2))
        if vline.x() == 0: # vertical
            return QtCore.QPointF(line.p1().x(), constrain_to_range(
                    grid_point.y(), line.p1().y(), line.p2().y()))
        elif vline.y() == 0: # horizontal
            return QtCore.QPointF(constrain_to_range(grid_point.x(), 
                    line.p1().x(), line.p2().x()), line.p1().y())
        else: # somehow tilted
            raise Exception("Found tilted line")
            
    def get_nearest_point(self, scene_point):
        p_nearest = None
        for line in self._lines:
            p = self._get_nearest_point_of_line(scene_point, line)
            if p_nearest is None or ((scene_point - p).manhattanLength() < 
                    (scene_point - p_nearest).manhattanLength()):
                p_nearest = p
        return p_nearest
