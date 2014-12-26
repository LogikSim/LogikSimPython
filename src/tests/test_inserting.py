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

        # check line count & temp
        trees = [item for item in scene.items() if isinstance(item, LineTree)]
        self.assertEqual(len(trees), 1)
        self.assertTrue(trees[0].is_temporary())

        # insert & check line count & temp
        line_route.do_insert()
        trees = [item for item in scene.items() if isinstance(item, LineTree)]
        self.assertEqual(len(trees), 1)
        self.assertFalse(trees[0].is_temporary())

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


class TestLineRouteGraphical(unittest.TestCase):
    def fill_scene(self, scene, input_area):
        lines = input_area.split('\n')

        def add_tree(p1, p2):
            scene.addItem(LineTree([scene.to_scene_point(p1),
                                    scene.to_scene_point(p2)]))

        # insert line stubs
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char in '-+┬┴':  # horizontal
                    add_tree((x - 0.5, y), (x + 0.5, y))
                if char in '┤+├|':
                    add_tree((x, y - 0.5), (x, y + 0.5))
                if char in '┐˄┬┌x':
                    add_tree((x, y), (x, y + 0.5))
                if char in '┘└˅┴x':
                    add_tree((x, y), (x, y - 0.5))
                if char in '┌└<├x':
                    add_tree((x, y), (x + 0.5, y))
                if char in '>┤┐┘x':
                    add_tree((x, y), (x - 0.5, y))

        # merge trees
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                for p in [(x, y), (x + 0.5, y), (x, y + 0.5)]:
                    pivot = scene.to_scene_point(p)
                    items = scene.items(pivot)
                    merger_tree = None
                    for item in items:
                        if not item.is_edge(pivot):
                            continue
                        if merger_tree is None:
                            merger_tree = item
                    if merger_tree is not None:
                        for item in items:
                            if item is not merger_tree:
                                merger_tree.merge_tree(item)
                                scene.removeItem(item)

    def to_positions(self, scene, position_area):
        scene = GridScene()
        lines = position_area.split('\n')

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char in 'AX':
                    point_a = x, y
                if char in 'BX':
                    point_b = x, y

        return (scene.to_scene_point(point_a),
                scene.to_scene_point(point_b))

    def verify_output_data(self, scene, output_area):
        lines = output_area.split('\n')

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                pivot = scene.to_scene_point((x, y))
                items = scene.items(pivot)
                if char in 'x┴˄˅<┤├>┬-|┘┐┌└':
                    self.assertEqual(len(items), 1, (x, y))
                    self.assertIsInstance(items[0], LineTree)
                    self.assertEqual(items[0].is_edge(pivot),
                                     char in 'x┴˄˅<┤├>┬┘┐┌└')
                elif char in ['+']:
                    self.assertLessEqual(len(items), 2)
                    for item in items:
                        self.assertIsInstance(item, LineTree)
                        self.assertEqual(item.is_edge(pivot), False)

    def visual_test(self, input_area, position_area, output_area,
                    view_result=False):
        """
        Visual test case definition for inserting lines.

        Visual test cases are defined based on tree areas, basically
        strings defined as a block representing a two-dimensional grid:

        :param input_area: define lines for the starting scene
        :param position_area: define start and endpoint for inserting
        :param output_area: define output lines

        Lines are encoded with unicode characters: ┴˄˅<┤├>┬-|┘┐┌└:
            - horizontal peace, | vertical mid peace
            < left end, > right end, ˄ upper end, ˅ lower end
            + crossing lines, x intersecting lines
            ┤┬ ┘┐┌└ ┴├, corners

        Positions are given as A, B and X:
            A start, B end, X start and end

        When specifying the areas it is advisable to copy the input area,
        to the position area, then adding positions, then copy the result
        to the ouput area and add the added line.

        :param view_result: open scene with resulting grid for debugging

        """
        scene = GridScene()
        self.fill_scene(scene, input_area)
        start, end = self.to_positions(scene, position_area)
        line_route = LineRouteBetweenPoints(scene, start, end)
        line_route.route()
        line_route.do_insert()

        if view_result:
            import schematics.mouse_modes
            import sys
            from PySide import QtGui
            app = QtGui.QApplication.instance()
            if app is None:
                app = QtGui.QApplication(sys.argv)
            view = schematics.EditSchematicView()
            view.setScene(scene)
            view.show()
            view.ensureVisible(QtCore.QRectF(0, 0, 0, 0))
            view.setMouseMode(schematics.mouse_modes.InsertLineMode)
            app.exec_()

        self.verify_output_data(scene, output_area)

    def test_horizontal_line(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """



        """
        position_area = """

           A             B

        """
        output_area = """

           <------------->

        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_split_line(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """
           <----------->
        """
        position_area = """
           <----A------>



                B
        """
        output_area = """
           <----┬------>
                |
                |
                |
                ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_crossover_line(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """

           <----------->

        """
        position_area = """
                 A
           <----------->
                 B
        """
        output_area = """
                 ˄
           <-----+----->
                 ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_crossover_two_lines(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """

           <----------->
           <----------->
        """
        position_area = """"
                A
           <----------->
           <----B------>
        """
        output_area = """"
                ˄
           <----+------>
           <----┴------>
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_connected_crossover_two_lines(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """

           ┌----------->
           └----------->
        """
        position_area = """"
                A
           ┌----------->
           └----B------>
        """
        output_area = """"
                ˄
           ┌----+------>
           └----┴------>
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_route_accross_edge(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """
                 ┌----------->
                 |
           ┌-----┴------------>
           └----------->

        """
        position_area = """
                 ┌-----A----->
                 |
           ┌-----┴------------>
           └----------->
                       B
        """
        output_area = """
                 ┌----┬------>
                 |    |
           ┌-----┴----+------->
           └----------+>
                      └>
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_connecting_two_lines(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
           ˄        ˄
           |        |
           |        |
           |        |
           ˅        ˅
        """
        position_area = """
           ˄        ˄
           |        |
           A        B
           |        |
           ˅        ˅
        """
        output_area = """
           ˄        ˄
           |        |
           ├--------┤
           |        |
           ˅        ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_extend_over_corner(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
           <--------┐
                    |
                    |
                    |
                    ˅
        """
        position_area = """
           <---A----┐    B
                    |
                    |
                    |
                    ˅
        """
        output_area = """
           <--------┬---->
                    |
                    |
                    |
                    ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_extend_over_corner_swapped(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
           <--------┐
                    |
                    |
                    |
                    ˅
        """
        position_area = """
           <---B----┐    A
                    |
                    |
                    |
                    ˅
        """
        output_area = """
           <--------┬---->
                    |
                    |
                    |
                    ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_connect_passing_crossing_lines(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
              ˄
              |
           <--+-->
              |
              ˅
        """
        position_area = """
              ˄
              |
           <--X-->
              |
              ˅
        """
        output_area = """
              ˄
              |
           <--x-->
              |
              ˅
        """
        self.visual_test(input_area, position_area, output_area)

    def test_simple_route_accross_gap(self):
        # ┴˄˅<┤├>┬-|┘┐┌└
        input_area = """

           <------┐┌----->
                  └┘
        """
        position_area = """

           <---A--┐┌----->    B
                  └┘
        """
        output_area = """
               ┌--------------┐
           <---┴--┐┌----->    ˅
                  └┘
        """
        self.visual_test(input_area, position_area, output_area)
