#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Test the scene logic for inserting lines.

(schematic -> mouse-mode -> line-submode -> inserting)
'''

import unittest

from PySide import QtCore

from schematics.mouse_modes.line_submode.inserting import (
    GetHightowerObjectAtPoint, LineRouteBetweenPoints, EndpointTrees)
from schematics.grid_scene import GridScene
from algorithms import hightower
from symbols import AndItem
from logicitems import LineTree


class TestHightowerObject(unittest.TestCase):
    def test_empty_scene(self):
        scene = GridScene()
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((10, 0)), None)
        self.assertIs(ho((0, 10)), None)
        self.assertIs(ho((10, 10)), None)

    def test_colision_add_item(self):
        scene = GridScene()
        and_item = AndItem()
        and_item.setPos(scene.to_scene_point((2, 2)))
        scene.addItem(and_item)
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((10, 0)), None)

        self.assertIs(ho((2, 2)), hightower.Solid)

    def test_colision_line_tree(self):
        scene = GridScene()

        def tsp(x, y):
            return scene.to_scene_point((x, y))
        tree = LineTree([tsp(5, 0), tsp(15, 0)])
        scene.addItem(tree)
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((5, 5)), None)

        self.assertIs(ho((5, 0)), hightower.LineEdge)
        self.assertIs(ho((15, 0)), hightower.LineEdge)

        self.assertIs(ho((10, 0)), hightower.PassableLine)


class TestLineRoute(unittest.TestCase):
    def test_horizontal_line(self):
        scene = GridScene()

        def tsp(x, y):
            return scene.to_scene_point((x, y))
        line_route = LineRouteBetweenPoints(scene, tsp(5, 10), tsp(15, 10))
        line_route.route()
        line_route.do_temp_insert()

        # check line count
        trees = [item for item in scene.items() if isinstance(item, LineTree)]
        self.assertEqual(len(trees), 1)

        # check edges
        tree = trees[0]
        self.assertTrue(tree.is_edge(tsp(5, 10)))
        self.assertTrue(tree.is_edge(tsp(15, 10)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(tsp(5, 10),
                                                         tsp(15, 10))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(tsp(5, 10),
                                                          tsp(4, 10))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(tsp(5, 10),
                                                          tsp(5, 9))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(tsp(5, 10),
                                                          tsp(5, 11))))
