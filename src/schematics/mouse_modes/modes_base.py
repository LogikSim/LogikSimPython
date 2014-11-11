#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Creates the mode for all interactive grid views.
'''

from ..interactive_grid_view import InteractiveGridView
import modes

GridViewMouseModeBase, mouse_mode_filtered = modes.generate_mode_base(
    InteractiveGridView, 'mouse')
