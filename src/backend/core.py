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


# FIXME: Figure out how to best provide logging to the core process

class CoreInterface:
    def __init__(self, core, channel_out):
        self.core = core
        self.channel_out = channel_out

    def schedule_edge(self, element_id, input, state):
        """
        Schedules a signal transition
        :param element_id: Element to schedule signal transition on
        :param input: Input pin index
        :param state: State to transition to
        """
        self.channel_out.put(
            {
                'action': 'edge',
                'id': element_id,
                'input': input,
                'state': state
            }
        )

    def create_element(self, guid, parent = None, additional_metadata={}):
        """
        Schedules creation of an element with the given GUID.

        GUID must already be registered with core component library.

        :param guid: Type of element to create
        :param parent: Optional parent element id
        :param additional_metadata: Additional meta-data to create element with
        """
        self.channel_out.put(
            {
                'action': 'create',
                'GUID': guid,
                'parent': parent,
                'metadata': additional_metadata
            }
        )

    def update_element(self, element_id, changed_metadata={}):
        self.channel_out.put(
            {
                'action': 'update',
                'id': element_id,
                'metadata': changed_metadata
            }
        )

    def delete_element(self, element_id):
        self.channel_out.put(
            {
                'action': 'delete',
                'id': element_id
            }
        )

    def request_element_information(self, element_id):
        self.channel_out.put(
            {
                'action': 'query',
                'id': element_id
            }
        )

    def connect(self, source_id, source_port, sink_id, sink_port, delay):
        self.channel_out.put(
            {
                'action': 'connect',
                'source_id': source_id,
                'source_port': source_port,
                'sink_id': sink_id,
                'sink_port': sink_port,
                'delay': delay
            }
        )

    def exit(self):
        self.channel_out.put(
            {
                'action': 'quit'
            }
        )


class Core(Process):
    def __init__(self, library):
        super().__init__()

        self.event_queue = PriorityQueue()

        self.channel_out = Queue()
        self.channel_in = Queue()

        self.clock = -1
        self.group = None
        self.quit = False

        self.elements = {}  # ID -> element in simulation
        self.connections = []  # (source_id, source_port, sink_id, sink_port)
        self.connect_from = {}  # ID -> port -> connection
        self.connect_to = {}  # ID -> port -> connection

        self.library = library

    def __str__(self):
        return "|Core(time={0})|={1}".format(self.clock, len(self.event_queue))

    def interface(self):
        return CoreInterface(core=self,
                             channel_out=self.channel_in)

    def _process_next_event(self):
        """
        Broken out inner core of event processing loop for easier testing.
        :return: Processed event.
        """
        event = self.event_queue.get()

        assert event.when >= self.clock, "Encountered event from the past"
        self.clock = event.when
        self.group = event.group

        last_in_group = \
            self.event_queue.empty() or \
            self.event_queue.queue[0].group != self.group or \
            self.event_queue.queue[0].when != self.clock

        for new_event in event.process(last_in_group):
            self.schedule(new_event)

        return event

    def propagate_change(self, data):
        """
        Function for propagating events up into the simulation frontend.
        Propagation follows child-parent-relationships so parent elements
        can employ filtering.

        :param data: metadata update message.
        :return:
        """
        self.channel_out.put(data)

    def run(self):
        self.quit = False

        while not self.quit:
            self._process_next_event()

            # We assume the vast majority of the load will be in simulation
            # so we can safely drain our command queue in a blocking fashion.
            # Would be awesome to handle this as part of the normal event
            # cycle but unfortunately that's not a good idea as we want to
            # achieve wall-time response times which is hard to do (and not
            # overdo) when working with events scheduled by simulation time.
            # Especially if we might drop sub-realtime if event-load gets high
            # enough. Ah well. When designs meet reality...
            while not self.channel_in.empty():  # Racy but totally fine here
                command = self.channel_in.get_nowait()  # Single consumer
                action = command.get('action')
                if action == 'create':
                    parent = self.elements.get(command.get("parent"))
                    element = self.library.instantiate(
                        command['GUID'],
                        self if not parent else parent,
                        command['metadata'])

                    element_id = element.id()
                    self.elements[element_id] = element
                elif action == 'update':
                    element = self.elements[command['id']]
                    element.update_metadata_fields(command['metadata'])

                elif action == 'delete':
                    # Delete connections from first
                    # The connections to
                    # Then delete element
                    raise NotImplementedError(action)
                elif action == 'query':
                    raise NotImplementedError(action)
                elif action == 'connect':
                    raise NotImplementedError(action)
                elif action == 'quit':
                    self.quit = True
                    break
                else:
                    raise TypeError("Unknown action type {0}".format(action))

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
