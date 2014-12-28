#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
import unittest

import backend.component_library as cl
from backend.components import And, Xor
from tests.mocks import ElementParentMock


class ComponentLibraryTests(unittest.TestCase):
    """
    Unit tests for component library
    """

    def test_component_instantiation(self):
        p = ElementParentMock()
        lib = cl.get_library()
        a = lib.instantiate(And.GUID(), 0, p)
        self.assertEqual("And", a.get_metadata_field("name"))

        x = lib.instantiate(Xor.GUID(), 1, p)
        self.assertEqual("Xor", x.get_metadata_field("name"))

    def test_invalid_behavior(self):
        lib = cl.get_library()

        self.assertRaises(AssertionError,
                          lib.instantiate,
                          "UNOBTAINIUM",
                          10,
                          None)

    def test_type_enumeration(self):
        lib = cl.ComponentLibrary()
        lib.register(And)
        lib.register(Xor)

        types = lib.enumerate_types()

        self.assertEqual(2, len(types))
        self.assertIn(And.get_metadata(), types)
        self.assertIn(Xor.get_metadata(), types)
