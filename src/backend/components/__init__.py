#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.component_library import get_library

from backend.components.basic_logic_elements import And, Or, Xor, Nand, Nor, \
    register

from backend.components.interconnect import Interconnect
from backend.components.compound_element import CompoundElement, \
    InputOutputBank

register(get_library())  # Register components
get_library().register(Interconnect)
get_library().register(CompoundElement)
get_library().register(InputOutputBank)

__all__ = ('And', 'Or', 'Xor', 'Nand', 'Nor', 'Interconnect',
           'CompoundElement', 'InputOutputBank')
