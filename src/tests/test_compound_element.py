#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest

from backend.compound_element import CompoundElement
from backend.interconnect import Interconnect


class CompoundElementTest(unittest.TestCase):
    """
    Unit tests for compound element.
    """

    def test_pass_through(self):
        e = CompoundElement("pass")

        e.input_posts.connect(e.output_posts, 0, 1)
        e.input_posts.connect(e.output_posts, 2, 3)
        e.input_posts.connect(e.output_posts, 5, 6)

        ins = [Interconnect() for i in range(0, 6)]
        outs = [Interconnect() for i in range(0, 6)]

        for i in range(0, 6):
            ins[i].connect(e, input=i)
            e.connect(outs[i], i, 0)

        for i in range(0, 6):
            for e in ins[i].edge(0, 0, True):
                e.process()

        self.assertListEqual([False, True, False, True, False, False],
                             [outs[i].state for i in range(0, 6)])
