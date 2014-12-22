#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from queue import Queue
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
        self.core = core
        self.channel_out = Queue()
        self.channel_in = Queue()

        self.elements = {}  # ID -> element in simulation
        self.connections = []  # (source_id, source_port, sink_id, sink_port)
        self.connect_from = {}  # ID -> port -> connection
        self.connect_to = {}  # ID -> port -> connection
        self.top_level_elements = []
        self.library = library

        self.simulation_rate = 1  # Ratio between SUs and wall-clock time
        self.last_process_time = 0  # Remembers last process return time

        self.action_handlers = {
            'create': self._on_create,
            'update': self._on_update,
            'delete': self._on_update,
            'query': self._on_query,
            'connect': self._on_connect,
            'quit': self._on_quit
        }

    def interface(self):
        return Interface(self.channel_in)

    def get_channel_in(self):
        return self.channel_in

    def get_channel_out(self):
        return self.channel_out

    def _on_create(self, command):
        parent = self.elements.get(command.get("parent"))
        element = self.library.instantiate(
            command['GUID'],
            self if not parent else parent,
            command['metadata'])

        element_id = element.id()
        self.elements[element_id] = element

    def _on_update(self, command):
        element = self.elements[command['id']]
        element.update_metadata_fields(command['metadata'])

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
        self.core.quit()

    def process(self, current_clock):
        """
        Processes commands queued in input channel and handles simulation
        timing management.

        :return: Tuple consisting of maximum simulation time and wall clock
        time before returning to this processing function.
        """

        while not self.channel_in.empty():  # We'll get another chance. Race ok
            command = self.channel_in.get_nowait()  # Single consumer

            action = command.get('action')
            handler = self.action_handlers.get(action)
            if not handler:
                raise TypeError("Unknown action type {0}".format(action))

            handler(command)

        return self._delay_accordingly(current_clock)

    def _delay_accordingly(self, current_clock):
        scheduling_interval = 0.04  # Seconds till reschedule of process

        elapsed_time = time.perf_counter() - self.last_process_time

        if elapsed_time < scheduling_interval:
            # FIXME: Not very content with this. Limits our resolution a lot.
            #        Should be fine for interactive use but will suck for
            #        interfacing with say an outside circuit. Not that I expect
            #        us to do a PWM but 20Hz _if_ things go right isn't that
            #        great. It's totally fixable though. Should switch to a
            #        min{next_event, control_proc_schedule} with busy loop for
            #        small delays. In any case I'm not sure how much much
            #        timing precision we can squeeze out of python anyways.
            time.sleep(scheduling_interval - elapsed_time)

        # Set target clock independently of history. This prevents the
        # simulation from trying to "catch" up. Imho the right way for
        # interactive control. If this behavior is wanted we should switch
        # from a delta to an absolute simulation time calculation.
        target_clock = current_clock + \
            self.simulation_rate * scheduling_interval

        self.last_process_time = time.perf_counter()
        return target_clock, self.last_process_time + scheduling_interval

    def propagate_change(self, data):
        """
        Function for propagating events up into the simulation frontend.
        Propagation follows child-parent-relationships so parent elements
        can employ filtering.

        :param data: metadata update message.
        """
        self.channel_out.put(data)

    def get_library(self):
        """
        :return: Library instance this controller is working with.
        """
        return self.library

    def child_added(self, child):
        """
        Top level elements of the simulation will register themselves
        with they controller using this function.

        :param child:
        :return:
        """
        self.top_level_elements.append(child)
