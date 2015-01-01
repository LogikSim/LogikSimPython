#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Resize actions are used to resize logic items in the scene.
'''

from .state_action import StateAction


class ResizeAction(StateAction):
    """Mergeable resize action for logic items."""
    def __init__(self, group_id, item, old_size, old_pos, new_size, new_pos):
        """
        Implement state action for resizable logic items.

        :param old_size: old size given as int
        :param old_pos: old position as QPointF
        :param new_size: new size given as int
        :param new_pos: new position as QPointF

        See StateAction for more info.
        """
        super().__init__("resize item", group_id, item, (old_size, old_pos),
                         (new_size, new_pos))

    def redo_item_state(self, item, state):
        item.set_input_count_and_pos(*state)

    def undo_item_state(self, item, state):
        item.set_input_count_and_pos(*state)
