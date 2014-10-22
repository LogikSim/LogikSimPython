#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
from PySide import QtGui

class Action(QtGui.QUndoCommand):
    """
    Small wrapper around QtGui.QUndoCommand which takes lambdas for redo and undo.
    Also sets given description as doc string for the class for easier debugging.
    """
    def __init__(self, redo, undo, description = None):
        super().__init__(description)
        self.__doc__ = description
        self.redo = redo
        self.undo = undo