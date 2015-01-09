#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
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
        super().__init__(when, self.OUT_EDGE_GROUP)
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

    def process(self, last):
        return self.element._output(self.when, self.output, self.state)


class SimpleElement(Element):
    """
    Wasteful but should do fine for quick and dirty development experiments.
    """
    def __init__(self,
                 parent,
                 metadata,
                 component_type,
                 logic_function):
        """
        Constructs a basic logic element with input to output transformation.

        TODO: fix documentation of parameters
        :param logic_function: Function taking input iterable transforming it
            into the future outputs that become visible after `delay`
        :param input_count: Number of input latches for the element
        :param output_count: Number of output latches for the element
        :param delay: Propagation delay inside this logic element
        """
        super().__init__(parent, metadata, component_type)

        input_count = self.get_metadata_field("#inputs")
        output_count = self.get_metadata_field("#outputs")
        delay = self.get_metadata_field("delay")

        self.logic_function = logic_function

        self.input_states = array('i', [False] * input_count)
        self.set_metadata_field('input-states',
                                list(self.input_states), False)

        self.output_states = array('i', self.logic_function(self.input_states))
        self.set_metadata_field('output-states',
                                list(self.output_states), False)
        assert len(self.output_states) == output_count

        self.outputs = [(None, 0, 0)] * output_count
        self.inputs = [(None, 0)] * input_count

        self.set_metadata_field('inputs',
                                self._in_con_to_data(self.inputs),
                                False)

        self.set_metadata_field('outputs',
                                self._out_con_to_data(self.outputs),
                                False)

        self.delay = delay
        self.last_clock = -1

    @classmethod
    def _out_con_to_data(cls, connections):
        return [((e.id() if e else None), c, d) for e, c, d in connections]

    @classmethod
    def _in_con_to_data(cls, connections):
        return [((e.id() if e else None), c) for e, c in connections]

    def __str__(self):
        return "{0}({1})={2}".format(self.__class__.__name__,
                                     ','.join([str(i) for i in
                                               self.input_states]),
                                     ','.join([str(i) for i in
                                               self.output_states]))

    def edge(self, input_port, state):
        """
        Handles a rising or falling edge on one of the elements inputs.

        :param input_port: Input index
        :param state: Value of the input (True/False)
        """
        assert input_port < len(self.input_states), \
            "Tried to set {0}th input on {1} input gate" \
            .format(input_port, len(self.input_states))

        self.input_states[input_port] = state  # Inputs apply immediately

    def clock(self, when):
        """
        Triggered when all egdes for a point in time have been received.

        :param when: Point in time
        :return: List of none or more future Event s
        """
        assert self.last_clock != when, "Repeated clock for {0}".format(when)
        self.last_clock = when

        self.set_metadata_field('input-states', list(self.input_states))

        future_output = self.logic_function(self.input_states)

        return [OutEdge(when + self.delay,
                        self,
                        output,
                        fstate) for output, fstate in enumerate(future_output)]

    def connect(self, element, output_port=0, input_port=0, delay=0):
        """
        Attach a given elements input to one of this elements outputs.

        :param element: Element to connect to output
        :param output_port: This elements output to connect to the input
        :param input_port: Input on given element to connect to
        :param delay: Delay of this connection in simulation units
        """
        assert element is not None, "Must be given element to connect to"

        if self.outputs[output_port][0] is not None:
            # Can't connect twice
            return False

        if not element.connected(self, output_port, input_port):
            # Other element rejected the connection
            return False

        self.outputs[output_port] = (element, input_port, delay)

        self.set_metadata_field('outputs', self._out_con_to_data(self.outputs))

        self.propagate_change({
            'source_id': self.id(),
            'source_port': output_port,
            'sink_id': element.id() if element else None,
            'sink_port': input_port,
            'delay': delay
        })

        return True

    def disconnect(self, output_port):
        """
        Disconnects the currently connected element from the given port
        on this element.

        :param output_port: Port to disconnect
        :return: True if successful
        """
        remote, remote_input, _ = self.outputs[output_port]
        if not remote:
            # Nothing connected
            return False

        if not remote.disconnected(remote_input):
            return False

        self.outputs[output_port] = (None, 0, 0)

        self.set_metadata_field('outputs', self._out_con_to_data(self.outputs))

        self.propagate_change({
            'source_id': self.id(),
            'source_port': output_port,
            'sink_id': None,
            'sink_port': 0,
            'delay': 0
        })

        return True

    def connected(self, element, output_port=0, input_port=0):
        """
        Remembers connections to a given port.

        :param element:
        :param output_port:
        :param input_port:
        :return:
        """
        assert element is not None, "Must be given element"

        if self.inputs[input_port][0] is not None:
            # Already have something connected on that port
            return False

        self.inputs[input_port] = (element, output_port)
        self.set_metadata_field('inputs', self._in_con_to_data(self.inputs))

        return True

    def disconnected(self, input_port):
        """
        Clears a connection to this element.

        :param input_port:
        :return: True if successfull
        """
        if self.inputs[input_port][0] is None:
            # There wasn't anything connected in the first place
            return False

        self.inputs[input_port] = (None, 0)
        self.set_metadata_field('inputs', self._in_con_to_data(self.inputs))

        return True

    def destruct(self):
        # Drop all in and outbound connections first
        for (element, port) in self.inputs:
            if not element:
                continue

            element.disconnect(port)

        for output_port, (element, port, delay) in enumerate(self.outputs):
            if not element:
                continue

            self.disconnect(output_port)

        # Make sure to go through the rest of the destruction process
        return super().destruct()

    def _output(self, when, output, state):
        assert output < len(self.output_states), \
            "Gate does not have an output {0}" \
            .format(output)

        if self.output_states[output] == state:
            # No thing to do here.
            return []

        self.output_states[output] = state
        self.set_metadata_field('output-states', list(self.output_states))

        element, input_port, delay = self.outputs[output]
        if element is None:
            return []  # Nothing connected. No follow-up events

        return [Edge(when + delay, element, input_port, state)]
