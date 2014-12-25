#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
"""
Generator for generating a naive time-limited function.
"""
import time


class TimeReached(Exception):
    pass


def time_limited(fun, lifetime):
    """
    Decorator checking a time limit condition before calling the given
    function. Throws TimeReached exception after lifetime seconds. Note that
    this doesn't limit the actual execution time of fun but instead is meant
    to be used to wrap repeatedly called functions handed as callbacks to
    e.g. algorithms.

    :param fun: Function to decorate
    :param lifetime: Number of seconds after which calls to this function
        should throw or None for infinite lifetime.
    :return: decorated fun
    """
    if lifetime is None:
        return fun

    max_time = time.time() + lifetime

    def time_limited_execution(*args, **argv):
        if time.time() > max_time:
            raise TimeReached()

        return fun(*args, **argv)

    return time_limited_execution
