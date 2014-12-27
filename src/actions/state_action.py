#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
State actions track changes with merge support.
'''

from PySide import QtGui


class StateAction(QtGui.QUndoCommand):
    """Mergeable state action for items."""
    def __init__(self, text, group_id, item, old_state, new_state):
        """
        Create mergable state transition action for item.

        It is assumed that the item is already in new state.

        :param group_id: only actions with same undo redo group are merged
        :param item: scene item being moved
        :param old_state: old state (user defined)
        :param new_state: new state (user defined)
        """
        super().__init__(text)
        self._group_id = group_id
        self._data = {item: (old_state, new_state)}
        self._first_call = True

    def id(self):
        return id(type(self))

    def mergeWith(self, other):
        """Merge with newer state action."""
        do_merge = self._group_id == other._group_id != -1

        if do_merge:
            for item, other_states in other._data.items():
                if item in self._data:
                    old_state, _ = self._data[item]
                    self._data[item] = old_state, other_states[1]
                else:
                    self._data[item] = other_states
        return do_merge

    def redo(self):
        # ignore first call
        if self._first_call:
            self._first_call = False
            return

        for item, states in self._data.items():
            self.redo_item_state(item, states[1])

    def undo(self):
        for item, states in self._data.items():
            self.undo_item_state(item, states[0])

    def redo_item_state(self, item, state):
        """Redo state on given item"""
        raise NotImplemented

    def undo_item_state(self, item, state):
        """Undo state on given item"""
        raise NotImplemented
