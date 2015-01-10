#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from backend.component_library import (get_library,
                                       ComponentLibrary,
                                       ComponentInstance,
                                       ComponentType)

from backend.components import And, Xor
from tests.mocks import ElementRootMock
from tests import helpers


class ComponentLibraryTests(helpers.CriticalTestCase):
    """
    Unit tests for component library
    """

    def test_component_instantiation(self):
        p = ElementRootMock()
        lib = get_library()
        a = lib.instantiate(And.GUID(), 0, p)
        self.assertEqual("And", a.get_metadata_field("name"))

        x = lib.instantiate(Xor.GUID(), 1, p)
        self.assertEqual("Xor", x.get_metadata_field("name"))

    def test_invalid_behavior(self):
        lib = get_library()

        self.assertRaises(AssertionError,
                          lib.instantiate,
                          "UNOBTAINIUM",
                          10,
                          None)

    def test_type_enumeration(self):
        lib = ComponentLibrary()
        lib.register(And)
        lib.register(Xor)

        types = lib.enumerate_types()

        self.assertEqual(2, len(types))
        self.assertIn(And.get_metadata(), types)
        self.assertIn(Xor.get_metadata(), types)

    def test_component_destruction(self):
        p = ElementRootMock()
        lib = get_library()
        a = lib.instantiate(And.GUID(), 0, p)
        b = lib.instantiate(And.GUID(), 1, a)
        lib.instantiate(And.GUID(), 2, b)
        lib.instantiate(And.GUID(), 3, b)

        self.assertListEqual([2, 3, 1], b.destruct())
        self.assertListEqual(
            [{'id': 2, 'GUID': None},
             {'id': 3, 'GUID': None},
             {'id': 1, 'GUID': None}], p.history)


class ComponentInstanceTests(helpers.CriticalTestCase):
    def setUp(self):
        super().setUp()

        class MyComponentType(ComponentType):
            METADATA = {'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F',
                        'key': 'value'}

            @classmethod
            def instantiate(cls, component_id, parent, additional_metadata):
                additional_metadata['id'] = component_id
                return MyComponent(parent, additional_metadata, cls)

        class MyComponent(ComponentInstance):
            def __init__(self, parent, metadata, component_type):
                super().__init__(parent, metadata, component_type)

        self.root = ElementRootMock('astringandnotalibrary')
        self.inst = MyComponentType.instantiate(0, self.root, {'foo': 'bar'})

    def test_metadata_field_query(self):
        self.assertEqual('bar', self.inst.get_metadata_field('foo'))
        self.assertEqual('value', self.inst.get_metadata_field('key'))
        self.assertEqual('mydefault',
                         self.inst.get_metadata_field('doesnotexist',
                                                      'mydefault'))

    def test_metadata_bulk_query(self):
        metadata = {'foo': 'bar',
                    'key': 'value',
                    'id': 0,
                    'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F'}

        self.assertDictEqual(metadata, self.inst.get_metadata())

    def test_metadata_set_field_propagation(self):
        self.inst.set_metadata_field('biz', 'buz')
        self.inst.set_metadata_field('biz', 'buz')
        self.inst.set_metadata_field('foo', 'bar')
        self.inst.set_metadata_field('foo', 'changed', propagate=False)
        self.assertEqual('buz', self.inst.get_metadata_field('biz'))
        # Make sure we only propagated the actual change and don't propagate
        # if we were asked not to
        self.assertListEqual([{'id': 0, 'biz': 'buz'}], self.root.history)

    def test_metadata_set_field(self):
        self.inst.set_metadata_field('key', 'changed')
        self.assertEqual('changed', self.inst.get_metadata_field('key'))
        # Make sure we didn't mess with the type
        self.assertEqual('value',
                         self.inst._component_type.get_metadata_field('key'))

        self.inst.set_metadata_field('new', 'shiny')
        self.assertEqual('shiny', self.inst.get_metadata_field('new'))

        metadata = {'foo': 'bar',
                    'key': 'changed',
                    'new': 'shiny',
                    'id': 0,
                    'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F'}

        self.assertDictEqual(metadata, self.inst.get_metadata())

    def test_metadata_set_fields(self):
        self.inst.set_metadata_fields({'key': 'changed',
                                       'new': 'shiny'})

        metadata = {'foo': 'bar',
                    'key': 'changed',
                    'new': 'shiny',
                    'id': 0,
                    'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F'}

        self.assertDictEqual(metadata, self.inst.get_metadata())

    def test_updated(self):
        self.inst.updated()
        self.assertEqual(1, len(self.root.history))

        metadata = {'foo': 'bar',
                    'key': 'value',
                    'id': 0,
                    'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F'}

        self.assertDictEqual(metadata, self.root.history[0])

    def test_get_library(self):
        self.assertEqual('astringandnotalibrary', self.inst.get_library())
