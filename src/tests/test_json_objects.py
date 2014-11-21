#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Test the json data format as used in the simulation model.
'''

import unittest

from simulation_model import JsonMeta, json_virtual, JsonObject


class JsonMetaSpec(unittest.TestCase):
    def setUp(self):
        JsonMeta._json_classes.clear()

    def test_setUp(self):
        self.assertEqual(JsonMeta._json_classes, {})

    def test_registration(self):
        class Test(JsonObject):
            pass

        obj = JsonMeta.load_object({'type': 'Test'})
        self.assertTrue(isinstance(obj, Test))
        self.assertIs(type(obj), Test)
        # error on wrong data
        self.assertRaises(Exception, JsonMeta.load_object, 'Test')
        self.assertRaises(Exception, JsonMeta.load_object, {'none': 'Test'})
        self.assertRaises(Exception, JsonMeta.load_object, {'type': 'wrong'})

    def test_unregister(self):
        class Test(JsonObject):
            pass

        JsonMeta.unregister_json_class(Test)
        self.assertRaises(Exception, JsonMeta.load_object, {'type': 'Test'})

    def test_json_virtual(self):
        @json_virtual
        class Test(JsonObject):
            pass

        self.assertRaises(Exception, JsonMeta.load_object, {'type': 'Test'})


class JsonObjectSpec(unittest.TestCase):
    def setUp(self):
        JsonMeta._json_classes.clear()

    def test_setUp(self):
        self.assertEqual(JsonMeta._json_classes, {})

    def test_load_unknown_type(self):
        class Test(JsonObject):
            pass

        obj = JsonMeta.load_object({'type': 'Test'})
        self.assertEqual(type(obj), Test)
        self.assertRaises(Exception, JsonMeta.load_object, {'type': 'fail'})

    def test_default_constructor(self):
        class Test(JsonObject):
            pass

        obj = Test()
        self.assertEqual(type(obj), Test)

    def test_extra_config_values(self):
        class Test(JsonObject):
            def __init__(self, json_data=None):
                super(Test, self).__init__(json_data=json_data)
                if json_data is not None:
                    self.value = json_data['value']
                else:
                    self.value = None

        obj = JsonMeta.load_object({'type': 'Test', 'value': 'res'})
        self.assertEqual(type(obj), Test)
        self.assertEqual(obj.value, 'res')

    def test_validate_object(self):
        class Test(JsonObject):
            pass

        JsonMeta.validate_data({'type': 'Test'})
        self.assertRaises(Exception, JsonMeta.validate_data, {'type': 'fail'})
        self.assertRaises(Exception, JsonMeta.validate_data, [])
        self.assertRaises(Exception, JsonMeta.validate_data, 1)
        self.assertRaises(Exception, JsonMeta.validate_data, 'Test')

    def test_save(self):
        class Test(JsonObject):
            pass

        obj = Test()
        self.assertDictEqual(obj.save(), {'type': 'Test'})
        JsonMeta.validate_data(obj.save())
