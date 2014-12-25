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

from backend.core import Core
from backend.controller import Controller
from backend.component_library import get_library
from threading import Thread
from logging import getLogger
from logicitems.item_registry import ItemRegistry
from symbols.and_item import AndItem


class GridScene(QtGui.QGraphicsScene):
    # signals position or shape change of any selected item
    selectedItemPosChanged = QtCore.Signal()

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        # draw grid?
        self.log = getLogger("scene")

        self._is_grid_enabled = True
        # can items be selected in this scene?
        self._allow_item_selection = False

        # Setup simulation backend for this scene
        self._core = Core()
        self._controller = Controller(self._core, get_library())
        self._interface = self._controller.get_interface()

        self._registry = ItemRegistry(self._controller, self)
        self._registry.register_type(AndItem)
        self._registry.start_handling()

        self._core_thread = Thread(target=self._core.run,
                                   daemon=True)  # FIXME: Daemon :(
        self._core_thread.start()

        self.actions = ActionStackModel(self.tr("New circuit"), parent=self)

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
        self.destroyed.connect(self.on_destroyed)

    @QtCore.Slot()
    def on_destroyed(self):
        """
        Quits and joins threads that were started by this object.
        """
        self._core.quit()
        self._core_thread.join()

    def get_interface(self):
        return self._interface

    def get_registry(self):
        return self._registry

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

        :param grid_point: Point in grid coordinates
        :return: Point in scene coordinates
        """
        spacing = self.get_grid_spacing()

        def to_scene(grid_coordinate):
            """ Converts grid coordinate to self.scene coordinates """
            return grid_coordinate * spacing

        return QtCore.QPointF(*map(to_scene, grid_point))

    def to_grid(self, scene_point):
        """ Converts points in self.scene to grid points used here.

        The functions always rounds down """
        spacing = self.get_grid_spacing()
        return int(scene_point / spacing)

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
        def set_state(state):
            if self._single_selected_item is not None and \
                    self._single_selected_item.scene() is self:
                assert isinstance(self._single_selected_item,
                                  logicitems.ItemBase)
                self._single_selected_item.itemChange(
                    logicitems.ItemBase.ItemSingleSelectionHasChanged,
                    state)

        # disable last
        set_state(False)
        # enable new
        sel_items = self.selectedItems()
        if len(sel_items) == 1:
            self._single_selected_item = sel_items[0]
        else:
            self._single_selected_item = None
        set_state(True)
