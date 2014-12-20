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


class ComponentLibraryTests(unittest.TestCase):
    """
    Unit tests for component library
    """

    def test_component_instantiation(self):
        lib = cl.get_library()
        a = lib.instantiate_type(And.GUID())
        self.assertEqual("And", a.get_metadata_field("name"))

        x = lib.instantiate_type(Xor.GUID())
        self.assertEqual("Xor", x.get_metadata_field("name"))

    def test_invalid_behavior(self):
        lib = cl.get_library()

        self.assertRaises(AssertionError, lib.instantiate_type, "UNOBTAINIUM")
