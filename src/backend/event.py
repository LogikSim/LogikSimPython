#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#


class Event(object):
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

    def __str__(self):
        return "Event({0},{1})".format(self.when, self.process)

    def __lt__(self, other):
        """
        :return: True if `other` is scheduled after this event.
        """
        return self.when < other.when
