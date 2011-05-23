#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on May 20, 2011

@author: Christian
'''

import unittest
import operator

from simulation_model import LogicValue


LV_0, LV_1, LV_X = map(LogicValue, '01X')

class ParserTest(unittest.TestCase):
    def test_LV_values(self):
        self.assertListEqual([LV_0, LV_1, LV_X], map(LogicValue, '01X'))
    
    def test_str_representations(self):
        self.assertListEqual(map(str, [LV_0, LV_1, LV_X]), list('01X'))
        self.assertListEqual(map(repr, [LV_0, LV_1, LV_X]), 
            ["LogicValue('0')", "LogicValue('1')", "LogicValue('X')"])
    
    def test_constructor(self):
        self.assertRaises(ValueError, LogicValue, 'b')
    
    def  test_slots(self):
        lv = LogicValue('0')
        self.assertRaises(AttributeError, setattr, lv, 'test', 0)
        
    def test_eq(self):
        """ == """
        self.assertListEqual(map(operator.eq, 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [True] * 3)
        
        self.assertListEqual(map(operator.eq, 
                [LogicValue('0'), LogicValue('0'), LogicValue('1')], 
                [LogicValue('1'), LogicValue('X'), LogicValue('X')]), 
                [False] * 3)
        
        self.assertFalse(LogicValue('0') == '0')
        
    def test_neq(self):
        """ != """
        self.assertListEqual(map(operator.ne, 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [False] * 3)
        
        self.assertListEqual(map(operator.ne, 
                [LogicValue('0'), LogicValue('0'), LogicValue('1')], 
                [LogicValue('1'), LogicValue('X'), LogicValue('X')]), 
                [True] * 3)
        
        self.assertTrue(LogicValue('0') != '0')
    
    def test_hash(self):
        self.assertSetEqual({LV_0, LV_1, LV_X}, 
                {LogicValue('0'), LogicValue('1'), LogicValue('X'), 
                 LogicValue('0'), LogicValue('1'), LogicValue('X')})
    
    def test_and(self):
        """ & """
        self.assertListEqual(map(operator.and_, 
                [LogicValue('0'), LogicValue('0'), LogicValue('0')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_0, LV_0])
        
        self.assertListEqual(map(operator.and_, 
                [LogicValue('1'), LogicValue('1'), LogicValue('1')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_1, LV_X])
        
        self.assertListEqual(map(operator.and_, 
                [LogicValue('X'), LogicValue('X'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_X, LV_X])
        
        lv1, lv2 = LogicValue('0'), LogicValue('1')
        self.assertIsNot(lv1, lv1 & lv2)
        self.assertIsNot(lv2, lv1 & lv2)
    
    def test_iand(self):
        """ &= """
        a = LogicValue('1')
        b = LogicValue('0')
        b &= a
        self.assertEqual(b, LV_0)
    
    def test_or(self):
        """ | """
        self.assertListEqual(map(operator.or_, 
                [LogicValue('0'), LogicValue('0'), LogicValue('0')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_1, LV_X])
        
        self.assertListEqual(map(operator.or_, 
                [LogicValue('1'), LogicValue('1'), LogicValue('1')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_1, LV_1, LV_1])
        
        self.assertListEqual(map(operator.or_, 
                [LogicValue('X'), LogicValue('X'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_X, LV_1, LV_X])
        
        lv1, lv2 = LogicValue('0'), LogicValue('1')
        self.assertIsNot(lv1, lv1 | lv2)
        self.assertIsNot(lv2, lv1 | lv2)
    
    def test_xor(self):
        """ ^ """
        self.assertListEqual(map(operator.xor, 
                [LogicValue('0'), LogicValue('0'), LogicValue('0')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_1, LV_X])
        
        self.assertListEqual(map(operator.xor, 
                [LogicValue('1'), LogicValue('1'), LogicValue('1')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_1, LV_0, LV_X])
        
        self.assertListEqual(map(operator.xor, 
                [LogicValue('X'), LogicValue('X'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_X, LV_X, LV_X])
        
        lv1, lv2 = LogicValue('0'), LogicValue('1')
        self.assertIsNot(lv1, lv1 ^ lv2)
        self.assertIsNot(lv2, lv1 ^ lv2)
    
    def test_add(self):
        """ + """
        self.assertListEqual(map(operator.add, 
                [LogicValue('0'), LogicValue('0'), LogicValue('0')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_0, LV_X, LV_X])
        
        self.assertListEqual(map(operator.add, 
                [LogicValue('1'), LogicValue('1'), LogicValue('1')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_X, LV_1, LV_X])
        
        self.assertListEqual(map(operator.add, 
                [LogicValue('X'), LogicValue('X'), LogicValue('X')], 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_X, LV_X, LV_X])
        
        lv1, lv2 = LogicValue('0'), LogicValue('1')
        self.assertIsNot(lv1, lv1 + lv2)
        self.assertIsNot(lv2, lv1 + lv2)
    
    def test_invert(self):
        """ ~ """
        self.assertListEqual(map(operator.inv, 
                [LogicValue('0'), LogicValue('1'), LogicValue('X')]), 
                [LV_1, LV_0, LV_X])
        
        lv1 = LogicValue('0')
        self.assertIsNot(lv1, ~lv1)

    def test_bool(self):
        """ if """
        self.assertRaises(ValueError, bool, LV_0)
        self.assertRaises(ValueError, lambda: True if LV_0 else False)
        
    def test_not(self):
        """ not """
        self.assertRaises(ValueError, lambda: not LV_0)
    
    def test_descriptor_class_level_get(self):
        lv = LogicValue('0')
        class Test(object):
            value = lv
        self.assertIs(Test.value, lv)
    
    def test_descriptor_class_level_set(self):
        class Test(object):
            value = LogicValue('0')
        o = object()
        Test.value = o
        self.assertIs(Test.value, o)
    
    def test_descriptor_class_level_delete(self):
        class Test(object):
            value = LogicValue('0')
        del Test.value
        self.assertRaises(AttributeError, getattr, Test, 'value')
    
    def test_descriptor_default_value(self):
        class Test_0(object):
            value = LogicValue('0')
        class Test_1(object):
            value = LogicValue('1')
        class Test_X(object):
            value = LogicValue('X')
        # class level
        self.assertListEqual(map(lambda o: getattr(o, 'value'), 
                [Test_0, Test_1, Test_X]), [LV_0, LV_1, LV_X])
        # instance level
        self.assertListEqual(map(lambda o: getattr(o, 'value'), 
                [Test_0(), Test_1(), Test_X()]), [LV_0, LV_1, LV_X])
        
    def test_descriptor_instance_level_set(self):
        class Test(object):
            value = LogicValue('0')
        test = Test()
        self.assertEqual(test.value, LV_0)
        # set string
        test.value = '1'
        self.assertEqual(test.value, LV_1)
        # set logic value
        lv = LogicValue('X')
        test.value = lv
        self.assertEqual(test.value, LV_X)
        self.assertIsNot(test.value, lv)
        # set invalid type
        self.assertRaises(TypeError, setattr, test, 'value', 1)
    
    def test_descriptor_instance_level_get(self):
        class Test(object):
            value = LogicValue('0')
        test1, test2 = Test(), Test()
        self.assertListEqual([test1.value, test2.value], [LV_0, LV_0])
        test1.value = '1'
        test2.value = 'X'
        self.assertListEqual([test1.value, test2.value], [LV_1, LV_X])
        # specificy that we always the same instance
        v1 = test1.value
        v2 = test1.value
        self.assertIs(v1, v2)
        # even after change!
        test1.value = '0'
        v1 = test1.value
        test1.value = '1'
        v2 = test1.value
        self.assertIs(v1, v2)
    
    def test_descriptor_instance_level_delete(self):
        class Test(object):
            value = LogicValue('0')
        test = Test()
        keys = test.__dict__.keys()
        test.value = '1'
        del test.value
        self.assertListEqual(test.__dict__.keys(), keys)
        self.assertEqual(test.value, LV_0) # default value
    
    def test_copy_state(self):
        lv = lv1 = LogicValue('0')
        self.assertEqual(lv, LV_0)
        lv.copy_from(LogicValue('1'))
        self.assertEqual(lv, LV_1)
        self.assertIs(lv, lv1)
        lv.copy_from(LogicValue('X'))
        self.assertEqual(lv, LV_X)
        self.assertIs(lv, lv1)
