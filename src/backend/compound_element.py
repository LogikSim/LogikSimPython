#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.element import Element


class IndirectionElement(Element):
    """
    Zero latency indirection element.
    """
    def __init__(self):
        self.mapping = {}

    def connect(self, element, output=0, input=0):
        self.mapping[output] = (element, input)

    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        Triggers reset
        :return: Edge events for every output.
        """
        events = []
        for element in set([e for (e, _) in self.mapping.values()]):
            events.extend(element.reset())

        return events

    def edge(self, when, input, state):
        """
        Handles a rising or falling edge and maps it to the corresponding
        element.

        :param when: Current simulation time.
        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: List of one or more future Event s
        """
        if input not in self.mapping:
            # Pin is not connected.
            return []

        element, element_input = self.mapping[input]

        return element.edge(when, element_input, state)


class CompoundElement(Element):
    """
    Element wrapping other elements
    """
    def __init__(self, name):
        super().__init__()

        self.name = name
        self.input_posts = IndirectionElement()
        self.output_posts = IndirectionElement()

    def __str__(self):
        return "CompoundElement(name={0})".format(self.name)

    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        :return: Edge events for every output.
        """
        # FIXME: Do we want this to propagate the signal? Probably should not

        return self.input_posts.reset(when) + self.output_posts.reset(when)

    def edge(self, when, input, state):
        """
        Handles a rising or falling edge and maps it to the corresponding
        internal element.

        :param when: Current simulation time.
        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: List of one or more future Event s
        """
        return self.input_posts.edge(when, input, state)

    def connect(self, element, output=0, input=0):
        """
        Connects output posts to external element.

        :param element: Element to connect
        :param output: Output of post to connect to element
        :param input: Input on element to connect to
        :return: True if connected successful
        """
        return self.output_posts.connect(element, output, input)
