#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from abc import ABCMeta, abstractmethod


class Event(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, when, group):
        """
        Creates a new event scheduled at a given time.

        :param when: Simulation time to schedule this event to.
        :param group: Integer value used to group events. Events occurring at
            the same time with the same group are guaranteed to be executed
            consecutively with the last one receiving the last_in_group flag
            during processing.
        :param process: Called with state to process event. Must
                        return a list of one or more future Events
                        to schedule.
        """
        self.when = when
        self.group = group

    @abstractmethod
    def process(self, last_in_group):
        """
        Called for processing events.
        :param last_in_group: True if this is the last even of the group
            handled at self.when
        :return: None or more new Events to schedule
        """
        pass

    def __str__(self):
        return "Event({0},{1},{2})".format(self.when, self.group, self.process)

    def __lt__(self, other):
        """
        :return: True if `other` is scheduled after this event.
        """
        return self.when < other.when if self.when != other.when else \
            self.group < other.group
