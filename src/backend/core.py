#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from queue import PriorityQueue
from multiprocessing import Process

from backend.event import Event


class Core(Process):
    def __init__(self):
        super().__init__()

        self.queue = PriorityQueue()
        self.clock = 0

    def __str__(self):
        return "|Core(time={0})|={1}".format(self.clock, len(self.queue))

    def _process_next_event(self):
        """
        Broken out inner core of event processing loop for easier testing.
        :return: Processed event.
        """
        event = self.queue.get()
        self.clock = event.when

        for new_event in event.process():
            self.schedule(new_event)

        return event

    def run(self):
        while True:
            self._process_next_event()

    def schedule(self, event):
        assert isinstance(event, Event),\
            "Can only schedule things derived from Event"
        assert event.when > self.clock,\
            "Can only schedule things in the future"

        self.queue.put(event)
