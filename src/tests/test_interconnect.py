#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
import unittest
from backend.interconnect import Interconnect
from backend.element import Edge
from helpers import CallTrack


class InterconnectTest(unittest.TestCase):
    """
    Unit tests for interconnect
    """

    def test_empty_interconnect(self):
        empty = Interconnect()
        self.assertListEqual([], empty.edge(0, 0, True))

    def test_edge_forward(self):
        i = Interconnect()

        class Foo: pass
        a = Foo()
        b = Foo()

        i.add_connection(a, 0)
        i.add_connection(b, 2, 10)

        self.assertListEqual([Edge(1, a, 0, False),
                              Edge(10, b, 2, False)],
                             i.edge(0, 0, False))

        self.assertListEqual([Edge(11, a, 0, True),
                              Edge(20, b, 2, True)],
                             i.edge(10, 0, True))
