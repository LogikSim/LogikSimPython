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
        self._library = library
        self._channel_out = multiprocessing.Queue()
        self._channel_in = multiprocessing.Queue()

        self.elements = {}  # ID -> element in simulation
        self.connections = []  # (source_id, source_port, sink_id, sink_port)
        self.connect_from = {}  # ID -> port -> connection
        self.connect_to = {}  # ID -> port -> connection
        self._top_level_elements = []

        self._simulation_rate = 1  # Ratio between SUs and wall-clock time
        self._last_process_time = 0  # Remembers last process return time

        self._action_handlers = {
            'create': self._on_create,
            'update': self._on_update,
            'delete': self._on_update,
            'query': self._on_query,
            'connect': self._on_connect,
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
        element = self._library.instantiate(
            command['GUID'],
            parent if parent else self,
            command['metadata'])

        element_id = element.id()
        self.elements[element_id] = element

    def _on_update(self, command):
        element = self.elements[command['id']]
        element.set_metadata_fields(command['metadata'])

    def _on_delete(self, command):
        # Delete connections from first
        # The connections to
        # Then delete element
        raise NotImplementedError(command['action'])

    def _on_query(self, command):
        raise NotImplementedError(command['action'])

    def _on_connect(self, command):
        raise NotImplementedError(command['action'])

    def _on_quit(self, command):
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

        elapsed_time = time.perf_counter() - self._last_process_time

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

        self._last_process_time = time.perf_counter()
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
