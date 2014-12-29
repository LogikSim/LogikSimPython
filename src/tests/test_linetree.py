#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Test the LineTree implementation.
'''

import unittest

from PySide import QtCore, QtGui

from logicitems.linetree import LineTree
from schematics import GridScene


class LineTreeRerootTest(unittest.TestCase):
    def test_reroot_path_3(self):
        tree = {1: {2: {3: {}}}}
        n_tree = LineTree._reroot(tree, 2)
        r_tree = {2: {1: {}, 3: {}}}
        self.assertEqual(n_tree, r_tree)

    def test_reroot_path_5(self):
        tree = {1: {2: {3: {4: {5: {}}}}}}
        n_tree = LineTree._reroot(tree, 3)
        r_tree = {3: {2: {1: {}}, 4: {5: {}}}}
        self.assertEqual(n_tree, r_tree)

    def test_reroot_tree_two_childs(self):
        tree = {1: {11: {},
                    12: {}}}
        n_tree = LineTree._reroot(tree, 11)
        r_tree = {11: {1: {12: {}}}}
        self.assertEqual(n_tree, r_tree)

    def test_reroot_tree_tree_childs(self):
        tree = {1: {11: {},
                    12: {},
                    13: {}}}
        n_tree = LineTree._reroot(tree, 11)
        r_tree = {11: {1: {12: {},
                           13: {}}}}
        self.assertEqual(n_tree, r_tree)

    def test_reroot_tree_complex(self):
        tree = {1: {11: {111: {},
                         112: {}},
                    12: {121: {1211: {},
                               1212: {}},
                         122: {}},
                    13: {}}}
        n_tree = LineTree._reroot(tree, 121)
        r_tree = {121: {1211: {},
                        1212: {},
                        12: {122: {},
                             1: {11: {111: {},
                                      112: {}},
                                 13: {}}}}}
        self.assertEqual(n_tree, r_tree)

    def test_reroot_tree_complex_sameroot(self):
        tree = {1: {11: {111: {},
                         112: {}},
                    12: {121: {1211: {},
                               1212: {}},
                         122: {}},
                    13: {}}}
        n_tree = LineTree._reroot(tree, 1)
        self.assertEqual(n_tree, tree)


class LineTreeGeneralTest(unittest.TestCase):
    def test_is_edge(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])

        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(1, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(9, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(11, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(15, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 1)))

    def test_contains_hor_line(self):
        hor_tree = LineTree([QtCore.QPointF(0, 0),
                             QtCore.QPointF(10, 0)])

        self.assertTrue(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(3, 0), QtCore.QPointF(7, 0))))
        self.assertTrue(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(7, 0), QtCore.QPointF(3, 0))))
        self.assertTrue(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))))
        self.assertTrue(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 0), QtCore.QPointF(0, 0))))

        self.assertFalse(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(11, 0))))
        self.assertFalse(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(-1, 0), QtCore.QPointF(0, 0))))
        self.assertFalse(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(20, 0), QtCore.QPointF(25, 0))))
        self.assertFalse(hor_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 1), QtCore.QPointF(10, 1))))

    def test_contains_ver_line(self):
        ver_tree = LineTree([QtCore.QPointF(0, 0),
                             QtCore.QPointF(0, 10)])

        self.assertTrue(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 3), QtCore.QPointF(0, 7))))
        self.assertTrue(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 7), QtCore.QPointF(0, 3))))
        self.assertTrue(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(0, 10))))
        self.assertTrue(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 10), QtCore.QPointF(0, 0))))

        self.assertFalse(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(0, 11))))
        self.assertFalse(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, -1), QtCore.QPointF(0, 0))))
        self.assertFalse(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 20), QtCore.QPointF(0, 25))))
        self.assertFalse(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(1, 0), QtCore.QPointF(1, 10))))

    def test_contains_hor_gap(self):
        ver_tree = LineTree([QtCore.QPointF(0, 0),
                             QtCore.QPointF(0, 10),
                             QtCore.QPointF(1, 10),
                             QtCore.QPointF(1, 11),
                             QtCore.QPointF(0, 11),
                             QtCore.QPointF(0, 20)])

        self.assertTrue(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 3), QtCore.QPointF(0, 7))))

        self.assertFalse(ver_tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 5), QtCore.QPointF(0, 15))))


class LineNearestPointTest(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication.instance()
        if not self.app:
            self.app = QtGui.QApplication([])

        self.scene = GridScene()

    def tearDown(self):
        # FIXME: No idea why this workaround is necessary :(
        self.scene.deleteLater()
        self.scene._core.quit()
        self.scene._core_thread.join()
        self.scene._registry._registry_handler.quit(True)
        self.scene = None

        self.app.processEvents()

    def test_nearest_point_horizontal(self):
        def tsp(x, y):
            return self.scene.to_scene_point((x, y))
        hor_tree = LineTree([tsp(0, 0), tsp(10, 0)])
        self.scene.addItem(hor_tree)

        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, 0)), tsp(0, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(5, 0)), tsp(5, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(10, 0)), tsp(10, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(1.3, 0)), tsp(1, 0))

        self.assertEqual(
            hor_tree.get_nearest_point(tsp(5, 1)), tsp(5, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(5, 100)), tsp(5, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(-10, 0)), tsp(0, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(-10, 10)), tsp(0, 0))

    def test_nearest_point_vertical(self):
        def tsp(x, y):
            return self.scene.to_scene_point((x, y))
        hor_tree = LineTree([tsp(0, 0), tsp(0, 10)])
        self.scene.addItem(hor_tree)

        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, 0)), tsp(0, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, 5)), tsp(0, 5))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, 10)), tsp(0, 10))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, 1.3)), tsp(0, 1))

        self.assertEqual(
            hor_tree.get_nearest_point(tsp(1, 5)), tsp(0, 5))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(100, 5)), tsp(0, 5))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(0, -10)), tsp(0, 0))
        self.assertEqual(
            hor_tree.get_nearest_point(tsp(10, -10)), tsp(0, 0))


class LineMergeRegressionTest(unittest.TestCase):
    """Merge test not relying on introspecting inner states."""
    def test_simple_corner(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(10, 10)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 10)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 5)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 5)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(3, 0), QtCore.QPointF(7, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(7, 0), QtCore.QPointF(3, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 0), QtCore.QPointF(0, 0))))

        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 3), QtCore.QPointF(10, 7))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 7), QtCore.QPointF(10, 3))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 0), QtCore.QPointF(10, 10))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 10), QtCore.QPointF(10, 0))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(11, 0))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(-1, 0), QtCore.QPointF(0, 0))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(20, 0), QtCore.QPointF(25, 0))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 1), QtCore.QPointF(10, 1))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 0), QtCore.QPointF(10, 11))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, -1), QtCore.QPointF(10, 0))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, 20), QtCore.QPointF(10, 25))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(11, 0), QtCore.QPointF(11, 10))))

    def test_horizontal_merge(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(20, 0)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(20, 0)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 5)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 5)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(20, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(5, 0), QtCore.QPointF(20, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(15, 0))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(30, 0))))

    def test_split_merge(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(5, 0),
                                  QtCore.QPointF(5, 10)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 10)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(3, 0)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 5)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 5)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(10, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(5, 0), QtCore.QPointF(10, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(5, 0), QtCore.QPointF(5, 10))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(5, 2), QtCore.QPointF(5, 7))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(30, 0))))
        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(5, 0), QtCore.QPointF(5, 15))))

    def test_two_sided_vertical_merge(self):
        tree = LineTree([QtCore.QPointF(0, 10),
                         QtCore.QPointF(0, 20)])
        tree.merge_tree(LineTree([QtCore.QPointF(0, 0),
                                  QtCore.QPointF(0, 10)]))
        tree.merge_tree(LineTree([QtCore.QPointF(0, 20),
                                  QtCore.QPointF(0, 30)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 30)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 10)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 20)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(0, 30))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(40, 0))))

    def test_pass_crossing_merge(self):
        """Lines crossing, without being merged"""
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(10, 10)]))

        tree_m = LineTree([QtCore.QPointF(5, 0),
                           QtCore.QPointF(5, 5)])
        tree_m.merge_tree(LineTree([QtCore.QPointF(5, 5),
                                    QtCore.QPointF(15, 5)]))

        tree.merge_tree(tree_m)

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 10)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 5)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(15, 5)))
        self.assertFalse(tree.is_edge(QtCore.QPointF(10, 5)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 10)))

    def test_four_crossing_merge(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(10, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(10, 10)]))
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(20, 0)]))
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(10, -10)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 10)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(20, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, -10)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 10)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(20, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, -10), QtCore.QPointF(10, 10))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(40, 0))))

    def test_split_crossing_lines(self):
        tree = LineTree([QtCore.QPointF(0, 0),
                         QtCore.QPointF(20, 0)])
        tree.merge_tree(LineTree([QtCore.QPointF(10, 0),
                                  QtCore.QPointF(10, 0)]))
        tree.merge_tree(LineTree([QtCore.QPointF(10, -10),
                                  QtCore.QPointF(10, 10)]))

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, 10)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(20, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(10, -10)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(0, 10)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(20, 0))))
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(10, -10), QtCore.QPointF(10, 10))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(40, 0))))

    def test_split_complex_trees(self):
        tree_a = LineTree([QtCore.QPointF(0, 0),
                           QtCore.QPointF(10, 0)])
        tree_a.merge_tree(LineTree([QtCore.QPointF(5, 0),
                                    QtCore.QPointF(5, 10)]))

        tree_b = LineTree([QtCore.QPointF(0, 5),
                           QtCore.QPointF(0, 15)])
        tree_b.merge_tree(LineTree([QtCore.QPointF(0, 10),
                                    QtCore.QPointF(10, 10)]))

        tree_c = LineTree([QtCore.QPointF(-10, 0),
                           QtCore.QPointF(-10, 15)])
        tree_c.merge_tree(LineTree([QtCore.QPointF(-10, 10),
                                    QtCore.QPointF(0, 10)]))

        tree_d = LineTree([QtCore.QPointF(3, 10),
                           QtCore.QPointF(3, 20)])
        tree_d.merge_tree(LineTree([QtCore.QPointF(0, 20),
                                    QtCore.QPointF(10, 20)]))

        tree_b.merge_tree(tree_a)
        tree_b.merge_tree(tree_c)
        tree_b.merge_tree(tree_d)
        tree = tree_b

        # check edges
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 0)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(5, 10)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(0, 10)))
        self.assertTrue(tree.is_edge(QtCore.QPointF(3, 10)))

        self.assertFalse(tree.is_edge(QtCore.QPointF(5, 5)))

        # contains line
        self.assertTrue(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(-10, 10), QtCore.QPointF(10, 10))))

        self.assertFalse(tree.contains_line(QtCore.QLineF(
            QtCore.QPointF(0, 0), QtCore.QPointF(40, 0))))
