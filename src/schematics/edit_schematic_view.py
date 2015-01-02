#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines the schematic view used to create and visualize logic circuits.
'''

from . import mouse_modes
from . import grid_scene


class EditSchematicView(mouse_modes.SelectItemsMode,
                        mouse_modes.InsertItemMode,
                        mouse_modes.InsertLineMode,
                        mouse_modes.InsertConnectorMode,
                        mouse_modes.TriggerEdgeMode):
    """Combines all mouse modes to edit schematics."""

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setScene(grid_scene.GridScene(self))
        self.setMouseMode(mouse_modes.SelectItemsMode)
