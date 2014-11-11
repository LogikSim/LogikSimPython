#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
The symbol widget is used to define or edit user created logic elements.
'''

from . import mouse_modes
from . import grid_scene


class EditSymbolView(mouse_modes.SelectItemsMode,
                     mouse_modes.InsertItemMode):
    def __init__(self, *args, **kargs):
        super().__init__(self, *args, **kargs)
        self.setScene(grid_scene.GridScene(self))
        self.setMouseMode(mouse_modes.SelectItemsMode)
