#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

import base_graphics_framework

class SymbolScene(base_graphics_framework.BasicGridScene):
    def __init__(self, *args, **kargs):
        super(SymbolScene, self).__init__(*args, **kargs)
        # set scene size
        height = 100 * 1000 # golden ratio
        self.setSceneRect(0, 0, height * (1+5**0.5)/2, height)


class SymbolView(
            base_graphics_framework.SelectItemsMode, 
            base_graphics_framework.InsertItemMode,
            base_graphics_framework.BasicGridView):
    def __init__(self, *args, **kargs):
        super(SymbolView, self).__init__(*args, **kargs)
        self.setScene(SymbolScene(self))
        self.setMouseMode(base_graphics_framework.SelectItemsMode)

