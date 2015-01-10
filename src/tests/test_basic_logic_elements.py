#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from tests.mocks import ElementRootMock
from backend.simple_element import OutEdge
from backend.components.basic_logic_elements import And, Or, Xor
from tests import helpers


class BasicLogicElementTest(helpers.CriticalTestCase):
    """
    Unit tests for basic logic elements.
    """

    def test_and(self):
        p = ElementRootMock()
        # Create two pin and
        e = And.instantiate(0, p)
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Rising edge on pin 0
        e.edge(0, True)
        events = e.clock(0)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(1, e, 0, False)], events)
        events[0].process(True)

        self.assertSequenceEqual((0,), e.output_states)
        self.assertSequenceEqual((1, 0), e.input_states)

        # Rising edge on pin 1
        e.edge(1, True)
        events = e.clock(2)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(3, e, 0, True)], events)
        events[0].process(True)

        self.assertSequenceEqual((1, 1), e.input_states)
        self.assertSequenceEqual((1,), e.output_states)

        # Falling edge on pin 0
        events = e.edge(0, False)
        events = e.clock(10)
        self.assertSequenceEqual((1,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(11, e, 0, False)], events)
        events[0].process(True)

        self.assertSequenceEqual((0,), e.output_states)
        self.assertSequenceEqual((0, 1), e.input_states)

    def test_or(self):
        p = ElementRootMock()
        # Create two pin or
        e = Or.instantiate(0, p)
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Rising edge on pin 0
        e.edge(0, True)
        events = e.clock(0)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(1, e, 0, True)], events)
        events[0].process(True)

        self.assertSequenceEqual((1,), e.output_states)
        self.assertSequenceEqual((1, 0), e.input_states)

        # Rising edge on pin 1
        e.edge(1, True)
        self.assertSequenceEqual((1,), e.output_states)  # Verify is delayed
        # NOP self.assertListEqual([OutEdge(4, e, 0, True)], events)
        # events[0].process()

        self.assertSequenceEqual((1, 1), e.input_states)
        self.assertSequenceEqual((1,), e.output_states)

        # Falling edge on pin 0 and 1
        e.edge(0, False)
        e.clock(10)[0].process(True)
        self.assertSequenceEqual((1,), e.output_states)

        e.edge(1, False)
        e.clock(11)[0].process(True)
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

    def test_xor(self):
        p = ElementRootMock()
        # Create two pin or
        e = Xor.instantiate(0, p)
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Rising edge on pin 0
        e.edge(0, True)
        events = e.clock(0)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(1, e, 0, True)], events)
        events[0].process(True)

        self.assertSequenceEqual((1,), e.output_states)
        self.assertSequenceEqual((1, 0), e.input_states)

        # Rising edge on pin 1
        e.edge(1, True)
        events = e.clock(3)
        self.assertSequenceEqual((1,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(4, e, 0, False)], events)
        events[0].process(True)

        self.assertSequenceEqual((1, 1), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Falling edge on pin 0 and 1
        e.edge(0, False)
        e.clock(10)[0].process(True)
        self.assertSequenceEqual((1,), e.output_states)

        e.edge(1, False)
        e.clock(11)[0].process(True)
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)
