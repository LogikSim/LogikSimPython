#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Apr 28, 2014

@author: Christian
'''

import unittest

from algorithms.hightower import hightower_line_search

class HightowerSpec(unittest.TestCase):
    def test_horizontal(self):
        point_a = (10, 5)
        point_b = (15, 5)
        is_point_free = lambda x: True
        is_point_out_bounds = (lambda x: not(0 <= x[0] <= 100 and 
                                             0 <= x[1] <= 100))
        
        res = hightower_line_search(point_a, point_b, is_point_free, 
                                    is_point_out_bounds)
        
        print(res)
        raise Exception()
