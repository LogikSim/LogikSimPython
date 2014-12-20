#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
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
                "name": __name__,
                "description": __doc__}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return InterconnectInstance(metadata)


class InterconnectInstance(Element):
    """
    Single input multiple output connection between two elements.

    This pretty much is built to map onto one of our frontend LineTrees. If
    we worked with single logical connections in the backend storing the
    meta-data for the front-end would be quite annoying. We'll see if this
    becomes an issue in the future.
    """
    PROPAGATION_CONSTANT = 1  # One time unit per length unit

    def __init__(self, metadata):
        super().__init__(metadata, Interconnect)

        self.endpoints = []
        self.state = False
        self.last_clock = -1

    def __str__(self):
        names = []
        for endpoint, endpoint_input, delay in self.endpoints:
            names.append("{0}@{1}".format(endpoint_input, endpoint))

        return "{0}(=>{1})".format(self.__class__.__name__,
                                   ','.join(names))

    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        :return: Edge events for every output.
        """
        return [Edge(when + delay,
                     element,
                     input,
                     self.state) for element, input, delay in self.endpoints]

    def connect(self, element, output=0, input=0, connection_length=1):
        """
        Connects an element output to another elements input.

        :param element: Element to connect to output (None disconnects output)
        :param output: This elements output to connect to the input (always 0)
        :param input: Input on given element to connect to
        :param connection_length: Length of the connection for delay calc
        :return: True if successfully connected
        """
        assert output == 0, "Interconnect only has one output"

        if element is None:
            # Disconnect everything
            self.endpoints.clear()
            pass

        delay = connection_length * self.PROPAGATION_CONSTANT
        self.endpoints.append((element, input, delay))

    def edge(self, input, state):
        """
        Registers a rising or falling edge on the interconnect.

        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        """
        assert input == 0, "Interconnect does not have multiple inputs."

        self.state = state

    def clock(self, when):
        """
        Schedules delayed propagation of state change to all connected element
        inputs.

        Note: This schedules directly on connected elements so it won't
              react to connectivity changes while the event is pending.

        :param when: Current simulation time.
        :return: One future edge event for each connection endpoint.
        """
        assert self.last_clock != when, "Repeated clock for {0} on {1}".format(
            when, self)
        self.last_clock = when

        return [Edge(when + delay,
                     element,
                     iinput,
                     self.state) for element, iinput, delay in self.endpoints]
