#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.simple_element import SimpleElement


class And(SimpleElement):
    def __init__(self, input_count=2):
        super().__init__(
            logic_function=lambda inputs: [all(inputs)],
            input_count=input_count)


class Or(SimpleElement):
    def __init__(self, input_count=2):
        super().__init__(
            logic_function=lambda inputs: [any(inputs)],
            input_count=input_count)


class Xor(SimpleElement):
    def __init__(self, input_count=2):
        super().__init__(
            logic_function=lambda inputs: [sum(inputs) == 1],
            input_count=input_count)


class Nand(SimpleElement):
    def __init__(self, input_count=2):
        super().__init__(
            logic_function=lambda inputs: [not all(inputs)],
            input_count=input_count)


class Nor(SimpleElement):
    def __init__(self, input_count=2):
        super().__init__(
            logic_function=lambda inputs: [not any(inputs)],
            input_count=input_count)
