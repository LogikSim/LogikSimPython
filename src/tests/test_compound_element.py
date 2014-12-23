#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest

from backend.components.compound_element import CompoundElement
from backend.components.interconnect import Interconnect
from backend.component_library import get_library
from tests.mocks import ElementParentMock


class CompoundElementTest(unittest.TestCase):
    """
    Unit tests for compound element.
    """

    def test_pass_through(self):
        p = ElementParentMock(get_library())
        e = CompoundElement.instantiate(0, p)

        e.input_bank.connect(e.output_bank, 0, 1)
        e.input_bank.connect(e.output_bank, 2, 3)
        e.input_bank.connect(e.output_bank, 5, 6)

        ins = [Interconnect.instantiate(i, p) for i in range(0, 6)]
        outs = [Interconnect.instantiate(i*10, p) for i in range(0, 6)]

        for i in range(0, 6):
            ins[i].connect(e, input=i)
            e.connect(outs[i], i, 0)

        for i in range(0, 6):
            ins[i].edge(0, True)
            for e in ins[i].clock(0):
                e.process(False)

        self.assertListEqual([False, True, False, True, False, False],
                             [outs[i].state for i in range(0, 6)])
