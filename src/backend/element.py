#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.event import Event
from backend.component_library import ComponentInstance
from abc import abstractmethod


class Edge(Event):
    """
    Expresses a scheduled edge on an element input pin.
    """
    def __init__(self, when, element, input, state):
        """
        Schedules a rising or falling edge on one of the given elements inputs.

        :param when: Time to schedule the event for
        :param element: Element `input` is referring to
        :param input: Index of the input the signal edge will occur on
        :param state: Signal value after the edge (True/False) at time `when`
        """
        super().__init__(when, id(element))
        self.element = element
        self.input = input
        self.state = state

    def __str__(self):
        return "Edge(when={0},element={1},input={2},state={3}" \
            .format(self.when, id(self.element), self.input, self.state)

    def __eq__(self, other):
        return self.element == other.element \
            and self.input == other.input \
            and self.state == other.state \
            and self.when == other.when

    def process(self, last):
        """Edge only knows handler functions so this function implements one"""
        self.element.edge(self.input, self.state)

        # Only schedule events when all edges addresses to the element
        # have been processed.

        if not last:
            return []

        return self.element.clock(self.when)


class Element(ComponentInstance):
    """
    Baseclass for all Elements that are part of the simulation.
    """
    def __init__(self, metadata, component_type):
        super().__init__(metadata, component_type)

    @abstractmethod
    def edge(self, input, state):
        """
        Handles a rising or falling edge on one of the elements inputs.

        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: List of none or more future Event s
        """
        pass

    @abstractmethod
    def clock(self, when):
        """
        Triggered when all egdes for a point in time have been received.

        :param when: Point in time
        :return: List of none or more future Event s
        """
        pass

    @abstractmethod
    def reset(self, when):
        """
        Emulates an input reset resulting in edge events for every output.
        :return: Edge events for every output.
        """
        pass

    @abstractmethod
    def connect(self, element, output=0, input=0):
        """
        Connects an element output to another elements input.

        :param element: Element to connect to output (None disconnects output)
        :param output: This elements output to connect to the input
        :param input: Input on given element to connect to
        :return: True if successfully connected
        """
        pass

    def disconnect(self, output):
        """
        Disconnects the given output.
        :param output: Output index.
        :return: True if successful
        """
        return self.connect(None, output)
