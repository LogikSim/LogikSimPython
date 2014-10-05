#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtCore, QtGui
from actions.ActionStack import ActionStack

class ActionStackModel(QtCore.QAbstractListModel):
    """
    Takes ownership of the given action stack and exposes it
    to UI components in a consistent way.
    """
    def __init__(self, action_stack = None, parent = None):
        super().__init__(parent)

        self.action_stack = action_stack or ActionStack(self)
        # Temporary row count limit is used to keep the model consistent
        # when executing a drop of undone actions during a execute(d) which
        # we otherwise cannot signal als row deletions and additions to Qt
        self.temporary_row_count_limit = None

    def rowCount(self, parent = QtCore.QModelIndex()):
        if parent.isValid():
            return 0

        if self.temporary_row_count_limit:
            return self.temporary_row_count_limit

        return self.action_stack.count()

    def data(self, index, role):
        if not index.isValid() or index.column() != 0:
            return None

        if index.row() < 0 or index.row() >= self.rowCount():
            return None

        action = self.action_stack.command(index.row())
        has_been_undone = index.row() >= self.action_stack.index()

        if role == QtCore.Qt.DisplayRole:
            return action.actionText()
        elif role == QtCore.Qt.ForegroundRole:
            #FIXME: Should probably use system palette derived color, a delegate or a user defined role for this
            if has_been_undone:
                return QtGui.QBrush(QtCore.Qt.lightGray)
            else:
                return None

        return None

    def headerData(self, section, orientation, role):
        if section != 0 or orientation != QtCore.Qt.Horizontal:
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.tr("Action")

    # Wrap the parts of ActionStack we need. Likely will end up
    # with big parts of QUndoStack wrapper but there's not really a
    # cleaner way

    def _push_action_wrap(fun):
        """
        This decorator works around the fact that Qt models have
        to signal insertions and deletions of rows separately while
        the undo stack push operations drop undone actions and push
        the new one in one step.

        The idea is to start a removal, execute the full push and limit
        the model so the pushed action isn't visible immediately. Now
        we can end the deletion, start the insertion, remove the limit
        end inserting and we are done and have kept the model consistent.

        :param fun: Function executing push to wrap
        :return: Wrapped fun
        """
        def model_push(self, *args, **kwargs):
            insertion_index = self.action_stack.index()

            will_drop_undone_actions = insertion_index < self.action_stack.count()

            if will_drop_undone_actions:
                first_undone = self.action_stack.index()
                last_undone = self.action_stack.count() - 1
                self.beginRemoveRows(QtCore.QModelIndex(), first_undone, last_undone)

                self.temporary_row_count_limit = insertion_index

            ret = fun(self, *args, **kwargs)

            if will_drop_undone_actions:
                self.endRemoveRows()

            self.beginInsertRows(QtCore.QModelIndex(), insertion_index, insertion_index)
            self.temporary_row_count_limit = None
            self.endInsertRows()

            return ret

        return model_push

    @_push_action_wrap
    def executed(self, redo, undo, description):
        return self.action_stack.executed(redo, undo ,description)

    executed.__doc__ = ActionStack.executed.__doc__

    @_push_action_wrap
    def execute(self, do, undo, description):
        return self.action_stack.execute(do, undo, description)

    execute.__doc__ = ActionStack.execute.__doc__

    @QtCore.Slot()
    def undo(self):
        if self.action_stack.canUndo():
            last_command_index = self.index(self.action_stack.index() - 1)
            self.action_stack.undo()
            new_last_command_index = self.index(self.action_stack.index() - 1)

            self.dataChanged.emit(new_last_command_index, last_command_index)

    undo.__doc__ = ActionStack.undo.__doc__

    @QtCore.Slot()
    def redo(self):
        if self.action_stack.canRedo():
            last_undone_command_index = self.index(self.action_stack.index())
            self.action_stack.redo()
            new_last_undone_command_index = self.index(self.action_stack.index())

            self.dataChanged.emit(last_undone_command_index, new_last_undone_command_index)

    redo.__doc__ = ActionStack.redo.__doc__

    def canUndo(self):
        return self.action_stack.canUndo()

    canUndo.__doc__ = ActionStack.canUndo.__doc__

    def canRedo(self):
        return self.action_stack.canRedo()

    canRedo.__doc__ = ActionStack.canRedo.__doc__

