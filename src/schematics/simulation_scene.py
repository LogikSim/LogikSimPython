#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Grid scene supporting simulation of the shown schematic.
'''

from threading import Thread

from backend.core import Core
from backend.controller import Controller
from backend.component_library import get_library
from . import grid_scene
from logicitems.item_registry import ItemRegistry
from symbols.and_item import AndItem


class SimulationScene(grid_scene.GridScene):
    """Extends GridScene to support simulation of the shown schematic."""
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        # Setup simulation backend for this scene
        self._core = Core()
        self._controller = Controller(self._core, get_library())
        self._interface = self._controller.get_interface()

        self._registry = ItemRegistry(self._controller, self)
        self._registry.register_type(AndItem)
        self._registry.start_handling()

        self._core_thread = Thread(target=self._core.run)
        self._core_thread.start()

        # Join threads on destruct (mustn't be a slot on this object)
        self.destroyed.connect(lambda: [self._core.quit(),
                                        self._core_thread.join()])

    def get_interface(self):
        return self._interface

    def get_registry(self):
        return self._registry
