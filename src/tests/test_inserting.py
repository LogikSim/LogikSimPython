#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Test the scene logic for inserting lines.

(schematic -> mouse-mode -> line-submode -> inserting)
'''

import unittest

from PySide import QtCore, QtGui

from schematics.mouse_modes.line_submode.inserting import (
    GetHightowerObjectAtPoint, LineRouteBetweenPoints, EndpointTrees,
    RouteNotFoundException)
from schematics import GridScene
from algorithms import hightower
from logicitems import LineTree
from tests.helpers import wait_until_registry_enumerated


class TestHightowerObject(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication.instance()
        if not self.app:
            self.app = QtGui.QApplication([])

        self.scene = GridScene()

        # wait until all types have been enumerated
        wait_until_registry_enumerated(self.scene, self.app)

    def tearDown(self):
        # FIXME: No idea why this workaround is necessary :(
        self.scene.deleteLater()
        self.scene._core.quit()
        self.scene._core_thread.join()
        self.scene._registry._registry_handler.quit(True)
        self.scene = None

        self.app.processEvents()

    def test_empty_scene(self):
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(self.scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((10, 0)), None)
        self.assertIs(ho((0, 10)), None)
        self.assertIs(ho((10, 10)), None)

    def test_colision_add_item(self):
        and_item = self.scene.registry().instantiate_frontend_item(
            "7793F2A0-B313-4489-ABF3-8570ECDFE3EE")
        and_item.setPos(self.scene.to_scene_point((2, 2)))
        self.scene.addItem(and_item)
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(self.scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((10, 0)), None)

        self.assertIs(ho((2, 2)), hightower.Solid)

    def test_colision_line_tree(self):
        def tsp(x, y):
            return self.scene.to_scene_point((x, y))
        tree_meta = LineTree.metadata_from_path([tsp(5, 0), tsp(15, 0)])
        tree = LineTree(parent=None, metadata=tree_meta)
        self.scene.addItem(tree)
        trees = EndpointTrees(None, None)
        ho = GetHightowerObjectAtPoint(self.scene, (0, 0), (10, 10), trees)

        self.assertIs(ho((0, 0)), None)
        self.assertIs(ho((5, 5)), None)

        self.assertIs(ho((5, 0)), hightower.LineEdge)
        self.assertIs(ho((15, 0)), hightower.LineEdge)

        self.assertIs(ho((10, 0)), hightower.PassableLine)


class TestLineRoute(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication.instance()
        if not self.app:
            self.app = QtGui.QApplication([])

        self.scene = GridScene()

        # wait until all types have been enumerated
        wait_until_registry_enumerated(self.scene, self.app)

    def tearDown(self):
        # FIXME: No idea why this workaround is necessary :(
        self.scene.deleteLater()
        self.scene._core.quit()
        self.scene._core_thread.join()
        self.scene._registry._registry_handler.quit(True)
        self.scene = None

        self.app.processEvents()

    def test_horizontal_line(self):
        def tsp(x, y):
            return self.scene.to_scene_point((x, y))
        line_route = LineRouteBetweenPoints(self.scene,
                                            tsp(5, 10),
                                            tsp(15, 10))
        line_route.route()
        line_route.do_temp_insert()

        # check line count & temp
        trees = [item for item in self.scene.items() if isinstance(item,
                                                                   LineTree)]
        self.assertEqual(len(trees), 1)
        self.assertTrue(trees[0].is_temporary())

        # insert & check line count & temp
        line_route.do_insert()
        trees = [item for item in self.scene.items() if isinstance(item,
                                                                   LineTree)]
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
    def setUp(self):
        self.app = QtGui.QApplication.instance()
        if not self.app:
            self.app = QtGui.QApplication([])

        self.scene = GridScene()

        # wait until all types have been enumerated
        wait_until_registry_enumerated(self.scene, self.app)

    def tearDown(self):
        # FIXME: No idea why this workaround is necessary :(
        self.scene.deleteLater()
        self.scene._core.quit()
        self.scene._core_thread.join()
        self.scene._registry._registry_handler.quit(True)
        self.scene = None

        self.app.processEvents()

    def fill_scene(self, scene, input_area):
        lines = input_area.split('\n')

        def add_tree(p1, p2):
            path = [scene.to_scene_point(p1), scene.to_scene_point(p2)]
            metadata = LineTree.metadata_from_path(path)
            l_tree = self.scene.registry().instantiate_frontend_item(
                backend_guid=LineTree.GUI_GUID(),
                additional_metadata=metadata)
            scene.addItem(l_tree)

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
                    items = [item for item in scene.items(pivot)
                             if isinstance(item, LineTree)]
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
                items = [item for item in scene.items(pivot)
                         if isinstance(item, LineTree)]
                if char in 'x┴˄˅<┤├>┬-|┘┐┌└':
                    self.assertEqual(len(items), 1, (x, y))
                    self.assertEqual(items[0].is_edge(pivot),
                                     char in 'x┴˄˅<┤├>┬┘┐┌└')
                elif char in ['+']:
                    self.assertLessEqual(len(items), 2)
                    for item in items:
                        self.assertEqual(item.is_edge(pivot), False)
                else:
                    self.assertEqual(len(items), 0)

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
        self.fill_scene(self.scene, input_area)
        start, end = self.to_positions(self.scene, position_area)
        line_route = LineRouteBetweenPoints(self.scene, start, end)
        try:
            line_route.route()
        except RouteNotFoundException:
            pass
        line_route.do_insert()

        if view_result:
            import schematics.mouse_modes
            import sys
            from PySide import QtGui
            app = QtGui.QApplication.instance()
            if app is None:
                app = QtGui.QApplication(sys.argv)
            view = schematics.EditSchematicView()
            view.setScene(self.scene)
            view.show()
            view.ensureVisible(QtCore.QRectF(0, 0, 0, 0))
            view.setMouseMode(schematics.mouse_modes.InsertLineMode)
            app.exec_()

        self.verify_output_data(self.scene, output_area)

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

    def test_extend_over_two_corners(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
           <--------┬-----┐
                    |     |
                    |     |
                    |     |
                    ˅     ˅
        """
        position_area = """
           <---A----┬-----┐     B
                    |     |
                    |     |
                    |     |
                    ˅     ˅
        """
        output_area = """
           <--------┬-----┬----->
                    |     |
                    |     |
                    |     |
                    ˅     ˅
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

    def test_try_route_from_passing_crossing_lines(self):
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
        B  <--A-->
              |
              ˅
        """
        output_area = """
              ˄
              |
           <--+-->
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

    def test_try_route_loop(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
            ┌-----┐
            |     |
            |     |
            |     |
            ˅     ˅
        """
        position_area = """
            ┌-----┐
            |     |
            A     B
            |     |
            ˅     ˅
        """
        output_area = """
            ┌-----┐
            |     |
            |     |
            |     |
            ˅     ˅
        """
        self.visual_test(input_area, position_area, output_area)

    @unittest.expectedFailure
    def test_verifyer(self):
        # ┴˄˅<┤├>┬-|┘┐┌└|
        input_area = """
            <----->
        """
        position_area = """
            A-----B
        """
        output_area = """
                 ->
        """
        self.visual_test(input_area, position_area, output_area)
