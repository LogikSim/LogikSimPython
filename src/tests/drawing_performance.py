#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

import sys

from PySide import QtGui, QtCore

import schematic_widget

def draw_one_rect(scene):
    scene.addRect(80000 + 1000., 50000 + 500., 300., 600., 
            QtGui.QPen(QtCore.Qt.white))


def draw_overlapping_rects(scene):
    scene.addRect(80000 + 1000., 50000 + 500., 300., 600., 
            QtGui.QPen(QtCore.Qt.white))
    scene.addRect(80000 + 1100., 50000 + 600., 300., 600., 
            QtGui.QPen(QtCore.Qt.white))


def draw_rects_test(scene):
    # draw 27k rects
    for x in range(300):
        for y in range(90):
            scene.addRect(8000 + x * 500, 5000 + y * 1000, 300, 600, 
                    QtGui.QPen(QtCore.Qt.white), QtGui.QBrush(QtCore.Qt.black))


def draw_items_test(scene):
    # draw 27k simple items (directly)
    class SimpleItem(QtGui.QGraphicsItem):
        rect = QtCore.QRectF(0, 0, 300, 600)
        pen = QtGui.QPen(QtCore.Qt.white)
        brush = QtGui.QBrush(QtCore.Qt.black)
        def boundingRect(self):
            return self.rect
        def paint(self, painter, options, widget):
            painter.setBrush(self.brush)
            painter.setPen(self.pen)
            painter.drawRect(self.rect)
    for x in range(300):
        for y in range(90):
            item = SimpleItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)


def draw_item_DontSavePainterState_test(scene):
    view = scene.views()[0]
    view.setOptimizationFlags(QtGui.QGraphicsView.DontSavePainterState)
    draw_items_test(scene)


def draw_item_picture_test(scene):
    # draw 27k simple items based on QPicture
    class SimpleItem(QtGui.QGraphicsItem):
        rect = QtCore.QRectF(0, 0, 300, 600)
        def __init__(self, *args, **kargs):
            QtGui.QGraphicsItem.__init__(self, *args, **kargs)
            self.picture = self.gen_new_picture()
        def gen_new_picture(self):
            picture = QtGui.QPicture()
            painter = QtGui.QPainter()
            painter.begin(picture)
            painter.setBrush(QtCore.Qt.black)
            painter.setPen(QtCore.Qt.white)
            painter.drawRect(self.rect)
            painter.end()
            return picture
        def boundingRect(self):
            return self.rect
        def paint(self, painter, options, widget):
            self.picture.play(painter)
    for x in range(300):
        for y in range(90):
            item = SimpleItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)


def draw_item_picture_memory_test(scene):
    rect = QtCore.QRectF(0, 0, 300, 600)
    # draw 27k simple items based on QPicture
    def gen_new_picture():
        picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(picture)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.white)
        painter.drawRect(rect)
        painter.end()
        return picture
    class SimpleItem(QtGui.QGraphicsItem):
        picture = gen_new_picture()
        def __init__(self, *args, **kargs):
            QtGui.QGraphicsItem.__init__(self, *args, **kargs)
        def boundingRect(self):
            return rect
        def paint(self, painter, options, widget):
            self.picture.play(painter)
    for x in range(300):
        for y in range(90):
            item = SimpleItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)

def draw_complex_item_test(scene):
    # draw 27k simple items (directly)
    class SimpleItem(QtGui.QGraphicsItem):
        rect = QtCore.QRectF(0, 0, 300, 600)
        pen = QtGui.QPen(QtCore.Qt.white)
        brush = QtGui.QBrush(QtCore.Qt.black)
        def boundingRect(self):
            return self.rect
        def paint(self, painter, options, widget):
            painter.setBrush(self.brush)
            painter.setPen(self.pen)
            painter.drawRect(self.rect)
            for i in range(10):
                painter.drawLine(0, 60 * i, 30 * i, 0)
                painter.drawLine(300, 60 * i, 30 * i, 600)
                painter.drawLine(0, 60 * i, 300 - 30 * i, 600)
                painter.drawLine(300, 60 * i, 300- 30 * i, 0)
    for x in range(300):
        for y in range(90):
            item = SimpleItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)


def draw_complex_picture_item_test(scene):
    rect = QtCore.QRectF(0, 0, 300, 600)
    # draw 27k simple items based on QPicture
    def gen_new_picture():
        picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(picture)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.white)
        painter.drawRect(rect)
        for i in range(10):
            painter.drawLine(0, 60 * i, 30 * i, 0)
            painter.drawLine(300, 60 * i, 30 * i, 600)
            painter.drawLine(0, 60 * i, 300 - 30 * i, 600)
            painter.drawLine(300, 60 * i, 300- 30 * i, 0)
        painter.end()
        return picture
    class SimpleItem(QtGui.QGraphicsItem):
        picture = gen_new_picture()
        def __init__(self, *args, **kargs):
            QtGui.QGraphicsItem.__init__(self, *args, **kargs)
        def boundingRect(self):
            return rect
        def paint(self, painter, options, widget):
            self.picture.play(painter)
    for x in range(300):
        for y in range(90):
            item = SimpleItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)


def draw_complex_item_open_gl_test(scene):
    view = scene.views()[0]
    from PySide import QtOpenGL
    view.setViewport(QtOpenGL.QGLWidget(QtOpenGL.QGLFormat(
            QtOpenGL.QGL.SampleBuffers)))
    draw_complex_item_test(scene)


def draw_complex_item_open_gl_full_update_test(scene):
    view = scene.views()[0]
    view.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    draw_complex_item_open_gl_test(scene)

def draw_many_logic_items_test(scene):
    from logic_item import LogicItem
    for x in range(300):
        for y in range(90):
            item = LogicItem()
            item.setPos(8000 + x * 500, 5000 + y * 1000)
            scene.addItem(item)


def add_items(scene):
    #draw_one_rect(scene) # 35 ms, 26 MB
    #draw_overlapping_rects(scene)
    #draw_rects_test(scene) # 185 ms, 51 MB
    #draw_items_test(scene) # 352 ms, 41 MB
    #draw_item_DontSavePainterState_test(scene) # 342 ms, 41 MB
    #draw_item_picture_test(scene) # 720 ms, 250 MB
    #draw_item_picture_memory_test(scene) # 660 ms, 41 MB
    #draw_complex_item_test(scene) # 1400 ms, 41 MB
    #draw_complex_picture_item_test(scene) # 2000 ms, 41 MB
    #draw_complex_item_open_gl_test(scene) # 2200 ms, 63 MB
    #draw_complex_item_open_gl_full_update_test(scene) # 2200 ms
    draw_many_logic_items_test(scene) # 900 ms, 59 MB


def main():
    app = QtGui.QApplication(sys.argv)
    
    view = schematic_widget.SchematicView()
    view.show()
    
    scene = view.scene()
    add_items(scene)
    app.exec_()

if __name__ == '__main__':
    main()
