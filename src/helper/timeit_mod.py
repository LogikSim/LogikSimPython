#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Apr 26, 2011

@author: Christian
'''

import time

def timeit(f):
    # min, max, sum, count
    store = [1.E16, 0, 0, 0]
    def timeit_wrapper(*args, **kargs):
        t = time.clock()
        try:
            return f(*args, **kargs)
        finally:
            t = (time.clock() - t) * 1000 # in ms
            store[0] = min(store[0], t)
            store[1] = max(store[1], t)
            store[2] += t
            store[3] += 1
            print f.__name__ + ": min: %6.2f ms, max: %6.2f ms, " \
                    "mean: %6.2f ms, last: %6.2f ms" % (store[0], store[1], 
                    store[2] / store[3], t)
    return timeit_wrapper
