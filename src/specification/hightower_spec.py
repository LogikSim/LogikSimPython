#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

import unittest

from algorithms.hightower import (do_lines_intersect, is_point_on_line, 
                                  hightower_line_search)


class DoLinesIntersectSpec(unittest.TestCase):
    def test_lines_1(self):
        line_a = ((10,0), ( 10,100))
        line_b = (( 0,5), (100,  5))
        res = do_lines_intersect(line_a, line_b)
        self.assertTrue(res)
        
    def test_lines_1_flipped(self):
        line_a = (( 0,5), (100,  5))
        line_b = ((10,0), ( 10,100))
        res = do_lines_intersect(line_a, line_b)
        self.assertTrue(res)
        
    def test_lines_2(self):
        line_a = ((10,0), ( 10,100))
        line_b = ((11,5), (100,  5))
        res = do_lines_intersect(line_a, line_b)
        self.assertFalse(res)
        
    def test_lines_2_flipped(self):
        line_a = ((11,5), (100,  5))
        line_b = ((10,0), ( 10,100))
        res = do_lines_intersect(line_a, line_b)
        self.assertFalse(res)


class IsPointOnLine(unittest.TestCase):
    def test_point_line_1(self):
        point = (10, 5)
        line = ((0, 5), (100, 5))
        res = is_point_on_line(point, line)
        self.assertTrue(res)
        
    def test_point_line_2(self):
        point = (10, 5)
        line = ((10, 0), (10, 100))
        res = is_point_on_line(point, line)
        self.assertTrue(res)



class HightowerSpec(unittest.TestCase):
    
    def test_same_points(self):
        point_a = (10, 5)
        point_b = (10, 5)
        is_point_free = lambda x: True
        is_point_out_bounds = (lambda x: not(0 <= x[0] <= 100 and 
                                             0 <= x[1] <= 100))
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    is_point_out_bounds)
        
        print("res = ", res)
        # TODO: improve assertion
        self.assertTrue(len(res) != 0)
    
    def test_horizontal(self):
        point_a = (10, 5)
        point_b = (15, 5)
        is_point_free = lambda x: True
        is_point_out_bounds = (lambda x: not(0 <= x[0] <= 100 and 
                                             0 <= x[1] <= 100))
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    is_point_out_bounds)
        
        print("res = ", res)
        # TODO: improve assertion
        self.assertTrue(len(res) != 0)
