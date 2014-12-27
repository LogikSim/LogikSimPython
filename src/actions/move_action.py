#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Move actions are used to move items in the scene.
'''

from PySide import QtGui


class MoveAction(QtGui.QUndoCommand):
    """Mergeable move action for items."""
    def __init__(self, group_id, item, old_pos, new_pos):
        """
        Create move action for item.

        It is assumed that the item is already moved.

        :param group_id: only actions with same undo redo group are merged
        :param item: scene item being moved
        :param old_pos: old position as QPointF
        :param new_pos: new position as QPointF
        """
        super().__init__("moved items")
        self._group_id = group_id
        self._data = {item: (old_pos, new_pos)}
        self._first_call = True

    def id(self):
        return id(MoveAction)

    def mergeWith(self, other):
        """Merge with newer move action."""
        do_merge = self._group_id == other._group_id != -1
        assert isinstance(other, MoveAction)

        for item, other_positions in other._data.items():
            if item in self._data:
                old_pos, _ = self._data[item]
                self._data[item] = old_pos, other_positions[1]
            else:
                self._data[item] = other_positions
        return do_merge

    def redo(self):
        # ignore first call
        if self._first_call:
            self._first_call = False
            return

        for item, positions in self._data.items():
            item.set_temporary(True)
            item.setPos(positions[1])
            item.set_temporary(False)

    def undo(self):
        for item, positions in self._data.items():
            item.set_temporary(True)
            item.setPos(positions[0])
            item.set_temporary(False)
