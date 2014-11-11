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

from logicitems.linetree import LineTree


class LineTreeTest(unittest.TestCase):
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
        
    