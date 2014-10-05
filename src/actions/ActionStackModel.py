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
    def __init__(self, base_action, action_stack = None, parent = None):
        super().__init__(parent)

        self.action_stack = action_stack or ActionStack(self)
        # Temporary row count limit is used to keep the model consistent
        # when executing a drop of undone actions during a execute(d) which
        # we otherwise cannot signal als row deletions and additions to Qt
        self.temporary_row_count_limit = None

        self.base_action = base_action

        # React to index changes on the action stack triggered by our actions. Has to be queued as
        # we mustn't handle this immediately on when we might still be fiddling around with the model
        # state. If we queue the signal we know it will be deferred until our functions complete.
        self.action_stack.indexChanged.connect(self._stackIndexChanged, QtCore.Qt.QueuedConnection)

    def reset(self, base_action):
        self.beginResetModel()
        self.base_action = base_action
        self.action_stack.clear()
        self.endResetModel()

    def rowCount(self, parent = QtCore.QModelIndex()):
        if parent.isValid():
            return 0

        if self.temporary_row_count_limit:
            return self.temporary_row_count_limit

        return self.action_stack.count() + 1

    def data(self, index, role):
        if not index.isValid() or index.column() != 0:
            return None

        if index.row() < 0 or index.row() >= self.rowCount():
            return None

        if index.row() == 0:
            # Special case first row
            if role != QtCore.Qt.DisplayRole:
                return None

            return self.base_action

        stack_index = index.row() - 1
        action = self.action_stack.command(stack_index)
        has_been_undone = stack_index >= self.action_stack.index()

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
            stack_insertion_index = self.action_stack.index()

            will_drop_undone_actions = stack_insertion_index < self.action_stack.count()

            if will_drop_undone_actions:
                stack_first_undone = self.action_stack.index()
                stack_last_undone = self.action_stack.count() - 1
                self.beginRemoveRows(QtCore.QModelIndex(), stack_first_undone + 1, stack_last_undone+ 1)

                self.temporary_row_count_limit = stack_insertion_index + 1

            ret = fun(self, *args, **kwargs)

            if will_drop_undone_actions:
                self.endRemoveRows()

            self.beginInsertRows(QtCore.QModelIndex(), stack_insertion_index + 1, stack_insertion_index + 1)
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
            last_command_model_index = self.index(self.action_stack.index())
            self.action_stack.undo()
            new_last_command_model_index = self.index(self.action_stack.index())

            self.dataChanged.emit(new_last_command_model_index, last_command_model_index)

    undo.__doc__ = ActionStack.undo.__doc__

    @QtCore.Slot()
    def redo(self):
        if self.action_stack.canRedo():
            last_undone_command_model_index = self.index(self.action_stack.index() + 1)
            self.action_stack.redo()
            new_last_undone_command_model_index = self.index(self.action_stack.index() + 1)

            self.dataChanged.emit(last_undone_command_model_index, new_last_undone_command_model_index)

    redo.__doc__ = ActionStack.redo.__doc__

    def canUndo(self):
        return self.action_stack.canUndo()

    canUndo.__doc__ = ActionStack.canUndo.__doc__

    def canRedo(self):
        return self.action_stack.canRedo()

    def undoRedoToIndex(self, modelIndex):
        """
        Given a model index attempts to undo or redo the stack to the given index
        so that index is the last executed operation. Similar to QUndoStack::setIndex
        but using model indexes and offset by + 1.

        :param modelIndex: QModelIndex to undo or redo to
        :return: True if the index could be reached.
        """
        if not modelIndex.isValid() or modelIndex.column() != 0:
            return False

        targetStackIndex = modelIndex.row()
        if targetStackIndex > self.action_stack.count():
            return False

        currentIndex = self.action_stack.index()
        if currentIndex == targetStackIndex:
            return True

        self.action_stack.setIndex(targetStackIndex)
        newIndex = self.action_stack.index()

        (first, last) = (newIndex, currentIndex) if newIndex <= currentIndex else (currentIndex, newIndex)

        self.dataChanged.emit(first, last)

        completed = (newIndex == targetStackIndex)

        return completed

    currentModelIndexChanged = QtCore.Signal(QtCore.QModelIndex)

    @QtCore.Slot(int)
    def _stackIndexChanged(self, index):
        """
        Reacts to index changes in the action stack and converts them to
        a model index change other parts of the application might want
        to react to.
        """
        # As index always point to last done + 1 it maps one to one to our model rows.
        self.currentModelIndexChanged.emit(self.index(index))

    canRedo.__doc__ = ActionStack.canRedo.__doc__

