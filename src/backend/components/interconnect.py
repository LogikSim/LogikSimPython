#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.element import Element, Edge
from backend.component_library import ComponentType
from copy import copy


class Interconnect(ComponentType):
    """
    Connection between elements.
    """
    METADATA = {"GUID": "00352520-7cf0-43b7-9449-6fca5be8d6dc",
                "name": "Interconnect",
                "#inputs": 1,
                "#outputs": 1,
                "description": "Represents connections between elements"}

    @classmethod
    def instantiate(cls, element_id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = element_id
        return InterconnectInstance(parent, metadata)


class InterconnectInstance(Element):
    """
    Single input multiple output connection between two elements.

    This pretty much is built to map onto one of our frontend LineTrees. If
    we worked with single logical connections in the backend storing the
    meta-data for the front-end would be quite annoying. We'll see if this
    becomes an issue in the future.
    """

    def __init__(self, parent, metadata):
        super().__init__(parent, metadata, Interconnect)

        if self.get_metadata_field("#inputs") != 1:
            self.set_metadata_field("#inputs", 1, False)

        output_count = self.get_metadata_field("#outputs")

        self.set_metadata_field('state', False, False)

        self.new_state = False
        self.state = False

        self.set_metadata_field('input-states',
                                False, False)

        self.outputs = [(None, 0, 0)] * output_count
        self.inputs = [(None, 0)]

        self.set_metadata_field('inputs',
                                self._in_con_to_data(self.inputs),
                                False)

        self.set_metadata_field('outputs',
                                self._out_con_to_data(self.outputs),
                                False)

    def __str__(self):
        names = []
        for endpoint, endpoint_input, delay in self.endpoints:
            names.append("{0}@{1}".format(endpoint_input, endpoint))

        return "{0}(=>{1})".format(self.__class__.__name__,
                                   ','.join(names))

    @classmethod
    def _out_con_to_data(cls, connections):
        return [((e.id() if e else None), c, d) for e, c, d in connections]

    @classmethod
    def _in_con_to_data(cls, connections):
        return [((e.id() if e else None), c) for e, c in connections]

    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        :return: Edge events for every output.
        """
        return [Edge(when + delay,
                     element,
                     input,
                     self.state) for element, input, delay in self.endpoints]

    def connect(self, element, output_port=0, input_port=0, delay=0):
        """
        Connects an element output to another elements input. This element
        has the speciality of automatically growing its amount of output
        ports instead of failing connection requests not matching the current
        one. The amount of outputs won't every shrink though

        :param element: Element to connect to output (None disconnects output)
        :param output_port: This elements output to connect to the input
        :param input_port: Input on given element to connect to
        :param delay: Delay for the connection
        :return: True if successfully connected
        """
        assert element is not None, "Must be given element to connect to"

        if len(self.outputs) < output_port + 1:
            # Expand the output count if needed
            outputs_to_add = output_port - len(self.outputs) + 1
            self.outputs.extend([(None, 0, 0)] * outputs_to_add)
            self.set_metadata_field('#outputs', output_port)

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

    def edge(self, input_port, state):
        """
        Registers a rising or falling edge on the interconnect.

        :param input_port: Index of the input
        :param state: Value of the input (True/False) at time `when`
        """
        assert input_port == 0, "Interconnect does not have multiple inputs."

        self.new_state = state

        return []

    def clock(self, when):
        """
        Schedules delayed propagation of state change to all connected element
        inputs.

        Note: This schedules directly on connected elements so it won't
              react to connectivity changes while the event is pending.

        :param when: Current simulation time.
        :return: One future edge event for each connection endpoint.
        """

        if self.new_state == self.get_metadata_field('state'):
            # Nothing to do
            # FIXME: Fix initialization behavior so we can return [] here
            pass

        self.set_metadata_field('state', self.new_state)
        self.state = self.new_state

        return [Edge(when + delay,
                     element,
                     input_port,
                     self.state) for (element,
                                      input_port,
                                      delay) in self.outputs if element]
