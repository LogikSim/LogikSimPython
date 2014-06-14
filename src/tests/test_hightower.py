#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Test the hightower algorithm.
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




        
def area_to_input_data(area):
    lines = area.split('\n')
    search_rect = [(-1, -1), 
                   (max(len(line) for line in lines), len(lines))]
    assert area.count('A') == area.count('B') == 1
    
    blocks = set([])
    sol_point = {}
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == 'A':
                point_a = x, y
            elif char == 'B':
                point_b = x, y
            elif char in ['+', '-', '|']:
                blocks.add((x, y))
            elif char in map(str, range(10)):
                sol_point[int(char)] = x, y
    
    def is_point_free(p):
        return p not in blocks
    
    high_input = point_a, point_b, is_point_free, search_rect
    exp_res = ([point_a] + [sol_point[i] for i in sorted(sol_point)] + 
               [point_b])
    return high_input, exp_res





class HightowerSpec(unittest.TestCase):
    
    def test_same_points(self):
        point_a = (10, 5)
        point_b = (10, 5)
        is_point_free = lambda p: True
        search_rect = [(0, 0), (100, 100)]
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    search_rect)
        
        self.assertListEqual([(10, 5), (10, 5)], res)
    
    def test_horizontal(self):
        point_a = (10, 5)
        point_b = (15, 5)
        is_point_free = lambda p: True
        search_rect = [(0, 0), (100, 100)]
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    search_rect)
        
        self.assertListEqual([(10, 5), (15, 5)], res)
    
    def test_empty_space(self):
        point_a = (10, 5)
        point_b = (15, 10)
        is_point_free = lambda p: True
        search_rect = [(0, 0), (100, 100)]
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    search_rect)
        
        self.assertTrue(res == [(10, 5), (15, 5), (15, 10)] or
                        res == [(10, 5), (10, 10), (15, 10)], res)
    
    def test_horizontal_blocking_object(self):
        point_a = ( 5, 15)
        point_b = (25, 15)
        is_point_free = (lambda p: not(10 < p[0] < 20 and
                                       10 < p[1] < 20))
        search_rect = [(0, 0), (30, 30)]
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    search_rect)
        
        self.assertTrue(res == [(5, 15), (5, 10), (25, 10), (25, 15)] or
                        res == [(5, 15), (5, 20), (25, 20), (25, 15)], res)
    
    def test_vertical_blocking_object(self):
        point_a = (15,  5)
        point_b = (15, 25)
        is_point_free = (lambda p: not(10 < p[0] < 20 and
                                       10 < p[1] < 20))
        search_rect = [(0, 0), (30, 30)]
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    search_rect)
        
        self.assertTrue(res == [(15, 5), (10, 5), (10, 25), (15, 25)] or
                        res == [(15, 5), (20, 5), (20, 25), (15, 25)], res)
    
    
    def test_paper_problem_one(self):
        area = """
                                                      
          1                        2                  
                         +--------+ +                 
                         |          |                 
                         |   B     3|                 
                         |          |                 
             +           +----------+                 
             |                                        
          A  |                                        
             +                                        
                                                      
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
    
    
    def test_narrow_hall(self):
        area = """
                  + +
                  | |
                  |A|
             +----+ |
         2         1|
         B   +------+
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        self.assertListEqual(res, exp_res)
    
    
    def test_narrow_cave_entry(self):
        area = """
         2         1
                  + +
                  | |
                  |A|
             +----+ |
             |      |
         B   +------+
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
    
    
    def test_cave_unsolvable(self):
        area = """
             +-----+
             |     |
             |  A  |
             |     |
         B   +-----+
        """
        
        high_input, _ = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertEqual(res, None)
    
    
    def test_escape_point_loop(self):
        area = """
                                 
               +---+             
          1 A  |   |              
               |   +-----+        
             +-+   +---+ |       
             |     | B | |       
             | +---+   | |       
           +-+ |  4  5 | |       
           |   |    +--+ |       
           +---+    |    |       
          2       3 +----+       
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
    
    
    @unittest.skip("Probably unsolvable by Hightower")
    def test_escape_zigzag_valley(self):
        area = """
                  + 1 A + 
                  |     | 
                +-+     | 
                |3  2+--+ 
            +---+  +-+    
            | B  4 |      
            +------+      
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
    
    
    def test_refinement_2_example_1(self):
        area = """
          2                   1      
            +-----------+            
            |           |   +         
            |           |   | A       
        +   |           |   +         
        | B |           +             +
        |   |              +-------+  +
        +---+                         
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
    
    
    def test_refinement_2_example_2(self):
        area = """
          1       2    
               +-+     
          A    | |     
               +-+ 
           +-+         
           | |    B
           | |
          ++ |
          |  |
          +--+     
        """
        
        high_input, exp_res = area_to_input_data(area)
        res = hightower_line_search(*high_input)
        
        self.assertListEqual(res, exp_res)
