#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest
from backend.simple_element import OutEdge
from backend.basic_logic_elements import And, Or


class BasicLogicElementTest(unittest.TestCase):
    """
    Unit tests for basic logic elements.
    """

    def test_and(self):
        # Create two pin and
        e = And()
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Rising edge on pin 0
        events = e.edge(0, 0, True)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(1, e, 0, False)], events)
        events[0].process()

        self.assertSequenceEqual((0,), e.output_states)
        self.assertSequenceEqual((1, 0), e.input_states)

        # Rising edge on pin 1
        events = e.edge(2, 1, True)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(3, e, 0, True)], events)
        events[0].process()

        self.assertSequenceEqual((1, 1), e.input_states)
        self.assertSequenceEqual((1,), e.output_states)

        # Falling edge on pin 0
        events = e.edge(10, 0, False)
        self.assertSequenceEqual((1,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(11, e, 0, False)], events)
        events[0].process()

        self.assertSequenceEqual((0,), e.output_states)
        self.assertSequenceEqual((0, 1), e.input_states)

    def test_or(self):
        # Create two pin or
        e = Or()
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)

        # Rising edge on pin 0
        events = e.edge(0, 0, True)
        self.assertSequenceEqual((0,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(1, e, 0, True)], events)
        events[0].process()

        self.assertSequenceEqual((1,), e.output_states)
        self.assertSequenceEqual((1, 0), e.input_states)

        # Rising edge on pin 1
        events = e.edge(3, 1, True)
        self.assertSequenceEqual((1,), e.output_states)  # Verify is delayed
        self.assertListEqual([OutEdge(4, e, 0, True)], events)
        events[0].process()

        self.assertSequenceEqual((1, 1), e.input_states)
        self.assertSequenceEqual((1,), e.output_states)

        # Falling edge on pin 0 and 1
        e.edge(10, 0, False)[0].process()
        self.assertSequenceEqual((1,), e.output_states)

        e.edge(10, 1, False)[0].process()
        self.assertSequenceEqual((0, 0), e.input_states)
        self.assertSequenceEqual((0,), e.output_states)
