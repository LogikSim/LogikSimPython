#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Defines scene that contain all the parts of the schematics.
'''

from actions.ActionStackModel import ActionStackModel

from PySide import QtGui, QtCore


class GridScene(QtGui.QGraphicsScene):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # draw grid?
        self._is_grid_enabled = True
        # can items be selected in this scenen?
        self._allow_item_selection = False

        self.actions =  ActionStackModel(self.tr("New circuit"), parent = self)
        
        # default values for new scene
        height = 100 * 1000 # golden ratio
        self.setSceneRect(0, 0, height * (1+5**0.5)/2, height)
    
    def setGridEnabled(self, value):
        assert isinstance(value, bool)
        self._is_grid_enabled = value
    
    def get_grid_spacing(self):
        return 100

    def get_grid_spacing_from_scale(self, scale):
        return 100 if scale > 0.033 else 500
    
    #@timeit
    def drawBackground(self, painter, rect):
        if self._is_grid_enabled:
            self._draw_grid(painter, rect)
        else:
            painter.setBrush(QtCore.Qt.white)
            painter.drawRect(rect)
    
    def _draw_grid(self, painter, rect):
        # calculate step
        lod = QtGui.QStyleOptionGraphicsItem.levelOfDetailFromTransform(
                painter.worldTransform())
        step = self.get_grid_spacing_from_scale(lod)
        # estimate area to redraw (limit background to sceneRect)
        step_round = lambda x, n=0: int(x / step + n) * step
        crect = rect.intersected(self.sceneRect())
        x0, y0 = map(step_round, (crect.x(), crect.y()))
        get_extend = lambda dir: min(step_round(getattr(crect, dir)(), 2), 
                int(getattr(self.sceneRect(), dir)()))
        w, h = map(get_extend, ('width', 'height'))
        
        #pen_minor = QtGui.QPen((QtGui.QColor(23, 23, 23))) # dark mode
        #pen_major = QtGui.QPen((QtGui.QColor(30, 30, 30))) # dark mode
        pen_minor = QtGui.QPen((QtGui.QColor(0, 0, 0, 20))) # light mode
        pen_major = QtGui.QPen((QtGui.QColor(0, 0, 0, 40))) # light mode
        # draw border (everything outside of sceneRect)
        painter.setBrush(QtGui.QColor(210, 210, 210))
        painter.setPen(QtCore.Qt.NoPen)
        #border = QtGui.QPolygonF(rect).subtracted(QtGui.QPolygonF(
        #        self.sceneRect()))
        #painter.drawPolygon(border)
        painter.drawRect(rect)
        # translate to scene origin
        painter.save()
        painter.translate(x0, y0)
        # draw shadow and white background
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 100)))
        srect = QtCore.QRectF(0, 0, w, h)
        #painter.drawRect(srect.translated(5/lod, 5/lod))
        painter.setBrush(QtCore.Qt.white)
        painter.drawRect(srect)
        # draw grid
        def set_pen(z):
            painter.setPen(pen_major if z % 500 == 0 else pen_minor)
        for x in range(0, w, step):
            set_pen(x0 + x)
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            set_pen(y0 + y)
            painter.drawLine(0, y, w, y)
        # draw border
        painter.restore()
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtCore.Qt.black)
        #painter.drawRect(self.sceneRect().adjusted(-1/lod, -1/lod, 0, 0))
        ### above does not work in PySide 1.2.2
        ## see http://stackoverflow.com/questions/18862234
        ## starting workaround
        rect = self.sceneRect().adjusted(-1/lod, -1/lod, 0, 0)
        painter.drawLine(rect.topLeft(), rect.topRight())
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomRight(), rect.bottomLeft())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())
        ### end workaround
    
    def roundToGrid(self, pos, y=None):
        """
        round scene coordinate to next grid point
        
        pos - QPointF or x coordinate
        """
        if y is not None:
            pos = QtCore.QPointF(pos, y)
        spacing = self.get_grid_spacing()
        return (pos / spacing).toPoint() * spacing
    
    def selectionAllowed(self):
        return self._allow_item_selection
    
    def setSelectionAllowed(self, value):
        self._allow_item_selection = value
        if not value:
            self.clearSelection()
    
    def mousePressEvent(self, mouseEvent):
        # Hack: prevent clearing the selection, e.g. while dragging or pressing
        #        the right mouse button
        #
        # original implementation has something like:
        # if qobject_cast<QGraphicsView *>(mouseEvent->widget()->parentWidget())
        #    view = mouseEvent->widget()
        #    dontClearSelection = view && view->dragMode() ==  
        #         QGraphicsView::ScrollHandDrag
        view = mouseEvent.widget().parentWidget()
        if isinstance(view, QtGui.QGraphicsView):
            origDragMode = view.dragMode()
            try:
                view.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
                QtGui.QGraphicsScene.mousePressEvent(self, mouseEvent)
            finally:
                view.setDragMode(origDragMode)
        else:
            QtGui.QGraphicsScene.mousePressEvent(self, mouseEvent)
    
    def wheelEvent(self, event):
        QtGui.QGraphicsScene.wheelEvent(self, event)
        # mark event as handled (prevent view from scrolling)
        event.accept()
