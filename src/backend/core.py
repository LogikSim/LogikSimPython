#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from queue import PriorityQueue, Queue
from multiprocessing import Process

from backend.event import Event

# Idea: Meta-data is king. Simple CRUD interface.

# Create element: {'guid':12312, 'metadata': {'x':213}}
# Move element: {'id': id, 'metadata': {'x':345, 'y':321 }}
# Delete element: {'id': id, None}
# Request information: {'id': id, 'query': ['x','y']}


class Core(Process):
    def __init__(self):
        super().__init__()

        self.eventQueue = PriorityQueue()

        self.channelOut = Queue()
        self.channelIn = Queue()

        self.clock = -1
        self.group = None

    def __str__(self):
        return "|Core(time={0})|={1}".format(self.clock, len(self.eventQueue))

    def _process_next_event(self):
        """
        Broken out inner core of event processing loop for easier testing.
        :return: Processed event.
        """
        event = self.eventQueue.get()

        assert event.when >= self.clock, "Encountered event from the past"
        self.clock = event.when
        self.group = event.group

        last_in_group = \
            self.eventQueue.empty() or \
            self.eventQueue.queue[0].group != self.group or \
            self.eventQueue.queue[0].when != self.clock

        for new_event in event.process(last_in_group):
            self.schedule(new_event)

        return event

    def run(self):
        while True:
            self._process_next_event()

    def schedule(self, event):
        assert isinstance(event, Event),\
            "Can only schedule things derived from Event"
        assert event.when >= self.clock,\
            "Cannot schedule events in the past"

        self.eventQueue.put(event)
