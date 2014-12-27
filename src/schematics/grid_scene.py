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

from PySide import QtGui, QtCore

from actions.action_stack_model import ActionStackModel
import logicitems


class GridScene(QtGui.QGraphicsScene):
    # signals position or shape change of any selected item
    selectedItemPosChanged = QtCore.Signal()

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # draw grid?
        self._is_grid_enabled = True
        # can items be selected in this scenen?
        self._allow_item_selection = False

        self.actions = ActionStackModel(self.tr("New circuit"), parent=self)
        self.actions.aboutToUndo.connect(self.onAboutToUndoRedo)
        self.actions.aboutToRedo.connect(self.onAboutToUndoRedo)

        # default values for new scene
        height = 100 * 1000  # golden ratio
        self.setSceneRect(0, 0, height * (1 + 5 ** 0.5) / 2, height)

        # setup selection item
        self._selection_item = logicitems.SelectionItem()
        self.addItem(self._selection_item)
        self.selectionChanged.connect(self._selection_item.onSelectionChanged)
        self.selectedItemPosChanged.connect(
            self._selection_item.onSelectedItemPosChanged)

        # setup signal for single selection notification
        self._single_selected_item = None
        self.selectionChanged.connect(self.onSelectionChanged)

        # group undo redo events
        self._is_undo_redo_grouping = False
        self._undo_redo_group_id = 0

    def setGridEnabled(self, value):
        assert isinstance(value, bool)
        self._is_grid_enabled = value

    def get_grid_spacing(self):
        return 100

    def get_grid_spacing_from_scale(self, scale):
        return 100 if scale > 0.033 else 500

    def get_lod_from_painter(self, painter):
        return QtGui.QStyleOptionGraphicsItem.levelOfDetailFromTransform(
            painter.worldTransform())

    def get_grid_spacing_from_painter(self, painter):
        lod = self.get_lod_from_painter(painter)
        return self.get_grid_spacing_from_scale(lod)

    def to_scene_point(self, grid_point):
        """
        Converts grid tuple to QPointF in scene coordinates.

        :param grid_point: Point in grid coordinates as tuple (int, int)
        :return: Point in scene coordinates as QtCore.QPointF
        """
        spacing = self.get_grid_spacing()
        x, y = grid_point
        return QtCore.QPointF(x * spacing, y * spacing)

    def to_grid(self, scene_point):
        """ Converts points in self.scene to grid points used here.

        The functions always rounds down

        :param scene_point: Point in scene coordinates as QtCore.QPointF
        :return: Point in grid coordinates as tuple (int, int)
        """
        spacing = self.get_grid_spacing()
        return int(scene_point.x() / spacing), int(scene_point.y() / spacing)

    # @timeit
    def drawBackground(self, painter, rect):
        if self._is_grid_enabled:
            self._draw_grid(painter, rect)
        else:
            painter.setBrush(QtCore.Qt.white)
            painter.drawRect(rect)

    def _draw_grid(self, painter, rect):
        # calculate step
        lod = self.get_lod_from_painter(painter)
        step = self.get_grid_spacing_from_painter(painter)
        # estimate area to redraw (limit background to sceneRect)

        def step_round(x, n=0):
            return int(x / step + n) * step

        crect = rect.intersected(self.sceneRect())
        x0, y0 = map(step_round, (crect.x(), crect.y()))

        def get_extend(dir):
            return min(step_round(getattr(crect, dir)(), 2),
                       int(getattr(self.sceneRect(), dir)()))

        w, h = map(get_extend, ('width', 'height'))

        # pen_minor = QtGui.QPen((QtGui.QColor(23, 23, 23))) # dark mode
        # pen_major = QtGui.QPen((QtGui.QColor(30, 30, 30))) # dark mode
        pen_minor = QtGui.QPen((QtGui.QColor(0, 0, 0, 20)))  # light mode
        pen_major = QtGui.QPen((QtGui.QColor(0, 0, 0, 40)))  # light mode
        # draw border (everything outside of sceneRect)
        painter.setBrush(QtGui.QColor(210, 210, 210))
        painter.setPen(QtCore.Qt.NoPen)
        # border = QtGui.QPolygonF(rect).subtracted(QtGui.QPolygonF(
        #        self.sceneRect()))
        # painter.drawPolygon(border)
        painter.drawRect(rect)
        # translate to scene origin
        painter.save()
        painter.translate(x0, y0)
        # draw shadow and white background
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 100)))
        srect = QtCore.QRectF(0, 0, w, h)
        # painter.drawRect(srect.translated(5/lod, 5/lod))
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
        # painter.drawRect(self.sceneRect().adjusted(-1/lod, -1/lod, 0, 0))
        # ### above does not work in PySide 1.2.2
        # ## see http://stackoverflow.com/questions/18862234
        # ## starting workaround
        rect = self.sceneRect().adjusted(-1 / lod, -1 / lod, 0, 0)
        painter.drawLine(rect.topLeft(), rect.topRight())
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomRight(), rect.bottomLeft())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())
        # ### end workaround

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
        # the right mouse button
        #
        # original implementation has something like:
        # if qobject_cast<QGraphicsView*>(mouseEvent->widget()->parentWidget())
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

    def onSelectionChanged(self):
        def set_single_selection_state(item, state):
            if item is not None and item.scene() is self:
                assert isinstance(item, logicitems.ItemBase)
                item.itemChange(
                    logicitems.ItemBase.ItemSingleSelectionHasChanged, state)

        # disable last
        set_single_selection_state(self._single_selected_item, False)
        # enable new
        sel_items = self.selectedItems()
        if len(sel_items) == 1:
            self._single_selected_item = sel_items[0]
            set_single_selection_state(self._single_selected_item, True)
        else:
            self._single_selected_item = None

    @QtCore.Slot()
    def onAboutToUndoRedo(self):
        self.clearSelection()

    def getUndoRedoGroupId(self):
        """
        Get undo redo group id.

        All undo/redo actions with the same group should be merged.
        """
        if self._is_undo_redo_grouping:
            return self._undo_redo_group_id
        else:
            return -1

    def beginUndoRedoGroup(self):
        """Group all coming item changes into one undo entry."""
        self._undo_redo_group_id += 1
        assert not self._is_undo_redo_grouping
        self._is_undo_redo_grouping = True

    def endUndoRedoGroup(self):
        """End grouping of undo entries."""
        assert self._is_undo_redo_grouping
        self._is_undo_redo_grouping = False
