#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from unittest import expectedFailure

from backend.core import Core
from backend.controller import Controller
from backend.event import Event
from backend.components.basic_logic_elements import Xor, And, Nor, Or
from backend.components.compound_element import CompoundElement
from backend.element import Edge
from backend.components.interconnect import Interconnect
from backend.component_library import ComponentLibrary
from backend.component_library import get_library
from tests.helpers import CallTrack
from tests import helpers
from queue import Queue


class TestingCore(Core):
    def __init__(self):
        super().__init__()
        self.timeline = []

    def loop_until_stable_state_or_time(self, time=float("inf")):
        while not self.event_queue.empty():
            if self.event_queue.queue[0].when >= time:
                return time

            # print(" Processing {0}".format(self.queue.queue[0]))
            event = self._process_next_event(time)
            self.timeline.append((self.clock, event))
            # print(" Done processing")

        return self.clock

    def schedule(self, event):
        # print("Scheduling {0}".format(event))
        super().schedule(event)


class TestingController(Controller):
    def __init__(self, core=None, library=None):
        core = core if core else TestingCore()
        library = library if library else ComponentLibrary()
        # Initialize the controller with normal queues to prevent
        # multiprocess.queue threading issues
        super().__init__(core, library, queue_type=Queue)


def build_halfadder(name, parent):
    half_adder = CompoundElement.instantiate(3, parent, {"name": name})

    a = Interconnect.instantiate(0, half_adder)
    b = Interconnect.instantiate(1, half_adder)

    xor_gate = Xor.instantiate(1, half_adder)
    and_gate = And.instantiate(2, half_adder)

    a.connect(output_port=0, element=xor_gate, input_port=0)
    a.connect(output_port=1, element=and_gate, input_port=0)

    b.connect(output_port=0, element=xor_gate, input_port=1)
    b.connect(output_port=1, element=and_gate, input_port=1)

    half_adder.input_bank.connect(0, a, 0)
    half_adder.input_bank.connect(1, b, 0)

    xor_gate.connect(0, half_adder.output_bank, 0)  # Sum on out 0
    and_gate.connect(0, half_adder.output_bank, 1)  # Carry on out 1

    return half_adder


def build_fulladder(name, parent):
    full_adder = CompoundElement.instantiate(0, parent, {"name": name})

    ha1 = build_halfadder(name + "_ha1", full_adder)
    ha2 = build_halfadder(name + "_ha2", full_adder)

    full_adder.input_bank.connect(0, ha1, 0)  # A input on 0
    full_adder.input_bank.connect(1, ha1, 1)  # B input on 1
    ha1.connect(0, ha2, 0)
    full_adder.input_bank.connect(2, ha2, 1)  # Carry input on 2

    or_gate = Or.instantiate(0, full_adder)
    ha1.connect(1, or_gate, 0)  # ha1 carry on or
    ha2.connect(1, or_gate, 1)  # ha2 carry on or

    ha2.connect(0, full_adder.output_bank, 0)  # Sum on out 0
    or_gate.connect(0, full_adder.output_bank, 1)  # Carry on out 1

    return full_adder


class FuEvent(Event):
    def __init__(self, when, group, fu):
        super().__init__(when, group)
        self.fu = fu

    def process(self, last):
        return self.fu(last)


class BackendCoreTest(helpers.CriticalTestCase):
    """
    Unit tests for backend core including some element integration tests.
    """

    def test_priority_queue(self):
        c = TestingCore()  # We don't start the process. That would be messy

        ct = CallTrack(result_fu=lambda x: [])
        ct2 = CallTrack(result_fu=lambda x: [])
        ct3 = CallTrack(result_fu=lambda x: [])

        e1 = FuEvent(10, 0, ct.slot)
        e2 = FuEvent(100, 0, ct2.slot)
        e3 = FuEvent(100, 0, ct2.slot)
        e4 = FuEvent(100, 1, ct3.slot)

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
        ctrl = TestingController()

        # Build a simple half-adder
        a = Interconnect.instantiate(0, ctrl)
        b = Interconnect.instantiate(1, ctrl)

        s = Interconnect.instantiate(2, ctrl)
        c = Interconnect.instantiate(3, ctrl)

        xor_gate = Xor.instantiate(4, ctrl)
        and_gate = And.instantiate(5, ctrl)

        self.assertTrue(a.connect(0, xor_gate, 0))
        self.assertTrue(a.connect(1, and_gate, 0))

        self.assertTrue(b.connect(0, xor_gate, 1))
        self.assertTrue(b.connect(1, and_gate, 1))

        self.assertTrue(xor_gate.connect(0, s, 0))
        self.assertTrue(and_gate.connect(0, c, 0))

        core = ctrl.get_core()
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
        ctrl = TestingController(library=get_library())

        s = Interconnect.instantiate(0, ctrl)
        carry = Interconnect.instantiate(1, ctrl)

        ha = build_halfadder("ha1", ctrl)
        ha.connect(0, s, 0)
        ha.connect(1, carry, 0)

        core = ctrl.get_core()

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

    @expectedFailure
    def test_stabilization(self):
        ctrl = TestingController()

        # Build a basic RS flip-flop
        r = Interconnect.instantiate(0, ctrl)
        s = Interconnect.instantiate(1, ctrl)

        nor_r = Nor.instantiate(2, ctrl)
        nor_s = Nor.instantiate(3, ctrl)

        q = Interconnect.instantiate(4, ctrl)
        nq = Interconnect.instantiate(5, ctrl)

        r.connect(0, nor_r, 0)
        s.connect(0, nor_s, 0)

        q.connect(output_port=1, element=nor_s, input_port=1)
        nq.connect(output_port=1, element=nor_r, input_port=1)

        nor_r.connect(0, q, 0)
        nor_s.connect(0, nq, 0)

        core = ctrl.get_core()

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
        ctrl = TestingController(library=get_library())

        fa = build_fulladder("fa", ctrl)
        carry = Interconnect.instantiate(0, ctrl)
        s = Interconnect.instantiate(1, ctrl)

        self.assertTrue(fa.connect(0, s, 0))
        self.assertTrue(fa.connect(1, carry, 0))

        self.assertFalse(s.state)
        self.assertFalse(carry.state)

        core = ctrl.get_core()

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
