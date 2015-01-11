#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.controller import Controller
from backend.interface import Handler
from tests.helpers import CallTrack, drain_queue
from backend.component_library import ComponentLibrary
from backend.components import And, Nand
from tests import helpers
import queue


class ElementMock:
    def __init__(self, metadata=None):
        self._metadata = metadata if metadata else {}

    def id(self):
        return self.get_metadata_field('id')

    def get_metadata_field(self, field, default=None):
        return self._metadata.get(field, default)

    def set_metadata_fields(self, data, propagate=True):
        self._metadata.update(data)

    def get_metadata(self):
        return self._metadata

    def updated(self):
        pass


class CoreMock:
    def __init__(self):
        self.clock = 0

    def set_controller(self, controller):
        # Make sure we crash immediatly instead of continuing execution
        # if we encounter exceptions in the controller
        controller._reraise_exceptions = True


class ControllerTest(helpers.CriticalTestCase):
    """
    Unit and integration tests for backend controller.
    """

    def test_element_creation(self):
        inst_counter = 0
        ids = []

        def instantiate_mock(guid, el_id, parent, metadata):
            nonlocal inst_counter
            inst_counter += 1
            ids.append(el_id)
            return ElementMock({'GUID': guid,
                                'id': el_id})

        library_emu = CallTrack(tracked_member="instantiate",
                                result_fu=instantiate_mock)

        ctrl = Controller(core=CoreMock(), library=library_emu,
                          queue_type=queue.Queue)

        i = ctrl.get_interface()

        i.create_element("FOO")
        i.create_element("BAR")

        ctrl.process(0)

        self.assertListEqual([("FOO", ids[0], ctrl, {}),
                              ("BAR", ids[1], ctrl, {})], library_emu())

        self.assertEqual(inst_counter, 2)

    def test_element_update(self):
        ids = []
        data = {}

        def instantiate_mock(guid, el_id, parent, metadata):
            nonlocal data
            nonlocal ids

            ids.append(el_id)

            data = {'GUID': guid,
                    'id': el_id,
                    'foo': 'bar',
                    'a': 'b'}

            return ElementMock(data)

        library_emu = CallTrack(tracked_member="instantiate",
                                result_fu=instantiate_mock)

        ctrl = Controller(core=CoreMock(), library=library_emu,
                          queue_type=queue.Queue)

        i = ctrl.get_interface()

        i.create_element("FOO")
        ctrl.process(0)

        i.update_element(ids[0], {'foo': 'buz',
                                  'bernd': 'bread'})

        ctrl.process(0)

        self.assertEqual(1, len(ids))
        self.assertDictEqual({'GUID': 'FOO',
                              'id': ids[0],
                              'foo': 'buz',
                              'bernd': 'bread',
                              'a': 'b'}, data)

    def test_controller_element_root_parent_interface(self):
        class Lib:
            pass

        lib = Lib()

        ctrl = Controller(core=CoreMock(), library=lib,
                          queue_type=queue.Queue)

        # def propagate_change(self, data)
        ctrl.propagate_change({'id': 1,
                               'foo': 'bar'})

        self.assertListEqual([{'type': 'change',
                               'clock': 0,
                               'data': {'id': 1,
                                        'foo': 'bar'}}],
                             drain_queue(ctrl.get_channel_out()))

        # def get_library(self):
        self.assertIs(lib, ctrl.get_library())

        # def child_added(self, child):
        class El:
            pass

        e = El()
        ctrl.child_added(e)

        self.assertListEqual([e], ctrl._top_level_elements)

    def test_controller_handler(self):
        updates = []

        class HandlerMock(Handler):
            def handle(self, update):
                if update['type'] != 'alive':
                    updates.append(update)
                return True

        root = None

        def instantiate_mock(guid, el_id, parent, metadata):
            nonlocal root
            root = parent
            return ElementMock({'GUID': guid,
                                'id': el_id})

        handler = HandlerMock()
        library_emu = CallTrack(tracked_member="instantiate",
                                result_fu=instantiate_mock)

        ctrl = Controller(core=CoreMock(), library=library_emu,
                          queue_type=queue.Queue)

        ctrl.connect_handler(handler)

        i = ctrl.get_interface()
        i.create_element("FOO")

        ctrl.process(0)

        root.propagate_change({'foo': 'bar'})
        root.propagate_change({'fiz': 'buz'})

        handler.poll()

        self.assertListEqual([{'type': 'change',
                               'clock': 0,
                               'data': {'foo': 'bar'}},
                              {'type': 'change',
                               'clock': 0,
                               'data': {'fiz': 'buz'}}], updates)


class ControllerSerializationTest(helpers.CriticalTestCase):
    def setUp(self):
        super().setUp()

        cl = ComponentLibrary()
        cl.register(And)
        cl.register(Nand)

        self.ctrl = Controller(core=CoreMock(), library=cl,
                               queue_type=queue.Queue)

        self.interface = self.ctrl.get_interface()

    def test_empty_serialization(self):
        rid = self.interface.serialize()
        self.ctrl.process(0)
        msg = drain_queue(self.ctrl.get_channel_out(),
                          lambda m: m['type'] != 'alive')
        self.assertEqual(1, len(msg))
        self.assertDictEqual({'type': 'serialization',
                              'in-reply-to': rid,
                              'clock': 0,
                              'data': []}, msg[0])

    def test_empty_deserialization(self):
        rid = self.interface.deserialize([])
        self.ctrl.process(0)
        msg = drain_queue(self.ctrl.get_channel_out(),
                          lambda m: m['type'] != 'alive')
        self.assertEqual(2, len(msg))
        self.assertDictEqual({'type': 'deserialization-start',
                              'clock': 0,
                              'in-reply-to': rid}, msg[0])
        self.assertDictEqual({'type': 'deserialization-end',
                              'clock': 0,
                              'in-reply-to': rid,
                              'ids': []}, msg[1])

    def test_serialization_framing(self):
        # Create some nested elements
        _, a1 = self.interface.create_element(And.GUID())
        _, a2 = self.interface.create_element(And.GUID(), a1)
        _, a3 = self.interface.create_element(And.GUID(), a1)
        self.interface.connect(a2, 0, a3, 1)
        self.interface.create_element(And.GUID(), a3)

        # Serialize them (ordering guarantees they exist)
        rid = self.interface.serialize()

        self.ctrl.process(0)

        msg = drain_queue(self.ctrl.get_channel_out(),
                          lambda m: m['type'] != 'alive')
        data = msg[-1]

        self.assertEqual('serialization', data['type'])
        self.assertEqual(rid, data['in-reply-to'])

        rid = self.interface.deserialize(data['data'])

        self.ctrl.process(1)

        msg = drain_queue(self.ctrl.get_channel_out(),
                          lambda m: m['type'] != 'alive')

        self.assertEqual('deserialization-start', msg[0]['type'])
        self.assertEqual(rid, msg[0]['in-reply-to'])

        self.assertEqual('deserialization-end', msg[-1]['type'])
        self.assertEqual(rid, msg[-1]['in-reply-to'])
