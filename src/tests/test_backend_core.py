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
from backend.components.basic_logic_elements import Xor, And, Nor, Or
from backend.components.compound_element import CompoundElement
from backend.element import Edge
from backend.components.interconnect import Interconnect
from tests.helpers import CallTrack


class TestingCore(Core):
    def __init__(self):
        super().__init__()
        self.timeline = []

    def loop_until_stable_state_or_time(self, time=None):
        while not self.queue.empty():
            if time is not None and self.queue.queue[0].when >= time:
                return time

            # print(" Processing {0}".format(self.queue.queue[0]))
            event = self._process_next_event()
            self.timeline.append((self.clock, event))
            # print(" Done processing")

        return self.clock

    def schedule(self, event):
        # print("Scheduling {0}".format(event))
        super().schedule(event)


def build_halfadder(name):
    a = Interconnect.instantiate(0)
    b = Interconnect.instantiate(1)

    xor_gate = Xor.instantiate(1)
    and_gate = And.instantiate(2)

    a.connect(xor_gate)
    a.connect(and_gate)

    b.connect(xor_gate, input=1)
    b.connect(and_gate, input=1)

    half_adder = CompoundElement.instantiate(3, {"name": name})
    half_adder.input_bank.connect(a, 0)
    half_adder.input_bank.connect(b, 1)

    xor_gate.connect(half_adder.output_bank, 0, 0)  # Sum on out 0
    and_gate.connect(half_adder.output_bank, 0, 1)  # Carry on out 1

    return half_adder


def build_fulladder(name):
    ha1 = build_halfadder(name+"_ha1")
    ha2 = build_halfadder(name+"_ha2")

    full_adder = CompoundElement.instantiate(0, {"name": name})
    full_adder.input_bank.connect(ha1, 0, 0)  # A input on 0
    full_adder.input_bank.connect(ha1, 1, 1)  # B input on 1
    ha1.connect(ha2, 0, 0)
    full_adder.input_bank.connect(ha2, 2, 1)  # Carry input on 2

    or_gate = Or.instantiate(0)
    ha1.connect(or_gate, 1, 0)  # ha1 carry on or
    ha2.connect(or_gate, 1, 1)  # ha2 carry on or

    ha2.connect(full_adder.output_bank, 0, 0)  # Sum on out 0
    or_gate.connect(full_adder.output_bank, 0, 1)  # Carry on out 1

    return full_adder


class BackendCoreTest(unittest.TestCase):
    """
    Unit tests for backend core including some element integration tests.
    """

    def test_priority_queue(self):
        c = TestingCore()  # We don't start the process. That would be messy

        ct = CallTrack(result_fu=lambda x: [])
        ct2 = CallTrack(result_fu=lambda x: [])
        ct3 = CallTrack(result_fu=lambda x: [])

        e1 = Event(10, 0, ct.slot)
        e2 = Event(100, 0, ct2.slot)
        e3 = Event(100, 0, ct2.slot)
        e4 = Event(100, 1, ct3.slot)

        c.schedule(e1)
        c.schedule(e2)
        c.schedule(e3)
        c.schedule(e4)

        c.loop_until_stable_state_or_time()

        self.assertListEqual([(10, e1), (100, e3), (100, e2), (100, e4)],
                             c.timeline)
        self.assertListEqual([True], ct())
        self.assertListEqual([False, True], ct2())
        self.assertListEqual([True], ct3())

    def test_element_behavior(self):
        # Build a simple half-adder
        a = Interconnect.instantiate(0)
        b = Interconnect.instantiate(1)

        s = Interconnect.instantiate(2)
        c = Interconnect.instantiate(3)

        xor_gate = Xor.instantiate(4)
        and_gate = And.instantiate(5)

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
        s = Interconnect.instantiate(0)
        carry = Interconnect.instantiate(1)

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
        r = Interconnect.instantiate(0)
        s = Interconnect.instantiate(1)

        nor_r = Nor.instantiate(2)
        nor_s = Nor.instantiate(3)

        q = Interconnect.instantiate(4)
        nq = Interconnect.instantiate(5)

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
        carry = Interconnect.instantiate(0)
        s = Interconnect.instantiate(1)

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
