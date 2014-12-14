#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.event import Event


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
        super().__init__(when, self._process)
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

    def _process(self):
        """Edge only knows handler functions so this function implements one"""
        return self.element.edge(self.when, self.input, self.state)


class Element(object):
    """
    Baseclass for all Elements that are part of the simulation.
    """

    def edge(self, when, input, state):
        """
        Handles a rising or falling edge on one of the elements inputs.

        :param when: Current simulation time.
        :param input: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: List of one or more future Event s
        """
        assert False, "Elements must implement input edge handling"
