#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Apr 26, 2011

@author: Christian
'''

import functools

from PySide import QtGui, QtCore

from helper.timeit_mod import timeit
import logic_item


class SchematicScene(QtGui.QGraphicsScene):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsScene.__init__(self, *args, **kargs)
        
        height = 100 * 1000 # golden ratio
        self.setSceneRect(0, 0, height * (1+5**0.5)/2, height)
        
        # can items be selected in this scenen?
        self._allow_item_selection = False

    def get_grid_spacing_from_scale(self, scale):
        return 100 if scale > 0.033 else 500
    
    #@timeit
    def drawBackground(self, painter, rect):
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


# enum like state definition
class MouseMode(object):
    SelectItems = object()
    InsertItem = object()
    InsertLine = object() # ready to insert line
    InsertingLine = object() # while new lines are inserted
    InsertConnector = object()


class SchematicView(QtGui.QGraphicsView):
    def __init__(self, *args, **kargs):
        QtGui.QGraphicsView.__init__(self, *args, **kargs)
        self.setScene(SchematicScene())
        
        self._mouse_mode = None
        # used to store last position while dragging the view with the 
        # middle mouse button
        self._mouse_mid_last_pos = None
        # class used to insert new items
        self._insert_item_class = logic_item.LogicItem
        # reference to currently inserted item (used to move it around
        # while the mouse button is still pressed)
        self._inserted_item = None
        # store start position and new line items while inserting lines
        self._insert_line_start = None
        self._inserted_line_hor = None
        self._inserted_line_ver = None
        self._line_anchor_indicator = None
        # stores start position and connector while inserting connectors
        self._insert_connector_start = None
        self._inserted_connector = None
        # shape used for mouse collision tests while searching for 
        # line anchors (must be float!)
        self._mouse_collision_line_radius = 18.
        self._mouse_collision_connector_radius = 25.
        
        self.setMouseMode(MouseMode.SelectItems)
        
        #self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        #self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        #self.setOptimizationFlags(QtGui.QGraphicsView.DontSavePainterState)
        #self.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)
        
        self.scale(0.1, 0.1)
    
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
                return filter(functools.partial(filter_func, 
                        path=self.mapToScene(path)), items)
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
                    isinstance(item, logic_item.LineItem) and item not in \
                    (self._inserted_line_hor, self._inserted_line_ver):
                return item.isHorizontalOrVertical() or path.contains(
                        item.line().p1()) or path.contains(item.line().p2())
            # connector items
            elif radius <= self._mouse_collision_connector_radius and \
                    isinstance(item, logic_item.ConnectorItem) and \
                    item is not self._inserted_connector:
                return path.contains(item.mapToScene(item.anchorPoint()))
        
        if y is not None:
            pos = QtCore.QPoint(pos, y)
        r_min, r_max = sorted((self._mouse_collision_line_radius, \
                self._mouse_collision_connector_radius))
        # first try to find item on smaller radius
        item = self.find_nearest_item_at_pos(pos, r_min, 
                functools.partial(anchor_filter, radius=r_min))
        # if nothing found, try to find item on larger radius
        if item is None:
            item = self.find_nearest_item_at_pos(pos, r_max, 
                    functools.partial(anchor_filter, radius=r_max))
        # find nearest point on line (in scene coordinates)
        if isinstance(item, logic_item.LineItem):
            line = item.line()
            spos = self.mapToScene(pos)
            gpos = self.scene().roundToGrid(spos)
            vline = line.p2() - line.p1()
            def contrain_to_range(x, l1, l2):
                return max(min(x, max(l1, l2)), min(l1, l2))
            if vline.x() == 0: # vertical
                return QtCore.QPointF(line.p1().x(), contrain_to_range(
                        gpos.y(), line.p1().y(), line.p2().y()))
            elif vline.y() == 0: # horizontal
                return QtCore.QPointF(contrain_to_range(gpos.x(), 
                        line.p1().x(), line.p2().x()), line.p1().y())
            else: # somehow tilted
                if (line.p1() - spos).manhattanLength() < \
                        (line.p2() - spos).manhattanLength():
                    return line.p1()
                else:
                    return line.p2()
        # return anchor point for connectors
        if isinstance(item, logic_item.ConnectorItem):
            return item.mapToScene(item.anchorPoint())
    
    def mapToSceneGrid(self, pos, y=None):
        if y is not None:
            pos = QtCore.QPoint(pos, y)
        return self.scene().roundToGrid(self.mapToScene(pos))
    
    def setLineAnchorIndicator(self, pos):
        """ pos - scene pos or None """
        if pos is None:
            if self._line_anchor_indicator is not None:
                self.scene().removeItem(self._line_anchor_indicator)
                self._line_anchor_indicator = None
        else:
            scale = self.getScale()
            size = max(1 / scale * 10, 70)
            rect = QtCore.QRectF(pos.x() - size/2, pos.y() - size/2, size, size)
            pen_width = max(1 / scale, 8)
            if self._line_anchor_indicator is None:
                # create new
                item = logic_item.LineAnchorIndicator(rect)
                item.setWidthF(pen_width)
                self._line_anchor_indicator = item
                self.scene().addItem(item)
            else:
                # resize existing
                self._line_anchor_indicator.setRect(rect)
                self._line_anchor_indicator.setWidthF(pen_width)
    
    def setMouseMode(self, mouse_mode):
        if mouse_mode != self._mouse_mode:
            #
            # rubber band with SelectItems
            if mouse_mode is MouseMode.SelectItems:
                self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
            else:
                self.setDragMode(QtGui.QGraphicsView.NoDrag)
            #
            # only allow selections with SelectItems
            self.scene().setSelectionAllowed(mouse_mode is 
                    MouseMode.SelectItems)
            #
            # cleanup InsertItem
            if mouse_mode is not MouseMode.InsertItem:
                if self._inserted_item is not None:
                    self.scene().removeItem(self._inserted_item)
                    self._inserted_item = None
            #
            # cleanup InsertLine
            if mouse_mode is not MouseMode.InsertLine:
                self.setLineAnchorIndicator(None)
            #
            # cleanup InsertingLine
            if mouse_mode is not MouseMode.InsertingLine:
                self._do_abort_insert_lines()
            
            
            self._mouse_mode = mouse_mode
    
    def getScale(self):
        return QtGui.QStyleOptionGraphicsItem.levelOfDetailFromTransform(
                self.viewportTransform())
    
    def resizeEvent(self, event):
        QtGui.QGraphicsView.resizeEvent(self, event)
        # workaround to immediately apply changes after maximize / restore
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.viewport().update()
    
    def wheelEvent(self, event):
        QtGui.QGraphicsView.wheelEvent(self, event)
        
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
    
    def _do_start_insert_lines(self, view_pos, anchor=None):
        # find anchor
        if anchor is None:
            anchor = self.find_line_anchor_at_view_pos(view_pos)
        start = self.mapToSceneGrid(view_pos) if anchor is None else anchor
        # create lines
        self._insert_line_start = start
        self._inserted_line_hor = logic_item.LineItem(
                QtCore.QLineF(start, start))
        self._inserted_line_ver = logic_item.LineItem(
                QtCore.QLineF(start, start))
        self.scene().addItem(self._inserted_line_hor)
        self.scene().addItem(self._inserted_line_ver)
    
    def _do_abort_insert_lines(self):
        if self._inserted_line_hor is not None:
            self.scene().removeItem(self._inserted_line_hor)
            self._inserted_line_hor = None
        if self._inserted_line_ver is not None:
            self.scene().removeItem(self._inserted_line_ver)
            self._inserted_line_ver = None
    
    def _do_end_insert_lines(self):
        if self._inserted_line_hor.line().length() == 0:
            self.scene().removeItem(self._inserted_line_hor)
        if self._inserted_line_ver.line().length() == 0:
            self.scene().removeItem(self._inserted_line_ver)
        self._inserted_line_hor = None
        self._inserted_line_ver = None
    
    def _mask_drag_mode(self, func, mouse_event):
        """
        disables rubber band mode when the left mouse button is not pressed, 
        then calls func(self, mouse_event)
        """
        drag_mode = self.dragMode()
        try:
            if drag_mode is QtGui.QGraphicsView.RubberBandDrag and \
                    not mouse_event.button() & QtCore.Qt.LeftButton:
                # disable rubber band drag
                self.setDragMode(QtGui.QGraphicsView.NoDrag)
            return func(self, mouse_event)
        finally:
            # restore old drag mode
            self.setDragMode(drag_mode)
    
    def mousePressEvent(self, event):
        # call parent with masked drag mode
        self._mask_drag_mode(QtGui.QGraphicsView.mousePressEvent, event)
        
        # drag mode
        if event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = self.mapToScene(event.pos())
            self.setCursor(QtCore.Qt.ClosedHandCursor)
        # left button
        elif event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            # insert new lines
            if self._mouse_mode is MouseMode.InsertLine:
                self._do_start_insert_lines(event.pos())
                self.setMouseMode(MouseMode.InsertingLine)
            # finish line & add further lines
            elif self._mouse_mode is MouseMode.InsertingLine:
                anchor = self.find_line_anchor_at_view_pos(event.pos())
                self._do_end_insert_lines()
                if anchor is None:
                    self._do_start_insert_lines(event.pos(), anchor)
                else:
                    self.setMouseMode(MouseMode.InsertLine)
            # insert new item
            elif self._mouse_mode is MouseMode.InsertItem:
                item = self._insert_item_class()
                item.setPos(gpos)
                self.scene().addItem(item)
                self._inserted_item = item
            # insert connector
            elif self._mouse_mode is MouseMode.InsertConnector:
                self._insert_connector_start = gpos
                self._inserted_connector = logic_item.ConnectorItem(
                        QtCore.QLineF(gpos, gpos))
                self.scene().addItem(self._inserted_connector)
        # right button
        elif event.button() is QtCore.Qt.RightButton:
            if self._mouse_mode is MouseMode.InsertingLine:
                self.setMouseMode(MouseMode.InsertLine)
    
    @timeit
    def mouseMoveEvent(self, event):
        QtGui.QGraphicsView.mouseMoveEvent(self, event)
        
        # mid mouse pressed -> drag grid
        if event.buttons() & QtCore.Qt.MiddleButton:
            curr_pos = self.mapToScene(event.pos())
            delta = curr_pos - self._mouse_mid_last_pos
            topLeft = QtCore.QPointF(self.horizontalScrollBar().value(), 
                self.verticalScrollBar().value())
            desired_slider_pos = topLeft - delta * self.getScale()
            self.horizontalScrollBar().setSliderPosition(desired_slider_pos.x())
            self.verticalScrollBar().setSliderPosition(desired_slider_pos.y())
        # mouse mode
        if event.buttons() & QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            # move new item
            if self._mouse_mode is MouseMode.InsertItem:
                if self._inserted_item is not None:
                    self._inserted_item.setPos(gpos)
            # resize connector
            elif self._mouse_mode is MouseMode.InsertConnector:
                self._inserted_connector.setLine(QtCore.QLineF(
                        self._inserted_connector.line().p1(), gpos))
        
        # line mode
        if self._mouse_mode in (MouseMode.InsertLine, MouseMode.InsertingLine):
            # find anchor
            anchor = self.find_line_anchor_at_view_pos(event.pos())
            self.setLineAnchorIndicator(anchor)
            if self._mouse_mode is MouseMode.InsertingLine:
                gpos = self.mapToSceneGrid(event.pos())
                end = gpos if anchor is None else anchor
                start = self._insert_line_start
                # adjust lines
                hline = QtCore.QLineF(start.x(), start.y(), end.x(), start.y())
                vline = QtCore.QLineF(end.x(), start.y(), end.x(), end.y())
                self._inserted_line_hor.setLine(hline)
                self._inserted_line_ver.setLine(vline)
    
    def mouseReleaseEvent(self, event):
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        
        if event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = None
            self.unsetCursor()
        # mouse mode
        elif event.button() is QtCore.Qt.LeftButton:
            # cleanup null size connectors
            if self._mouse_mode is MouseMode.InsertConnector:
                if self._inserted_connector.line().length() == 0:
                    self.scene().removeItem(self._inserted_connector)
                self._inserted_connector = None
            # prevent item from beeing deleted when switching modes
            if self._mouse_mode is MouseMode.InsertItem:
                self._inserted_item = None
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F1:
            print 'selection mode'
            self.setMouseMode(MouseMode.SelectItems)
        elif event.key() == QtCore.Qt.Key_F2:
            print 'insert logic element'
            self.setMouseMode(MouseMode.InsertItem)
        elif event.key() == QtCore.Qt.Key_F3:
            print 'insert connector'
            self.setMouseMode(MouseMode.InsertConnector)
        elif event.key() == QtCore.Qt.Key_F4:
            print 'insert lines'
            self.setMouseMode(MouseMode.InsertLine)
        elif event.key() == QtCore.Qt.Key_Escape:
            if self._mouse_mode is MouseMode.InsertingLine:
                self.setMouseMode(MouseMode.InsertLine)
        else:
            QtGui.QGraphicsView.keyPressEvent(self, event)
    
    @timeit
    def paintEvent(self, *args, **kargs):
        QtGui.QGraphicsView.paintEvent(self, *args, **kargs)
    

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    
    view = SchematicView()
    view.show()
    
    scene = view.scene()
    scene.addRect(80000 + 1000., 50000 + 500., 300., 600., 
            QtGui.QPen(QtCore.Qt.white))
    
    app.exec_()

 
if __name__ == '__main__':
    main()
