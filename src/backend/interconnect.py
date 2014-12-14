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
    PROPAGATION_CONSTANT=1  # One time unit per length unit

    def __init__(self):
        self.endpoints = []

    def __str__(self):
        names = [(id(endpoint), input) for (endpoint, input) in self.endpoints]
        return "{0}(=>{1})".format(self.__class__.__name__,
                                   ','.join(names))

    def add_connection(self, element, input, connection_length=1):
        """
        Inserts a new connection to the given elements input with given length.
        :param element: Element `input` refers to.
        :param input: Index of input to connect to
        :param connection_length: Length of the connection for delay calc
        """
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
        assert input==0, "Interconnect does not have multiple inputs."

        return [Edge(when + delay,
                     element,
                     input,
                     state) for element, input, delay in self.endpoints]
