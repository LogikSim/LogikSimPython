#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#


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

    def create_element(self, guid, parent=None, additional_metadata={}):
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
