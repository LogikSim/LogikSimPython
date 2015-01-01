#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import multiprocessing
from backend.interface import Interface
from backend.component_library import ComponentRoot, gen_component_id
from backend.element import Edge
import time
from logging import getLogger


class Controller(ComponentRoot):
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

        self._message_handlers = {
            'create': self._on_create,
            'update': self._on_update,
            'delete': self._on_delete,
            'serialize': self._on_serialize,
            'deserialize': self._on_deserialize,
            'edge': self._on_edge,
            'query': self._on_query,
            'connect': self._on_connect,
            'disconnect': self._on_disconnect,
            'enumerate_components': self._on_enumerate_components,
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
        element_id = command['id']

        element = self._library.instantiate(
            guid,
            element_id,
            parent if parent else self,
            command['metadata'])

        self.elements[element_id] = element
        self.log.info("Instantiated %s as %d with %s", guid, element_id,
                      command['metadata'])

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

        self.log.info("Delete %s", command)

    def _on_serialize(self, command):
        elements = self._top_level_elements
        element_ids = command.get('ids')
        if element_ids is not None:
            elements = [self.elements[uid] for uid in element_ids]

        def _serialize(element):
            """
            Serialize element and instead of having a list of ids as children
            insert the serialized children themselves into the list.
            """
            data = element.get_metadata()
            data['children'] = [_serialize(c) for c in element.get_children()]
            return data

        serialization = [_serialize(element) for element in elements]

        self._post_to_frontend('serialization', {'data': serialization},
                               command.get('request-id'))

        self.log.info("Serialized %s", [e.id() for e in elements])

    def _on_deserialize(self, command):
        serialization = command['data']

        id_mappings = {}  # old id -> new id
        elements = {}  # new id -> element
        connections = {}  # element -> connections

        self._post_to_frontend('deserialization-start',
                               in_reply_to=command.get('request-id'))

        def _deserialize(datasets):
            for data in datasets:
                element_id = gen_component_id()
                id_mappings[data['id']] = element_id

                # Remove elements we have to rewrite or recreate at
                # later stages
                children = data.pop('children')
                del data['inputs']
                outgoing = data.pop('outputs')

                parent = elements.get(id_mappings.get(data.get('parent')))

                element = self._library.instantiate(
                    data['GUID'],
                    element_id,
                    parent if parent else self,
                    data)

                element.updated()

                elements[element_id] = element
                connections[element] = outgoing

                _deserialize(children)

        _deserialize(serialization)

        for element, connections in connections.items():
            for (out_port, (old_target, in_port)) in enumerate(connections):
                if old_target is None:
                    continue

                target = elements.get(id_mappings.get(old_target))
                if target:
                    # Only reconnect if target was part of serialization
                    element.connect(target, out_port, in_port)

        self._post_to_frontend('deserialization-end',
                               {'ids': list(elements.keys())},
                               command.get('request-id'))

        self.log.info("Deserialized %s", list(elements.keys()))

    def _on_edge(self, command):
        """
        Triggers an edge at a point in the future.

        :param command: Command of the form:
            { 'type': 'edge',
              'id': element_id,
              'input': input,
              'state': state,
              'delay': delay }
        """
        element = self.elements[command['id']]
        core = self.get_core()
        core.schedule(Edge(core.clock + command['delay'],
                           element,
                           command['input'],
                           command['state']))

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

    def _on_enumerate_components(self, command):
        self._post_to_frontend('enumerate_components',
                               {'data': self._library.enumerate_types()},
                               command.get('request-id'))

        self.log.info("Enumerated component types")

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

            message_type = command.get('type')
            handler = self._message_handlers.get(message_type)
            if not handler:
                raise TypeError("Unknown message type {0}"
                                .format(message_type))

            handler(command)

        self._post_to_frontend('alive')

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
        Function for propagating changes up into the simulation frontend.
        Propagation follows child-parent-relationships so parent elements
        can employ filtering.

        :param data: metadata update message.
        """
        self._post_to_frontend('change', {'data': data})

    def _post_to_frontend(self,
                          message_type,
                          additional_fields={},
                          in_reply_to=None):
        """
        Places a message to the frontend queue using the default framing.

        :param message_type: Type of the message being sent
        :param additional_fields: Message specific data fields
        :param in_reply_to: If given marks message as in reply to request id
        """
        message = {
            'type': message_type,
            'clock': self.get_core().clock,  # Only always current clock
        }

        if in_reply_to is not None:
            message['in-reply-to'] = in_reply_to

        message.update(additional_fields)

        self._channel_out.put(message)

    def get_library(self):
        """
        :return: Library instance this controller is working with.
        """
        return self._library

    def child_added(self, child):
        """
        Top level elements of the simulation will register themselves
        with the controller using this function.

        :param child:
        :return:
        """
        self._top_level_elements.append(child)
