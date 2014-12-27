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

from .state_action import StateAction


class MoveAction(StateAction):
    """Mergeable move action for items."""
    def __init__(self, group_id, item, old_pos, new_pos):
        """
        Implement state action for movable items.

        :param old_pos: old position as QPointF
        :param new_pos: new position as QPointF

        See StateAction for more info.
        """
        super().__init__("moved item", group_id, item, old_pos, new_pos)

    def redo_item_state(self, item, pos):
        item.set_temporary(True)
        item.setPos(pos)
        item.set_temporary(False)

    def undo_item_state(self, item, pos):
        item.set_temporary(True)
        item.setPos(pos)
        item.set_temporary(False)
