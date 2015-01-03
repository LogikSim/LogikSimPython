#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 The LogikSim Authors. All rights reserved.
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
from tests.helpers import wait_until_registry_enumerated


def linetree_from_path(path):
    """Create LineTree from path."""
    metadata = LineTree.metadata_from_path(path)
    return LineTree(parent=None, metadata=metadata)


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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
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
        hor_tree = linetree_from_path([QtCore.QPointF(0, 0),
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
        ver_tree = linetree_from_path([QtCore.QPointF(0, 0),
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
        ver_tree = linetree_from_path([QtCore.QPointF(0, 0),
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

    def test_nearest_point_horizontal(self):
        def tsp(x, y):
            return self.scene.to_scene_point((x, y))
        hor_tree = linetree_from_path([tsp(0, 0), tsp(10, 0)])
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
        hor_tree = linetree_from_path([tsp(0, 0), tsp(0, 10)])
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(5, 0),
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
        tree = linetree_from_path([QtCore.QPointF(0, 10),
                                   QtCore.QPointF(0, 20)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(0, 0),
                                            QtCore.QPointF(0, 10)]))
        tree.merge_tree(linetree_from_path([QtCore.QPointF(0, 20),
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(10, 10)]))

        tree_m = linetree_from_path([QtCore.QPointF(5, 0),
                                     QtCore.QPointF(5, 5)])
        tree_m.merge_tree(linetree_from_path([QtCore.QPointF(5, 5),
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(10, 10)]))
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(20, 0)]))
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
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
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(20, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(10, 0)]))
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, -10),
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
        tree_a = linetree_from_path([QtCore.QPointF(0, 0),
                                     QtCore.QPointF(10, 0)])
        tree_a.merge_tree(linetree_from_path([QtCore.QPointF(5, 0),
                                              QtCore.QPointF(5, 10)]))

        tree_b = linetree_from_path([QtCore.QPointF(0, 5),
                                     QtCore.QPointF(0, 15)])
        tree_b.merge_tree(linetree_from_path([QtCore.QPointF(0, 10),
                                              QtCore.QPointF(10, 10)]))

        tree_c = linetree_from_path([QtCore.QPointF(-10, 0),
                                     QtCore.QPointF(-10, 15)])
        tree_c.merge_tree(linetree_from_path([QtCore.QPointF(-10, 10),
                                              QtCore.QPointF(0, 10)]))

        tree_d = linetree_from_path([QtCore.QPointF(3, 10),
                                     QtCore.QPointF(3, 20)])
        tree_d.merge_tree(linetree_from_path([QtCore.QPointF(0, 20),
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


class LineLengthToTest(unittest.TestCase):
    def test_horizontal_line(self):
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0)])
        tree._set_tree(tree._reroot(tree._tree, (0, 0)))

        self.assertEqual(tree._length_to((0, 0)), 0)
        self.assertEqual(tree._length_to((10, 0)), 10)
        self.assertEqual(tree._length_to((5, 0)), 5)

    def test_vertical_line(self):
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(0, 10)])
        tree._set_tree(tree._reroot(tree._tree, (0, 0)))

        self.assertEqual(tree._length_to((0, 0)), 0)
        self.assertEqual(tree._length_to((0, 10)), 10)
        self.assertEqual(tree._length_to((0, 5)), 5)

    def test_path_line(self):
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(10, 0),
                                   QtCore.QPointF(10, 10),
                                   QtCore.QPointF(20, 10)])
        tree._set_tree(tree._reroot(tree._tree, (10, 0)))

        self.assertEqual(tree._length_to((0, 0)), 10)
        self.assertEqual(tree._length_to((10, 0)), 0)
        self.assertEqual(tree._length_to((5, 0)), 5)

        self.assertEqual(tree._length_to((10, 10)), 10)
        self.assertEqual(tree._length_to((10, 5)), 5)

        self.assertEqual(tree._length_to((20, 10)), 20)
        self.assertEqual(tree._length_to((15, 10)), 15)

    def test_merged_tree(self):
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(20, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(10, 10)]))
        tree._set_tree(tree._reroot(tree._tree, (0, 0)))

        self.assertEqual(tree._length_to((0, 0)), 0)
        self.assertEqual(tree._length_to((10, 0)), 10)
        self.assertEqual(tree._length_to((5, 0)), 5)

        self.assertEqual(tree._length_to((20, 0)), 20)
        self.assertEqual(tree._length_to((15, 0)), 15)

        self.assertEqual(tree._length_to((10, 10)), 20)
        self.assertEqual(tree._length_to((10, 5)), 15)

    def test_nonexisting_tree(self):
        tree = linetree_from_path([QtCore.QPointF(0, 0),
                                   QtCore.QPointF(20, 0)])
        tree.merge_tree(linetree_from_path([QtCore.QPointF(10, 0),
                                            QtCore.QPointF(10, 10)]))
        tree._set_tree(tree._reroot(tree._tree, (0, 0)))

        self.assertRaises(Exception, tree._length_to, (20, 20))


