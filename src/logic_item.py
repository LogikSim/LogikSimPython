#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on May 2, 2011

@author: Christian
'''

from PySide import QtGui, QtCore

import simulation_model


class LogicItem(QtGui.QGraphicsItem, simulation_model.SimulationObject):
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


class LineItem(SmoothGrahpicsLineItem):
    def __init__(self, *args, **kargs):
        SmoothGrahpicsLineItem.__init__(self, *args, **kargs)
        self.setPen(QtGui.QPen(QtCore.Qt.red))


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


