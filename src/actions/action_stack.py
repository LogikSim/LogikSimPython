#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.

from PySide import QtGui

from actions.action import Action


class ActionStack(QtGui.QUndoStack):
    """
    Small wrapper around QtGui.UndoStack with some convenience functions.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def executed(self, redo, undo, description):
        """
        Creates an already performed Action from parameters and puts it onto
        the action stack.

        :param redo: Function called to redo the action if undone
        :param undo: Function called to undo the action
        :param description: Short user facing description of the action
        :return: The created action
        """
        first = True

        # Work around QUndoStack.push always executing the action on push
        def redoButIgnoreFirstCall():
            nonlocal first
            if first:
                first = False
                return
            redo()

        action = Action(redoButIgnoreFirstCall, undo, description)
        self.push(action)

        return action

    def execute(self, do, undo, description):
        """
        Creates an Action, executes it and puts it onto the action stack.

        :param do: Function called to do or redo the action
        :param undo: Function called to undo the action
        :param description: Short user facing description of the action
        :return: The created action
        """
        action = Action(do, undo, description)
        self.push(action)

        return action