def get_linetree_with_states(tree, states, curr_clock, grid_spacing=1,
                             delay_per_gridpoint=1):
    """
    :param tree: tree dict
    :param states: list of (time, value)
    :param curr_clock: current simulation clock
    :param grid_spacing: spacing of the grid
    """
    class dummy:
        pass

    tree = LineTree(None, {'tree': tree})
    tree._delay_per_gridpoint = delay_per_gridpoint

    # setup scene
    scene_obj = dummy()

    def scene():
        return scene_obj
    tree.scene = scene
    registry_obj = dummy()

    def registry():
        return registry_obj
    tree.scene().registry = registry

    def get_grid_spacing():
        return grid_spacing
    tree.scene().get_grid_spacing = get_grid_spacing

    # feed with states
    for clock, state in states:
        def get_clock():
            return clock
        tree.scene().registry().clock = get_clock
        tree.update({'state': state})

    # set current clock
    def get_curr_clock():
        return curr_clock
    tree.scene().registry().clock = get_curr_clock
    return tree


class StateLineSegmentationTest(unittest.TestCase):
    def test_horizontal_line_partial_start(self):
        tree = get_linetree_with_states(
            {(0, 0): {(10, 0): {}}},
            [(0, False), (1, True), (2, False), (5, True)],
            curr_clock=5)

        self.assertListEqual(list(tree.iter_state_line_segments()),
                             [(QtCore.QLineF(0, 0, 3, 0), False),
                              (QtCore.QLineF(3, 0, 4, 0), True),
                              (QtCore.QLineF(4, 0, 5, 0), False),
                              (QtCore.QLineF(5, 0, 10, 0), False)])

    def test_horizontal_line_startup(self):
        tree = get_linetree_with_states({(0, 0): {(10, 0): {}}},
                                        [], curr_clock=0)

        self.assertListEqual(list(tree.iter_state_line_segments()),
                             [(QtCore.QLineF(0, 0, 10, 0), False)])

    def test_horizontal_line_full_simulation(self):
        tree = get_linetree_with_states(
            {(0, 0): {(10, 0): {}}},
            [(0, False), (3, True), (7, False), (10, True)],
            curr_clock=12)

        self.assertListEqual(list(tree.iter_state_line_segments()),
                             [(QtCore.QLineF(0, 0, 2, 0), True),
                              (QtCore.QLineF(2, 0, 5, 0), False),
                              (QtCore.QLineF(5, 0, 9, 0), True),
                              (QtCore.QLineF(9, 0, 10, 0), False)])

    def test_path_line_full_simulation(self):
        tree = get_linetree_with_states(
            {(0, 0): {(10, 0): {(10, 10): {}}}},
            [(0, False), (3, True), (7, False), (10, True),
             (14, False), (17, True), (18, False), (21, True)],
            curr_clock=22)

        self.assertListEqual(list(tree.iter_state_line_segments()),
                             [(QtCore.QLineF(0, 0, 1, 0), True),
                              (QtCore.QLineF(1, 0, 4, 0), False),
                              (QtCore.QLineF(4, 0, 5, 0), True),
                              (QtCore.QLineF(5, 0, 8, 0), False),
                              (QtCore.QLineF(8, 0, 10, 0), True),
                              (QtCore.QLineF(10, 0, 10, 2), True),
                              (QtCore.QLineF(10, 2, 10, 5), False),
                              (QtCore.QLineF(10, 5, 10, 9), True),
                              (QtCore.QLineF(10, 9, 10, 10), False)])

    def test_tree_full_simulation(self):
        tree = get_linetree_with_states(
            {(0, 0): {(10, 0): {(10, 10): {}, (20, 0): {}}, (0, 10): {}}},
            [(0, True), (15, False), (25, True)],
            curr_clock=30)

        def to_set(iterator):
            res = set({})
            for line, state in iterator:
                res.add((line.toTuple(), state))
            return res

        self.assertSetEqual(to_set(tree.iter_state_line_segments()),
                            to_set([(QtCore.QLineF(0, 0, 5, 0), True),
                                    (QtCore.QLineF(0, 0, 0, 5), True),
                                    (QtCore.QLineF(5, 0, 10, 0), False),
                                    (QtCore.QLineF(0, 5, 0, 10), False),

                                    (QtCore.QLineF(10, 0, 15, 0), False),
                                    (QtCore.QLineF(10, 0, 10, 5), False),
                                    (QtCore.QLineF(15, 0, 20, 0), True),
                                    (QtCore.QLineF(10, 5, 10, 10), True)]))
