#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest
from backend.controller import Controller
from helpers import CallTrack


class ElementMock:
    def __init__(self, metadata=None):
        self._metadata = metadata if metadata else {}

    def id(self):
        return self.get_metadata_field('id')

    def get_metadata_field(self, field, default=None):
        return self._metadata.get(field, default)

    def set_metadata_fields(self, data, propagate=True):
        self._metadata.update(data)


class ControllerTest(unittest.TestCase):
    """
    Unit and integration tests for backend controller.
    """

    def test_element_creation(self):
        id_counter = 0

        def instantiate_mock(guid, parent, metadata):
            nonlocal id_counter
            id_counter += 1
            return ElementMock({'GUID': guid,
                                'id': id_counter})

        library_emu = CallTrack(tracked_member="instantiate",
                                result_fu=instantiate_mock)

        ctrl = Controller(core=None, library=library_emu)
        i = ctrl.get_interface()

        i.create_element("FOO")
        i.create_element("BAR")

        ctrl.process(0)

        self.assertListEqual([("FOO", ctrl, {}),
                              ("BAR", ctrl, {})], library_emu())

        self.assertEqual(id_counter, 2)

    def test_element_update(self):
        id_counter = 0
        data = {}

        def instantiate_mock(guid, parent, metadata):
            nonlocal id_counter
            nonlocal data

            id_counter += 1

            data = {'GUID': guid,
                    'id': id_counter,
                    'foo': 'bar',
                    'a': 'b'}

            return ElementMock(data)

        library_emu = CallTrack(tracked_member="instantiate",
                                result_fu=instantiate_mock)

        ctrl = Controller(core=None, library=library_emu)
        i = ctrl.get_interface()

        i.create_element("FOO")
        i.update_element(1, {'foo': 'buz',
                             'bernd': 'bread'})

        ctrl.process(0)

        self.assertEqual(1, id_counter)
        self.assertDictEqual({'GUID': 'FOO',
                              'id': 1,
                              'foo': 'buz',
                              'bernd': 'bread',
                              'a': 'b'}, data)

    def test_controller_element_root_parent_interface(self):
        class Lib:
            pass

        lib = Lib()

        ctrl = Controller(core=None, library=lib)

        # def propagate_change(self, data)
        ctrl.propagate_change({'id': 1,
                               'foo': 'bar'})

        # def get_library(self):
        self.assertIs(lib, ctrl.get_library())
        self.assertListEqual([{'id': 1,
                               'foo': 'bar'}],
                             list(ctrl.get_channel_out().queue))

        # def child_added(self, child):
        class El:
            pass

        e = El()
        ctrl.child_added(e)

        self.assertListEqual([e], ctrl._top_level_elements)
