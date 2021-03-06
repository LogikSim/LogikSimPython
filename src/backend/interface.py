#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import queue
import random
from backend.component_library import gen_component_id


class Handler:
    """
    The handler class can be registered with a controller for receiving
    access to item updates outside of the backend.
    """
    def __init__(self):
        self._channel_in = None

    def _connect(self, channel_in):
        """
        Used by Controller to connect handler.

        :param channel_in: Channel poll will take updates from.
        """
        self._channel_in = channel_in

    def poll_blocking(self, timeout=None):
        """
        Blocks for updates with given timeout and processes exactly one of
        them once it becomes available.
        :return: True if handled one event, false if timeout was reached
        """
        assert self._channel_in is not None, \
            "Handler must be connected to controller"

        try:
            self.handle(self._channel_in.get(timeout=timeout))
        except queue.Empty:
            return False

        return True

    def poll(self):
        """
        Called to process queued up updates in correct process context.
        Calls handle once for each request.
        :return: True if no more updates to handle. False if some remain.
        """
        assert self._channel_in is not None, \
            "Handler must be connected to controller"

        while not self._channel_in.empty() and \
                self.handle(self._channel_in.get_nowait()):
            pass

        return self._channel_in.empty()

    def handle(self, update):
        """
        This method will receive updates in the form of data dictionaries.
        :return: True to keep processing. False to abort current poll loop.
        """
        pass


class Interface:
    """
    The interface class allows cross-thread RPC style interaction
    with the backend controller.
    """
    def __init__(self, channel_out):
        """

        :param channel_out:
        :return:
        """
        self._channel_out = channel_out

    def batch_context(self):
        """
        Returns a context that can be used to queue up multiple
        commands as a batch. You can retrieve the request id of
        the context from the context member request_id after the
        context closes. Replies will be marked with a batch-id
        equal to the request id of this batch command.
        """
        return self._BatchCommand(self)

    def set_simulation_properties(self, properties):
        """
        Sets the given properties for the simulation.

        :param properties: Dict with properties to set
        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'set-simulation-properties',
                'properties': properties,
                'request-id': request_id
            }
        )

        return request_id

    def query_simulation_properties(self):
        """
        Queries the current simulation properties from the backend.
        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'query-simulation-properties',
                'request-id': request_id
            }
        )

        return request_id

    def schedule_edge(self, element_id, input, state, delay):
        """
        Schedules a signal transition in the future.

        :param element_id: Element to schedule signal transition on
        :param input: Input pin index
        :param state: State to transition to
        :param delay: Time in simulation units to delay edge
        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'edge',
                'id': element_id,
                'input': input,
                'state': state,
                'delay': delay,
                'request-id': request_id
            }
        )

        return request_id

    def create_element(self, guid, parent=None, additional_metadata={}):
        """
        Schedules creation of an element with the given GUID.

        GUID must already be registered with core component library.

        :param guid: Type of element to create
        :param parent: Optional parent element id
        :param additional_metadata: Additional meta-data to create element with
        :return: Tuple of request id, ID of the element after its creation
        """

        request_id = self._gen_request_id()
        element_id = additional_metadata.get('id')
        if element_id is None:
            element_id = gen_component_id()

        self._channel_out.put(
            {
                'type': 'create',
                'GUID': guid,
                'id': element_id,
                'parent': parent,
                'metadata': additional_metadata,
                'request-id': request_id
            }
        )

        return request_id, element_id

    def serialize(self, ids=None):
        """
        Schedules full serialization of the given list of element IDs.
        :param ids: List of IDs. If non everything is serialized.
        :return: Request id
        """
        request_id = self._gen_request_id()

        request = {
            'type': 'serialize',
            'request-id': request_id
        }

        if ids is not None:
            request['ids'] = ids

        self._channel_out.put(request)

        return request_id

    def deserialize(self, serialization):
        """
        Schedules deserialization.

        :param serialization: Output of previous serialize call.
        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'deserialize',
                'data': serialization,
                'request-id': request_id
            }
        )

        return request_id

    def enumerate_components(self):
        """
        Asks the backend to enumerate all component GUIDs registered
        with the backend. The reply not only includes the GUIDs but
        also the corresponding ComponentType metadata.

        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'enumerate_components',
                'request-id': request_id
            }
        )

        return request_id

    def update_element(self, element_id, changed_metadata={}):
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'update',
                'id': element_id,
                'metadata': changed_metadata,
                'request-id': request_id
            }
        )

        return request_id

    def delete_element(self, element_id):
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'delete',
                'id': element_id,
                'request-id': request_id
            }
        )

        return request_id

    def request_element_information(self, element_id):
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'query',
                'id': element_id,
                'request-id': request_id
            }
        )

        return request_id

    def connect(self, source_id, source_port, sink_id, sink_port, delay=0):
        """
        Schedules a connection of the source_port of the to the sink_port.

        :param source_id: Source element id
        :param source_port: Source port index
        :param sink_id: Sink element id
        :param sink_port: Sink port index
        :param delay: Natural delay of the connection on propagation
        :return: Request id
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'connect',
                'source_id': source_id,
                'source_port': source_port,
                'sink_id': sink_id,
                'sink_port': sink_port,
                'delay': delay,
                'request-id': request_id
            }
        )

        return request_id

    def disconnect(self, source_id, source_port):
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'disconnect',
                'source_id': source_id,
                'source_port': source_port,
                'request-id': request_id
            }
        )

        return request_id

    def exit(self):
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'quit',
                'request-id': request_id
            }
        )

        return request_id

    @classmethod
    def _gen_request_id(cls):
        """
        Generates a unique request id that will be included in replies
        from the backend that result from the request.
        :return: Unique id
        """
        return random.getrandbits(128)

    def _post_batch(self, commands):
        """
        Post a number of separate commands as a batch command.
        """
        request_id = self._gen_request_id()

        self._channel_out.put(
            {
                'type': 'batch',
                'commands': commands,
                'request-id': request_id
            }
        )

        return request_id

    class _BatchCommand:
        """
        Context class for batching multiple interface commands
        to have them executes in the backend without the possibility
        of outside interference. Does _not_ perform a rollback if
        any of the commands fail. The request ID the command is posted
        with is saved as the request_id member on this class.
        """
        def __init__(self, interface):
            self._interface = interface
            self._commands = []

        def __enter__(self):
            assert len(self._commands) == 0

            class Q:
                @classmethod
                def put(cls, command):
                    self._commands.append(command)

            return Interface(Q)

        def __exit__(self, type, value, traceback):
            self.request_id = self._interface._post_batch(self._commands)
