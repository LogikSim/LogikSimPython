#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#


class Event(object):
    sequence_counter = 0

    def __init__(self, when, process):
        """
        Creates a new event scheduled at a given time.

        :param when: Simulation time to schedule this event to.
        :param process: Called with state to process event. Must
                        return a list of one or more future Events
                        to schedule.
        """
        self.when = when
        self.process = process

        self.sequence = Event.sequence_counter
        # FIXME: Kinda ugly but we need them to be executed in the order
        #  they were created or we might end up having events occurring at
        #  the same time racing each other leading to invalid outputs
        #  depending on execution order. E.g. if we have an Or element and
        #  a (1,0)->1 is scheduled at the same time as a (0,0)->0
        #  the constant output delay might mean we might output the edge to 0
        #  first ending up in an invalid 1 output state after both edges.
        #
        Event.sequence_counter += 1

    def __str__(self):
        return "Event({0},{1})".format(self.when, self.process)

    def __lt__(self, other):
        """
        :return: True if `other` is scheduled after this event.
        """
        return self.when < other.when if self.when != other.when else \
            self.sequence < other.sequence
