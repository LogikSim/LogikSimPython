#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
The graphics framework defines reusable GUI classes to interact with 
schematics. 

Behaviour like drawing the grid, scrolling, interting elements
and lines is implemented here.
'''

import functools
import time

from PySide import QtGui, QtCore

from helper.timeit_mod import timeit
import modes
import logic_item

import algorithms.hightower as hightower


class BasicGridScene(QtGui.QGraphicsScene):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # draw grid?
        self._is_grid_enabled = True
        # can items be selected in this scenen?
        self._allow_item_selection = False
    
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


class BasicView(QtGui.QGraphicsView):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # workaround to immediately apply changes after maximize / restore
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.viewport().update()


class BasicGridView(BasicView):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        
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
    
    def wheelEvent(self, event):
        super().wheelEvent(event)
        
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
        self._mask_drag_mode(super().mousePressEvent, event)

        # drag mode
        if (event.button() is QtCore.Qt.MidButton or
                event.button() is QtCore.Qt.MiddleButton):
            self._mouse_mid_last_pos = self.mapToScene(event.pos())
            self.setCursor(QtCore.Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        # mid mouse pressed -> drag grid
        if (event.buttons() & QtCore.Qt.MidButton or
                event.buttons() & QtCore.Qt.MiddleButton):
            curr_pos = self.mapToScene(event.pos())
            delta = curr_pos - self._mouse_mid_last_pos
            topLeft = QtCore.QPointF(self.horizontalScrollBar().value(), 
                self.verticalScrollBar().value())
            desired_slider_pos = topLeft - delta * self.getScale()
            self.horizontalScrollBar().setSliderPosition(desired_slider_pos.x())
            self.verticalScrollBar().setSliderPosition(desired_slider_pos.y())
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if (event.button() is QtCore.Qt.MidButton or
                event.button() is QtCore.Qt.MiddleButton):
            self._mouse_mid_last_pos = None
            self.unsetCursor()
    
#    @timeit
    def paintEvent(self, *args, **kargs):
        super().paintEvent(*args, **kargs)


GridViewMouseModeBase, mouse_mode_filtered = modes.generate_mode_base(
        BasicGridView, 'mouse')


class SelectItemsMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
    
    def mouse_enter(self):
        super().mouse_enter()
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.scene().setSelectionAllowed(True)
    
    def mouse_leave(self):
        super().mouse_leave()
        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        self.scene().setSelectionAllowed(False)


class InsertItemMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # class used to insert new items
        self._insert_item_class = logic_item.LogicItem
        # reference to currently inserted item (used to move it 
        # while the mouse button is still pressed)
        self._inserted_item = None
    
    def mouse_enter(self):
        super().mouse_enter()
    
    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            item = self._insert_item_class()
            item.setPos(gpos)
            self.scene().addItem(item)
            self._inserted_item = item
    
    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        # left button
        if event.buttons() & QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            # move new item
            if self._inserted_item is not None:
                self._inserted_item.setPos(gpos)
    
    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            # prevent item from being deleted when switching modes
            self._inserted_item = None
    
    def mouse_leave(self):
        super().mouse_leave()
        # cleanup InsertItem
        if self._inserted_item is not None:
            self.scene().removeItem(self._inserted_item)
            self._inserted_item = None


LineSubModeBase, line_submode_filtered = modes.generate_mode_base(
        GridViewMouseModeBase, 'linesub')


class InsertLineSubModeBase(LineSubModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # store start position and new line items while inserting lines
        self._insert_line_start = None
        self._inserted_lines = []
        self._line_anchor_indicator = None
        # shape used for mouse collision tests while searching for 
        # line anchors (must be float!)
        self._mouse_collision_line_radius = 5.
        self._mouse_collision_connector_radius = 10.
        # used to store anchor in mouseMoveEvent
        self._mouse_move_anchor = None
    
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
                return list(filter(functools.partial(filter_func, 
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
    
    def find_line_anchor_at_view_pos(self, pos, y=None):
        """
        returns nearest anchor to pos in scene coordinates or None
        
        pos - coordinate in view coordinates
        """
        def anchor_filter(item, path, radius):
            # line items
            if radius <= self._mouse_collision_line_radius and \
                    isinstance(item, logic_item.LineItem) and \
                    item not in self._inserted_lines:
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
    
    def _do_start_insert_lines(self, view_pos, anchor=None):
        # find anchor
        if anchor is None:
            anchor = self.find_line_anchor_at_view_pos(view_pos)
        start = self.mapToSceneGrid(view_pos) if anchor is None else anchor
        # store start position
        self._insert_line_start = start
    
    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        self._mouse_move_anchor = self.find_line_anchor_at_view_pos(event.pos())
        self.setLineAnchorIndicator(self._mouse_move_anchor)


class ReadyToInsertLineSubMode(InsertLineSubModeBase):
    """ ready to insert line """
    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            self._do_start_insert_lines(event.pos())
            self.setLinesubMode(InsertingLineSubMode)


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
        self._inserted_lines = []
        self._insert_line_start_end_last = None
    
    @line_submode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
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
        
        p_start = to_grid(start.x()), to_grid(start.y())
        p_end = to_grid(end.x()), to_grid(end.y())
        
        if (p_start, p_end) == self._insert_line_start_end_last:
            return
        self._insert_line_start_end_last = p_start, p_end
        
        # remove old results
        for item in self._inserted_lines:
            self.scene().removeItem(item)
        self._inserted_lines = []
        
        bound_rect = self.scene().itemsBoundingRect()
        r_left = to_grid(min(bound_rect.left(), start.x(), end.x())) - 1
        r_top = to_grid(min(bound_rect.top(), start.y(), end.y())) - 1
        r_right = to_grid(max(bound_rect.right(), start.x(), end.x())) + 2
        r_bottom = to_grid(max(bound_rect.bottom(), 
                                     start.y(), end.y())) + 2
        
        # only try to find path for max. 100 ms
        max_time = [time.time() + 0.3]
        class TimeReached(Exception):
            pass
        def get_obj_at_point(point):
            if time.time() > max_time[0]:
                raise TimeReached()
            
            scene_point = QtCore.QPointF(*map(to_scene, point))
            items = self.scene().items(scene_point)
            found_passable_line = False
            found_line_edge = False
            for item in items:
                if item is self._line_anchor_indicator:
                    continue
                if isinstance(item, logic_item.ConnectorItem) and \
                        point in (p_start, p_end):
                    #continue
                    pass
                if isinstance(item, logic_item.LineItem):
                    if item.is_edge(scene_point):
                        found_line_edge = True
                    else:
                        found_passable_line = True
                    continue
                return hightower.Solid
            
            print()
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
        
        # draw result
        for line in zip(res, res[1:]):
            start = QtCore.QPointF(*map(to_scene, line[0]))
            end = QtCore.QPointF(*map(to_scene, line[1]))
            l_line = logic_item.LineItem(QtCore.QLineF(start, end))
            self.scene().addItem(l_line)
            self._inserted_lines.append(l_line)
        
    
    def linesub_leave(self):
        super().linesub_leave()
        # cleanup InsertingLine
        for item in self._inserted_lines:
            self.scene().removeItem(item)
        self._inserted_lines = []


class InsertLineMode(ReadyToInsertLineSubMode, InsertingLineSubMode):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
    
    def mouse_enter(self):
        super().linesub_enter()
        self.setLinesubMode(ReadyToInsertLineSubMode)
    
    def mouse_leave(self):
        super().linesub_leave()
        # cleanup InsertLine
        self.setLineAnchorIndicator(None)
        self.setLinesubMode(None)
    
    @mouse_mode_filtered
    def abort_line_inserting(self):
        self.setLinesubMode(ReadyToInsertLineSubMode)
        


class InsertConnectorMode(GridViewMouseModeBase):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # stores start position and connector while inserting connectors
        self._insert_connector_start = None
        self._inserted_connector = None
    
    @mouse_mode_filtered
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            self._insert_connector_start = gpos
            self._inserted_connector = logic_item.ConnectorItem(
                    QtCore.QLineF(gpos, gpos))
            self.scene().addItem(self._inserted_connector)
    
    @mouse_mode_filtered
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        # left button
        if event.buttons() & QtCore.Qt.LeftButton:
            gpos = self.mapToSceneGrid(event.pos())
            self._inserted_connector.setLine(QtCore.QLineF(
                    self._inserted_connector.line().p1(), gpos))
    
    @mouse_mode_filtered
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        
        # left button
        if event.button() is QtCore.Qt.LeftButton:
            # cleanup null size connectors
            if self._inserted_connector.line().length() == 0:
                self.scene().removeItem(self._inserted_connector)
            self._inserted_connector = None


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
