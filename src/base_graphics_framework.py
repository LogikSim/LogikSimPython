#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 8, 2011

@author: Christian
'''

from PySide import QtGui, QtCore

from helper.timeit_mod import timeit


class BasicGridScene(QtGui.QGraphicsScene):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsScene.__init__(self, *args, **kargs)
        # draw grid?
        self._is_grid_enabled = True
        # can items be selected in this scenen?
        self._allow_item_selection = False
    
    def setGridEnabled(self, value):
        assert isinstance(value, bool)
        self._is_grid_enabled = value

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
        painter.drawRect(self.sceneRect().adjusted(-1/lod, -1/lod, 0, 0))
    
    def roundToGrid(self, pos, y=None):
        """
        round scene coordinate to next grid point
        
        pos - QPointF or x coordinate
        """
        if y is not None:
            pos = QtCore.QPointF(pos, y)
        spacing = 100
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


class BasicGridView(QtGui.QGraphicsView):
    def __init__(self, *args, **kargs):
        super(BasicGridView, self).__init__(*args, **kargs)
        
        # used to store last position while dragging the view with the 
        # middle mouse button
        self._mouse_mid_last_pos = None
        
        #self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        #self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        #self.setOptimizationFlags(QtGui.QGraphicsView.DontSavePainterState)
        #self.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)
        
        self.scale(0.1, 0.1)
    
    def mapToSceneGrid(self, pos, y=None):
        if y is not None:
            pos = QtCore.QPoint(pos, y)
        return self.scene().roundToGrid(self.mapToScene(pos))
    
    def getScale(self):
        return QtGui.QStyleOptionGraphicsItem.levelOfDetailFromTransform(
                self.viewportTransform())
    
    def resizeEvent(self, event):
        super(BasicGridView, self).resizeEvent(event)
        # workaround to immediately apply changes after maximize / restore
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.viewport().update()
    
    def wheelEvent(self, event):
        super(BasicGridView, self).wheelEvent(event)
        
        if event.orientation() is QtCore.Qt.Horizontal or \
                event.modifiers() != QtCore.Qt.NoModifier:
            # scroll
            fake_evt = QtGui.QWheelEvent(event.pos(), 
                    event.globalPos(), event.delta(), event.buttons(), 
                    event.modifiers() &~(QtCore.Qt.ControlModifier), 
                    event.orientation())
            QtGui.QAbstractScrollArea.wheelEvent(self, fake_evt)
        else:
            # scale
            factor = 1.1**(event.delta()/60)
            new_scale = self.getScale() * factor
            if  0.0075 < new_scale < 5:
                self.scale(factor, factor)
        
        # generate mouse move event
        # workaround to update AnchorUnderMouse 
        move_event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, event.pos(),
                event.globalPos(), QtCore.Qt.NoButton, event.buttons(), 
                event.modifiers())
        self.mouseMoveEvent(move_event)
    
    def _mask_drag_mode(self, func, mouse_event):
        """
        disables rubber band mode when the left mouse button is not pressed, 
        then calls func(mouse_event)
        """
        drag_mode = self.dragMode()
        try:
            if drag_mode is QtGui.QGraphicsView.RubberBandDrag and \
                    not mouse_event.button() & QtCore.Qt.LeftButton:
                # disable rubber band drag
                self.setDragMode(QtGui.QGraphicsView.NoDrag)
            return func(mouse_event)
        finally:
            # restore old drag mode
            self.setDragMode(drag_mode)
    
    def mousePressEvent(self, event):
        # call parent with masked drag mode
        self._mask_drag_mode(super(BasicGridView, self).mousePressEvent, event)
        
        # drag mode
        if event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = self.mapToScene(event.pos())
            self.setCursor(QtCore.Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        super(BasicGridView, self).mouseMoveEvent(event)
        
        # mid mouse pressed -> drag grid
        if event.buttons() & QtCore.Qt.MiddleButton:
            curr_pos = self.mapToScene(event.pos())
            delta = curr_pos - self._mouse_mid_last_pos
            topLeft = QtCore.QPointF(self.horizontalScrollBar().value(), 
                self.verticalScrollBar().value())
            desired_slider_pos = topLeft - delta * self.getScale()
            self.horizontalScrollBar().setSliderPosition(desired_slider_pos.x())
            self.verticalScrollBar().setSliderPosition(desired_slider_pos.y())
    
    def mouseReleaseEvent(self, event):
        super(BasicGridView, self).mouseReleaseEvent(event)
        
        if event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = None
            self.unsetCursor()
    
    @timeit
    def paintEvent(self, *args, **kargs):
        super(BasicGridView, self).paintEvent(*args, **kargs)


def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    view = BasicGridView()
    view.show()
    scene = BasicGridScene()
    height = 200 * 100 # golden ratio
    scene.setSceneRect(0, 0, height * (1+5**0.5)/2, height)
    scene.addRect(8000 + 1000., 5000 + 500., 300., 600., 
            QtGui.QPen(QtCore.Qt.black))
    view.setScene(scene)
    app.exec_()

if __name__ == '__main__':
    main()
