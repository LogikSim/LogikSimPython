#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest
from backend.core import Core
from backend.event import Event
from backend.basic_logic_elements import Xor, And, Nor, Or
from backend.compound_element import CompoundElement
from backend.element import Edge
from backend.interconnect import Interconnect
from tests.helpers import CallTrack


class TestingCore(Core):
    def __init__(self):
        super().__init__()
        self.timeline = []

    def loop_until_stable_state_or_time(self, time=None):
        while not self.queue.empty():
            if time is not None and self.queue.queue[0].when >= time:
                return time

            event = self._process_next_event()
            self.timeline.append((self.clock, event))

        return self.clock


def build_halfadder(name):
    a = Interconnect()
    b = Interconnect()

    xor_gate = Xor()
    and_gate = And()

    a.connect(xor_gate)
    a.connect(and_gate)

    b.connect(xor_gate, input=1)
    b.connect(and_gate, input=1)

    half_adder = CompoundElement(name)
    half_adder.input_posts.connect(a, 0)
    half_adder.input_posts.connect(b, 1)

    xor_gate.connect(half_adder.output_posts, 0, 0)  # Sum on out 0
    and_gate.connect(half_adder.output_posts, 0, 1)  # Carry on out 1

    return half_adder


def build_fulladder(name):
    ha1 = build_halfadder(name+"_ha1")
    ha2 = build_halfadder(name+"_ha2")

    full_adder = CompoundElement(name)
    full_adder.input_posts.connect(ha1, 0, 0)  # A input on 0
    full_adder.input_posts.connect(ha1, 1, 1)  # B input on 1
    ha1.connect(ha2, 0, 0)
    full_adder.input_posts.connect(ha2, 2, 1)  # Carry input on 2

    or_gate = Or()
    ha1.connect(or_gate, 1, 0)  # ha1 carry on or
    ha2.connect(or_gate, 1, 1)  # ha2 carry on or

    ha2.connect(full_adder.output_posts, 0, 0)  # Sum on out 0
    or_gate.connect(full_adder.output_posts, 0, 1)  # Carry on out 1

    return full_adder


class BackendCoreTest(unittest.TestCase):
    """
    Unit tests for backend core including some element integration tests.
    """

    def test_priority_queue(self):
        c = TestingCore()  # We don't start the process. That would be messy

        ct = CallTrack(result_fu=lambda: [])
        ct2 = CallTrack(result_fu=lambda: [])

        e1 = Event(10, ct.slot)
        e2 = Event(100, ct2.slot)
        c.schedule(e1)
        c.schedule(e2)

        c.loop_until_stable_state_or_time()

        self.assertListEqual([(10, e1), (100, e2)], c.timeline)
        self.assertListEqual([()], ct())
        self.assertListEqual([()], ct2())

    def test_element_behavior(self):
        # Build a simple half-adder
        a = Interconnect()
        b = Interconnect()

        s = Interconnect()
        c = Interconnect()

        xor_gate = Xor()
        and_gate = And()

        a.connect(xor_gate)
        a.connect(and_gate)

        b.connect(xor_gate, input=1)
        b.connect(and_gate, input=1)

        xor_gate.connect(s)
        and_gate.connect(c)

        core = TestingCore()  # We don't start the process. That would be messy

        core.schedule(Edge(10, a, 0, True))
        core.schedule(Edge(15, b, 0, True))

        core.loop_until_stable_state_or_time(11)  # Expect a 2 time unit delay
        self.assertFalse(s.state)
        self.assertFalse(c.state)

        core.loop_until_stable_state_or_time(13)  # First should've propagated
        self.assertTrue(s.state)
        self.assertFalse(c.state)

        core.loop_until_stable_state_or_time()  # Run till end
        self.assertFalse(s.state)
        self.assertTrue(c.state)

    def test_compound_element_behavior(self):
        # Test the half adder wrapped in a compound element
        s = Interconnect()
        carry = Interconnect()

        ha = build_halfadder("ha1")
        ha.connect(s, 0)
        ha.connect(carry, 1)

        core = TestingCore()  # We don't start the process. That would be messy

        core.schedule(Edge(10, ha, 0, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertTrue(s.state)
        self.assertFalse(carry.state)

        core.schedule(Edge(core.clock + 1, ha, 1, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertFalse(s.state)
        self.assertTrue(carry.state)

        core.schedule(Edge(core.clock + 1, ha, 0, False))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertTrue(s.state)
        self.assertFalse(carry.state)

        core.schedule(Edge(core.clock + 1, ha, 1, False))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertFalse(s.state)
        self.assertFalse(carry.state)

    def test_stabilization(self):
        # Build a basic RS flip-flop
        r = Interconnect()
        s = Interconnect()

        nor_r = Nor()
        nor_s = Nor()

        q = Interconnect()
        nq = Interconnect()

        r.connect(nor_r)
        s.connect(nor_s)

        q.connect(nor_s, input=1)
        nq.connect(nor_r, input=1)

        nor_r.connect(q)
        nor_s.connect(nq)

        core = TestingCore()  # We don't start the process. That would be messy

        core.schedule(Edge(0, r, 0, False))  # Make sure we don't oscillate
        core.schedule(Edge(10, s, 0, True))  # Set the FF
        core.schedule(Edge(11, s, 0, False))

        self.assertGreater(100, core.loop_until_stable_state_or_time(100))

        self.assertTrue(q.state)
        self.assertFalse(nq.state)

        core.schedule(Edge(core.clock + 1, r, 0, True))  # Reset the ff

        self.assertGreater(100, core.loop_until_stable_state_or_time(100))

        self.assertFalse(q.state)
        self.assertTrue(nq.state)

        core.schedule(Edge(core.clock + 1, r, 0, False))  # Shouldn't change

        self.assertGreater(100, core.loop_until_stable_state_or_time(100))

        self.assertFalse(q.state)
        self.assertTrue(nq.state)

    def test_compound(self):
        fa = build_fulladder("fa")
        carry = Interconnect()
        s = Interconnect()

        fa.connect(s, 0)
        fa.connect(carry, 1)

        core = TestingCore()

        self.assertFalse(s.state)
        self.assertFalse(carry.state)

        core.schedule(Edge(0, fa, 0, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertTrue(s.state)
        self.assertFalse(carry.state)

        core.schedule(Edge(core.clock + 1, fa, 0, False))
        core.schedule(Edge(core.clock + 1, fa, 1, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertTrue(s.state)
        self.assertFalse(carry.state)

        core.schedule(Edge(core.clock + 1, fa, 0, True))
        core.schedule(Edge(core.clock + 1, fa, 1, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertFalse(s.state)
        self.assertTrue(carry.state)

        core.schedule(Edge(core.clock + 1, fa, 2, True))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertTrue(s.state)
        self.assertTrue(carry.state)

        core.schedule(Edge(core.clock + 1, fa, 0, False))
        self.assertGreater(100, core.loop_until_stable_state_or_time(100))
        self.assertFalse(s.state)
        self.assertTrue(carry.state)
