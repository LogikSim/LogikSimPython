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
import time


# FIXME: Figure out how to best provide logging to the core process

class Core(Process):
    def __init__(self, controller):
        super().__init__()

        self.event_queue = PriorityQueue()

        self.clock = -1
        self.retired_events = 0
        self.group = None

        self._quit = False
        self.controller = controller

    def __str__(self):
        return "|Core(time={0})|={1}".format(self.clock, len(self.event_queue))

    def _process_next_event(self, upto_clock):
        """
        Broken out inner core of event processing loop.
        :param upto_clock: Only process events scheduled up to this time. -1
            for executing till stable state.
        :return: Processed event or None if nothing was pending or clock
            limit reached
        """

        if self.event_queue.empty() or \
                self.event_queue.queue[0].when > upto_clock:
            # If queue is empty circuit is steady state so simulation is
            # infinitely fast. Also we need this clock behavior to make delta
            # timing in the controller work. It totally makes sense though ;)
            self.clock = upto_clock

            return None

        event = self.event_queue.get_nowait()

        assert event.when >= self.clock, "Encountered event from the past"
        self.clock = event.when
        self.group = event.group

        last_in_group = \
            self.event_queue.empty() or \
            self.event_queue.queue[0].group != self.group or \
            self.event_queue.queue[0].when != self.clock

        followup_events = event.process(last_in_group)
        self.retired_events += 1

        self.schedule_many(followup_events)

        return event

    def quit(self):
        """
        Causes the core to terminate execution as soon as possible.
        """
        self._quit = True

    def run(self):
        self._quit = False

        while not self._quit:
            (target_clock, target_time) = self.controller.process(self.clock)

            while target_time - time.perf_counter() > 0:
                if not self._process_next_event(target_clock):
                    break

    def schedule_many(self, events):
        for event in events:
            self.schedule(event)

    def schedule(self, event):
        """
        Schedules an event for processing.

        Must NOT be called outside of this processes thread.

        :param event:
        :return:
        """
        assert isinstance(event, Event),\
            "Can only schedule things derived from Event"
        assert event.when >= self.clock,\
            "Cannot schedule events in the past"

        self.event_queue.put(event)
