#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.element import Element, Edge


class Interconnect(Element):
    """
    Single input multiple output connection between two elements.

    This pretty much is built to map onto one of our frontend LineTrees. If
    we worked with single logical connections in the backend storing the
    meta-data for the front-end would be quite annoying. We'll see if this
    becomes an issue in the future.
    """
    PROPAGATION_CONSTANT = 1  # One time unit per length unit

    def __init__(self):
        self.endpoints = []
        self.state = False

    def __str__(self):
        names = [(id(endpoint), input) for (endpoint, input) in self.endpoints]
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

    def edge(self, when, input, state):
        """
        Schedules delayed propagation of state change to all connected element
        inputs.

        Note: This schedules directly on connected elements so it won't
              react to connectivity changes while the event is pending.

        :param when: Current simulation time.
        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: One future edge event for each connection endpoint.
        """
        assert input == 0, "Interconnect does not have multiple inputs."

        self.state = state

        return [Edge(when + delay,
                     element,
                     iinput,
                     state) for element, iinput, delay in self.endpoints]
