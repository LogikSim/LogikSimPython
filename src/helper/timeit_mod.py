#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Time functions on each call and print statistics on the console.
'''

import time


def timeit(f):
    """ Decorator to time functions on each call and print stats """
    # min, max, sum, count
    store = [1.E16, 0, 0, 0]

    def timeit_wrapper(*args, **kargs):
        t = time.clock()
        try:
            return f(*args, **kargs)
        finally:
            t = (time.clock() - t) * 1000  # in ms
            store[0] = min(store[0], t)
            store[1] = max(store[1], t)
            store[2] += t
            store[3] += 1
            print(f.__name__ + ": min: %6.2f ms, max: %6.2f ms, "
                  "mean: %6.2f ms, last: %6.2f ms" % (store[0], store[1],
                                                      store[2] / store[3], t))

    return timeit_wrapper
