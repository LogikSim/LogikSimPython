#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from backend.components.compound_element import CompoundElement
from backend.components.interconnect import Interconnect
from backend.component_library import get_library
from tests.mocks import ElementRootMock
from tests import helpers


class CompoundElementTest(helpers.CriticalTestCase):
    """
    Unit tests for compound element.
    """

    def test_pass_through(self):
        p = ElementRootMock(get_library())
        e = CompoundElement.instantiate(0, p)

        e.input_bank.connect(0, e.output_bank, 1)
        e.input_bank.connect(2, e.output_bank, 3)
        e.input_bank.connect(5, e.output_bank, 6)

        ins = [Interconnect.instantiate(i, p) for i in range(0, 6)]
        outs = [Interconnect.instantiate(i * 10, p) for i in range(0, 6)]

        for i in range(0, 6):
            ins[i].connect(output_port=i, element=e, input_port=i)
            e.connect(i, outs[i], 0)

        for i in range(0, 6):
            ins[i].edge(0, True)
            for e in ins[i].clock(0):
                e.process(True)

        self.assertListEqual([False, True, False, True, False, False],
                             [outs[i].state for i in range(0, 6)])
