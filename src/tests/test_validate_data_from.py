#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Test json data validation system as used in the simulation model.
'''

import unittest
import numbers

from simulation_model import JsonMeta, JsonObject


validate = JsonMeta.validate_data_from_spec


class ValidateJsonData(unittest.TestCase):
    def setUp(self):
        JsonMeta._json_classes.clear()

    def test_setUp(self):
        self.assertEqual(JsonMeta._json_classes, {})

    def test_string(self):
        validate(str, 'a')
        validate(str, 'a')
        self.assertRaises(TypeError, validate, str, 1)

    def test_int(self):
        validate(numbers.Integral, 1)
        validate(numbers.Integral, int(1))
        self.assertRaises(TypeError, validate, numbers.Integral, 1.5)

    def test_real(self):
        validate(float, 1.0)
        self.assertRaises(TypeError, validate, float, 1)

    def test_true_false(self):
        validate(bool, True)
        validate(bool, False)
        self.assertRaises(TypeError, validate, bool, 1)

    def test_dict_type_checking(self):
        validate({'a': float}, {'a': 1.})
        self.assertRaises(TypeError, validate, {'a': float}, {'a': 1})

    def test_missing_dict_items(self):
        validate({'a': float}, {'a': 1.})
        self.assertRaises(KeyError, validate, {'a': float}, {})
        self.assertRaises(KeyError, validate, {'a': float}, {'b': 1.})

    def test_variable_length_array(self):
        validate([float, numbers.Integral], [])
        validate([float, numbers.Integral], [1])
        validate([float, numbers.Integral], [1.])
        validate([float, numbers.Integral], [int(1)])
        validate([float, numbers.Integral], [1, 2., 3, 4., int(5)])
        self.assertRaises(TypeError, validate,
                          [float, numbers.Integral], [1, 2., 's', 4., int(5)])

    def test_fixed_structured_array_test_type_checking(self):
        validate((float, numbers.Integral), [1., 1])
        self.assertRaises(TypeError, validate,
                          (float, numbers.Integral), ['a', 1])

    def test_fixed_structured_array_test_length_checking(self):
        validate((float, numbers.Integral), [1., 1])
        validate((float,), [1.])
        self.assertRaises(ValueError, validate,
                          (float, numbers.Integral), [1, 1., 1.])

    def test_structured_array_stackering(self):
        spec = ((float, float), (float, float))
        validate(spec, [[1., 1.], [1., 1.]])
        self.assertRaises(Exception, validate,
                          spec, 's')
        self.assertRaises(Exception, validate,
                          spec, [[1., 1.], [1., 1.], [1., 1.]])
        self.assertRaises(Exception, validate,
                          spec, [[1., 1.], [1., 1., 1.]])
        self.assertRaises(Exception, validate,
                          spec, [[1., 1.], [1., 's']])

    def test_variable_length_array_of_structured_arrays(self):
        spec = [(float, float)]

        validate(spec, [])
        validate(spec, [[1., 1.]])
        validate(spec, [[0., 1.], [2., 3.]])

        self.assertRaises(Exception, validate,
                          spec, 's')
        self.assertRaises(Exception, validate,
                          spec, [[1., 1.], [1., 1., 1.]])
        self.assertRaises(Exception, validate,
                          spec, [[1., 1.], [1., 's']])

    def test_object(self):
        class Test(JsonObject):
            pass

        validate(Test, {'type': 'Test'})
        self.assertRaises(TypeError, validate, Test, {'type': 'Invalid'})
        self.assertRaises(KeyError, validate, Test, {})
        self.assertRaises(TypeError, validate, Test, 'abc')

    def test_virtual_object(self):
        class Test(JsonObject):
            pass

        validate(Test, {'type': 'Test'})
        type(Test).unregister_json_class(Test)
        self.assertRaises(Exception, validate, Test, {'type': 'Test'})

    def test_own_validate_method(self):
        class Test(JsonObject):
            @classmethod
            def validate_data(cls, data):
                super(Test, cls).validate_data(data)
                cls.validate_data_from_spec({'name': str}, data)

        validate(Test, {'type': 'Test', 'name': 'Test One'})
        self.assertRaises(Exception, validate, Test,
                          {'type': 'Invalid', 'name': 'Test One'})
        self.assertRaises(Exception, validate, Test,
                          {'type': 'Test', 'name': 1})

    def test_list_of_objects(self):
        class Test(JsonObject):
            pass

        spec = [(Test, numbers.Integral)]

        validate(spec, [])
        validate(spec, [[{'type': 'Test'}, 2]])
        validate(spec, [[{'type': 'Test'}, 1], [{'type': 'Test'}, 2]])

        self.assertRaises(Exception, validate, [[{'type': 'Test'}, 2]])
        self.assertRaises(Exception, validate, [[{'type': 'Invalid'}, 2]])
        self.assertRaises(Exception, validate, [[{'type': 'Test'}, 'b']])
        self.assertRaises(Exception, validate, [[2, {'type': 'Test'}]])
        self.assertRaises(Exception, validate, [{'type': 'Test'}])
