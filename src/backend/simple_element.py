#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from array import array
from backend.element import Element, Edge
from backend.event import Event


class OutEdge(Event):
    """
    Expresses a scheduled edge on an output pin.
    Used internally by SimpleElement
    """

    # Giving the output edges a common group with negative value
    # makes sure they are processed first. This is required as
    # they will create new events at the very same time
    # their triggering edge occurs.
    OUT_EDGE_GROUP = -1

    def __init__(self, when, element, output, state):
        super().__init__(when, self.OUT_EDGE_GROUP, self._process)
        self.element = element
        self.output = output
        self.state = state

    def __str__(self):
        return "OutEdge(when={0},element={1},output={2},state={3}"\
            .format(self.when, id(self.element), self.output, self.state)

    def __eq__(self, other):
        return self.element == other.element\
            and self.output == other.output\
            and self.state == other.state\
            and self.when == other.when

    def _process(self, last):
        return self.element._output(self.when, self.output, self.state)


class SimpleElement(Element):
    """
    Wasteful but should do fine for quick and dirty development experiments.
    """
    def __init__(self,
                 logic_function,
                 input_count=1,
                 output_count=1,
                 delay=1):
        """
        Constructs a basic logic element with input to output transformation.

        :param logic_function: Function taking input iterable transforming it
            into the future outputs that become visible after `delay`
        :param input_count: Number of input latches for the element
        :param output_count: Number of output latches for the element
        :param delay: Propagation delay inside this logic element
        """
        self.input_states = array('i', [False] * input_count)
        self.output_states = array('i', [False] * output_count)
        self.outputs = [(None, 0)] * output_count
        self.delay = delay
        self.logic_function = logic_function
        self.last_clock = -1

    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        :return: Edge events for every output.
        """
        future_output = self.logic_function(self.input_states)

        return [OutEdge(when + self.delay,
                        self,
                        output,
                        state) for output, state in enumerate(future_output)]

    def __str__(self):
        return "{0}({1})={2}".format(self.__class__.__name__,
                                     ','.join([str(i) for i in
                                               self.input_states]),
                                     ','.join([str(i) for i in
                                               self.output_states]))

    def edge(self, input, state):
        """
        Handles a rising or falling edge on one of the elements inputs.

        :param input: Input index
        :param state: Value of the input (True/False)
        """
        assert input < len(self.input_states), \
            "Tried to set {0}th input on {1} input gate" \
            .format(input, len(self.input_states))

        self.input_states[input] = state  # Inputs apply immediately

    def clock(self, when):
        """
        Triggered when all egdes for a point in time have been received.

        :param when: Point in time
        :return: List of none or more future Event s
        """
        assert self.last_clock != when, "Repeated clock for {0}".format(when)
        self.last_clock = when

        future_output = self.logic_function(self.input_states)

        return [OutEdge(when + self.delay,
                        self,
                        output,
                        fstate) for output, fstate in enumerate(future_output)]

    def connect(self, element, output=0, input=0):
        """
        Attach a given elements input to one of this elements outputs.

        :param element: Element to connect to output
        :param output: This elements output to connect to the input
        :param input: Input on given element to connect to
        """
        self.outputs[output] = (element, input)

    def _output(self, when, output, state):
        assert output < len(self.output_states), \
            "Gate does not have an output {0}" \
            .format(output)

        if self.output_states[output] == state:
            # No thing to do here.
            return []

        self.output_states[output] = state

        element, input = self.outputs[output]
        if element is None:
            return []  # Nothing connected. No follow-up events

        return [Edge(when, element, input, state)]
