#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
import unittest

from backend.components.interconnect import Interconnect
from backend.element import Edge
from tests.mocks import ElementRootMock


class InterconnectTest(unittest.TestCase):
    """
    Unit tests for interconnect
    """

    def test_empty_interconnect(self):
        p = ElementRootMock()
        empty = Interconnect.instantiate(0, p)
        empty.edge(0, True)
        self.assertListEqual([], empty.clock(0))
        self.assertTrue(empty.state)

    def test_edge_forward(self):
        p = ElementRootMock()
        i = Interconnect.instantiate(0, p)

        class Foo:
            def id(self):
                return 0

            def connected(self, *args, **argv):
                return True

        a = Foo()
        b = Foo()

        self.assertTrue(i.connect(a, input_port=0, output_port=0, delay=1))
        self.assertTrue(i.connect(b, input_port=2, output_port=1, delay=10))

        i.edge(0, True)
        self.assertListEqual([Edge(1, a, 0, True),
                              Edge(10, b, 2, True)],
                             i.clock(0))

        self.assertTrue(i.state)

        i.edge(0, False)
        self.assertListEqual([Edge(11, a, 0, False),
                              Edge(20, b, 2, False)],
                             i.clock(10))
        self.assertFalse(i.state)
