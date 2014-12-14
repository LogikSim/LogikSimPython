#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from array import array
from backend.element import Element
from backend.event import Event


class OutEdge(Event):
    """
    Expresses a scheduled edge on an output pin.
    Used internally by SimpleElement
    """
    def __init__(self, when, element, output, state):
        super().__init__(when, self._process)
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

    def _process(self):
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
        self.outputs = [None] * output_count
        self.delay = delay
        self.logic_function = logic_function

    def __str__(self):
        return "{0}({1})={2}".format(self.__class__.__name__,
                                     ','.join(self.input_states),
                                     ','.join(self.output_states))

    def edge(self, when, input, state):
        """
        Handles a rising or falling edge on one of the elements inputs.

        :param when: Current simulation time.
        :param input: Input index
        :param state: Value of the input (True/False)
        """
        assert input < len(self.input_states), \
            "Tried to set {0}th input on {1} input gate" \
            .format(input, len(self.input_states))

        self.input_states[input] = state  # Inputs apply immediately

        future_output = self.logic_function(self.input_states)

        return [OutEdge(when + self.delay,
                        self,
                        output,
                        state) for output, state in enumerate(future_output)]

    def attach(self, output, element, input=0):
        self.outputs[output] = (element, input)

    def _output(self, when, output, state):
        assert output < len(self.output_states), \
            "Gate does not have an output {0}" \
                .format(output)

        self.output_states[output] = state

        if self.outputs[output] is not None:
            element, input = self.outputs[output]
            return element.edge(when, input, state)

        return []  # Nothing connected. No follow-up events

