#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import multiprocessing
from backend.interface import Interface
import time
from logging import getLogger


class Controller:
    """
    Class managing control and observation based aspects of the simulation.
    This includes enabling instantiating, modifying, destroying as well as
    observation of component instances in the simulation by users.

    The controller receives special treatment in the simulation core to allow
    it fast response times independent of simulation speed and event load and
    hence doesn't rely on events for processing.
    """
    def __init__(self, core, library):
        self._core = core
        self._core.set_controller(self)
        self.log = getLogger("ctrl")

        self._library = library
        self._channel_out = multiprocessing.Queue()
        self._channel_in = multiprocessing.Queue()

        self.elements = {}  # ID -> element in simulation
        self._top_level_elements = []

        self._simulation_rate = 1  # Ratio between SUs and wall-clock time
        self._last_process_time = 0  # Remembers last process return time

        self._action_handlers = {
            'create': self._on_create,
            'update': self._on_update,
            'delete': self._on_update,
            'query': self._on_query,
            'connect': self._on_connect,
            'disconnect': self._on_disconnect,
            'quit': self._on_quit
        }

    def get_interface(self):
        return Interface(self._channel_in)

    def connect_handler(self, handler):
        handler._connect(self.get_channel_out())

    def get_core(self):
        return self._core

    def get_channel_in(self):
        return self._channel_in

    def get_channel_out(self):
        return self._channel_out

    def _on_create(self, command):
        parent = self.elements.get(command.get("parent"))
        guid = command['GUID']
        element = self._library.instantiate(
            guid,
            parent if parent else self,
            command['metadata'])

        element_id = element.id()
        self.elements[element_id] = element
        self.log.info("Instantiated %s as %d", guid, element_id)

        element.updated()

    def _on_update(self, command):
        element_id = command['id']
        element = self.elements[element_id]
        element.set_metadata_fields(command['metadata'])

        self.log.info("Updated %d with %s", command['id'], command['metadata'])

    def _on_delete(self, command):
        deleted_elements = self.elements[command['id']].destruct()

        for element_id in deleted_elements:
            del self.elements[element_id]
            # Since the element can't effectively self-destruct propagate
            # this event after removing them from the controller
            self.propagate_change({'id': element_id, 'GUID': None})

        self.log.info("Delete %s", command)

    def _on_query(self, command):
        uid = command['id']
        element = self.elements[uid]
        self.propagate_change(element.get_metadata())

        self.log.info("Queried for %d", uid)

    def _on_connect(self, command):
        source = self.elements[command['source_id']]
        sink = self.elements[command['sink_id']]

        if not source.connect(sink,
                              command['source_port'],
                              command['sink_port']):
            self.log.warning("Failed to connect %d port %d to %d port %d",
                             command['source_id'],
                             command['source_port'],
                             command['sink_id'],
                             command['sink_port'])
            return

        self.log.info("Connected %d port %d to %d port %d",
                      command['source_id'],
                      command['source_port'],
                      command['sink_id'],
                      command['sink_port'])

    def _on_disconnect(self, command):
        source = self.elements[command['source_id']]
        source.disconnect(command['source_port'])

        self.log.info("Disconnected port %d of %d",
                      command['source_id'],
                      command['source_port'])

    def _on_quit(self, command):
        self.log.info("Asked to quit")
        self._core.quit()

    def process(self, current_clock):
        """
        Processes commands queued in input channel and handles simulation
        timing management.

        :return: Tuple consisting of maximum simulation time and wall clock
        time before returning to this processing function.
        """

        while not self._channel_in.empty():  # Many chances. Race ok
            command = self._channel_in.get_nowait()  # Single consumer

            action = command.get('action')
            handler = self._action_handlers.get(action)
            if not handler:
                raise TypeError("Unknown action type {0}".format(action))

            handler(command)

        return self._delay_accordingly(current_clock)

    def _delay_accordingly(self, current_clock):
        scheduling_interval = 0.05  # Seconds till reschedule of process

        elapsed_time = time.clock() - self._last_process_time

        if elapsed_time < scheduling_interval:
            # FIXME: Not very content with this. Limits our resolution a lot.
            #        Should be fine for interactive use but will suck for
            #        interfacing with say an outside circuit. Not that I expect
            #        us to do a PWM but 20Hz _if_ things go right isn't that
            #        great. It's totally fixable though. Should switch to a
            #        min{next_event, control_proc_schedule} with busy loop for
            #        small delays. In any case I'm not sure how much much
            #        timing precision we can squeeze out this anyways.
            time.sleep(scheduling_interval - elapsed_time)

        # Set target clock independently of history. This prevents the
        # simulation from trying to "catch" up. Imho the right way for
        # interactive control. If this behavior is wanted we should switch
        # from a delta to an absolute simulation time calculation.
        target_clock = current_clock + \
            self._simulation_rate * scheduling_interval

        self._last_process_time = time.clock()
        return target_clock, self._last_process_time + scheduling_interval

    def propagate_change(self, data):
        """
        Function for propagating events up into the simulation frontend.
        Propagation follows child-parent-relationships so parent elements
        can employ filtering.

        :param data: metadata update message.
        """
        self._channel_out.put(data)

    def get_library(self):
        """
        :return: Library instance this controller is working with.
        """
        return self._library

    def child_added(self, child):
        """
        Top level elements of the simulation will register themselves
        with they controller using this function.

        :param child:
        :return:
        """
        self._top_level_elements.append(child)
