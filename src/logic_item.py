#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Definition of base classes of all logic elements like Logic, 
Connector and Line items. 

All interactive elements of our circuit build on these classes.
They can be found in the symbols folder.
'''

from PySide import QtGui, QtCore


class MovableGraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsItem.__init__(self, *args, **kargs)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        
        # contains last valid position for self.itemChange(...)
        self._last_position = None
        # stores bounding rect
        self._bounding_rect = None
        
        self._update_bounding_rect()
    
    def _update_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect = self.ownBoundingRect().united(
                self.childrenBoundingRect()).adjusted(-25, -25, 25, 25)
    
    def _is_current_position_valid(self):
        origin = self.mapToScene(QtCore.QPointF(0, 0))
        bound_rect = self.boundingRect().translated(origin)
        return self.scene().sceneRect().contains(bound_rect)
    
    def itemChange(self, change, value):
        if self.scene() is not None:
            #
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                self._last_position = self.pos()
                return self.scene().roundToGrid(value)
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                if not self._is_current_position_valid():
                    self.setPos(self._last_position)
            #
            # only selectable when allowed by scene
            elif change == QtGui.QGraphicsItem.ItemSelectedChange:
                return value and self.scene().selectionAllowed()
            #
            # only movable when selected
            elif change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
                self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, value)
        if change in (QtGui.QGraphicsItem.ItemChildAddedChange,
                QtGui.QGraphicsItem.ItemChildRemovedChange):
            self._update_bounding_rect()
        return QtGui.QGraphicsItem.itemChange(self, change, value)
    
    def ownBoundingRect(self):
        """ bounding rect of LogicItem without considering childs """
        raise NotImplementedError
    
    def boundingRect(self):
        return self._bounding_rect
    
    def paint(self, painter, options, widget):
        #lod = options.levelOfDetailFromTransform(painter.worldTransform())
        painter.setBrush(QtCore.Qt.white)
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(0, 0, 300, 600)
        # item selection box
        if options.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.white)
            painter.drawRect(self.boundingRect())
            painter.setPen(QtGui.QPen(QtGui.QColor(40, 125, 210), 0, 
                    QtCore.Qt.DashLine))
            painter.drawRect(self.boundingRect())
    
    def mouseReleaseEvent(self, event):
        """
        default implementation of QGraphicsItem selects the current item
        if any mouse button is released, limit this behaviour to the 
        left mouse button.
        """
        if not event.button() is QtCore.Qt.LeftButton:
            # default implementation changes selection when following is true:
            # event->scenePos() == event->buttonDownScenePos(Qt::LeftButton)
            event.setButtonDownScenePos(QtCore.Qt.LeftButton, 
                    event.scenePos() + QtCore.QPointF(1, 1))
        return QtGui.QGraphicsItem.mouseReleaseEvent(self, event)
        


class LogicItem(QtGui.QGraphicsItem):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsItem.__init__(self, *args, **kargs)
        #self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        
        # contains last valid position for self.itemChange(...)
        self._last_position = None
        # stores bounding rect
        self._bounding_rect = None
        
        self._update_bounding_rect()
    
    def _update_bounding_rect(self):
        self.prepareGeometryChange()
        self._bounding_rect = self.ownBoundingRect().united(
                self.childrenBoundingRect()).adjusted(-25, -25, 25, 25)
    
    def _is_current_position_valid(self):
        origin = self.mapToScene(QtCore.QPointF(0, 0))
        bound_rect = self.boundingRect().translated(origin)
        return self.scene().sceneRect().contains(bound_rect)
    
    def itemChange(self, change, value):
        if self.scene() is not None:
            #
            # round position to grid point
            if change == QtGui.QGraphicsItem.ItemPositionChange:
                self._last_position = self.pos()
                return self.scene().roundToGrid(value)
            elif change == QtGui.QGraphicsItem.ItemPositionHasChanged:
                if not self._is_current_position_valid():
                    self.setPos(self._last_position)
            #
            # only selectable when allowed by scene
            elif change == QtGui.QGraphicsItem.ItemSelectedChange:
                return value and self.scene().selectionAllowed()
            #
            # only movable when selected
            elif change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
                self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, value)
        if change in (QtGui.QGraphicsItem.ItemChildAddedChange,
                QtGui.QGraphicsItem.ItemChildRemovedChange):
            self._update_bounding_rect()
        return QtGui.QGraphicsItem.itemChange(self, change, value)
    
    def ownBoundingRect(self):
        """ bounding rect of LogicItem without considering childs """
        return QtCore.QRectF(0, 0, 300, 600)
    
    def boundingRect(self):
        return self._bounding_rect
    
    def paint(self, painter, options, widget):
        #lod = options.levelOfDetailFromTransform(painter.worldTransform())
        painter.setBrush(QtCore.Qt.white)
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(0, 0, 300, 600)
        # item selection box
        if options.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtCore.Qt.white)
            painter.drawRect(self.boundingRect())
            painter.setPen(QtGui.QPen(QtGui.QColor(40, 125, 210), 0, 
                    QtCore.Qt.DashLine))
            painter.drawRect(self.boundingRect())
    
    def mouseReleaseEvent(self, event):
        """
        default implementation of QGraphicsItem selects the current item
        if any mouse button is released, limit this behaviour to the 
        left mouse button.
        """
        if not event.button() is QtCore.Qt.LeftButton:
            # default implementation changes selection when following is true:
            # event->scenePos() == event->buttonDownScenePos(Qt::LeftButton)
            event.setButtonDownScenePos(QtCore.Qt.LeftButton, 
                    event.scenePos() + QtCore.QPointF(1, 1))
        return QtGui.QGraphicsItem.mouseReleaseEvent(self, event)


class SmoothGrahpicsLineItem(QtGui.QGraphicsLineItem):
    def shouldAntialias(self, painter):
        # enable antialiasing for tilted lines
        inv_transform, invertable = painter.worldTransform().inverted()
        if invertable:
            angle = inv_transform.map(self.line()).angle()
            straight = abs(angle % 90 - 45) == 45
            return not straight
        else:
            return True
    
    def isHorizontalOrVertical(self):
        vline = self.line().p2() - self.line().p1()
        return vline.x() == 0 or vline.y() == 0
    
    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing, 
                self.shouldAntialias(painter))
        QtGui.QGraphicsLineItem.paint(self, painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)


class ConnectorItem(SmoothGrahpicsLineItem):
    def __init__(self, *args, **kargs):
        SmoothGrahpicsLineItem.__init__(self, *args, **kargs)
        self.setPen(QtGui.QPen(QtCore.Qt.black))
    
    def anchorPoint(self):
        """
        returns position where lines can connect to
        """
        return self.line().p2()
    
    def setLine(self, line):
        """
        line defines: start, anchor
        """
        SmoothGrahpicsLineItem.setLine(self, line)


class LineTree(QtGui.QGraphicsItem):
    """ A collection of simple lines grouped together """
    def __init__(self, lines):
        QtGui.QGraphicsItem.__init__(self)
        """lines is list of QLines"""
        self._lines = None  # list with all lines
        self._edges = None  # set with all edges as tuples
        self._shape = None  # shape path
        self._rect = None   # bounding rect
        
        #self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        
        self._update_lines(lines)
    
    def _update_lines(self, lines):
        """ Updates internal storage when lines change """
        self._lines = lines
        self._edges = set()
        for line in lines:
            self._edges.add(line.p1().toTuple())
            self._edges.add(line.p2().toTuple())
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
        self._update_lines(self.lines() + new_lines)
    
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
        
        # paint all lines - debuging
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 128)))
        for line in self._lines:
            rect = QtCore.QRectF(line.p1(), line.p2()).\
                    normalized().adjusted(-25, -25, 25, 25)
            painter.drawRect(rect)
        
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


class LineConnectorItem(QtGui.QGraphicsEllipseItem):
    """ indicates a connection between tree or more lines """
    #TODO: write implmentation
    pass


class LineAnchorIndicator(QtGui.QGraphicsEllipseItem):
    """ visual effect for line anchors while adding lines """
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsEllipseItem.__init__(self, *args, **kargs)
        self.setPen(QtGui.QPen(QtCore.Qt.darkGreen))
    
    def setWidthF(self, width):
        if width != self.widthF():
            pen = self.pen()
            pen.setWidthF(width)
            self.setPen(pen)
    
    def widthF(self):
        return self.pen().widthF()
    
    def paint(self, painter, options, widget):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        QtGui.QGraphicsEllipseItem.paint(self, painter, options, widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)


