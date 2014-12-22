#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
import unittest

from backend.components.interconnect import Interconnect
from backend.element import Edge
from tests.mocks import ElementParentMock


class InterconnectTest(unittest.TestCase):
    """
    Unit tests for interconnect
    """

    def test_empty_interconnect(self):
        p = ElementParentMock()
        empty = Interconnect.instantiate(0, p)
        empty.edge(0, True)
        self.assertListEqual([], empty.clock(0))
        self.assertTrue(empty.state)

    def test_edge_forward(self):
        p = ElementParentMock()
        i = Interconnect.instantiate(0, p)

        class Foo:
            pass

        a = Foo()
        b = Foo()

        i.connect(a, input=0)
        i.connect(b, input=2, connection_length=10)

        i.edge(0, False)
        self.assertListEqual([Edge(1, a, 0, False),
                              Edge(10, b, 2, False)],
                             i.clock(0))
        self.assertFalse(i.state)

        i.edge(0, True)
        self.assertListEqual([Edge(11, a, 0, True),
                              Edge(20, b, 2, True)],
                             i.clock(10))
        self.assertTrue(i.state)
