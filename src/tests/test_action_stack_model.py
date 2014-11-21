#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.

import unittest

from PySide import QtCore, QtGui

from actions.action_stack_model import ActionStackModel
from tests.helpers import CallTrack
from tests.mocks import ModelIndexMock


class DoUndoLog:
    """
    Helper class to keep track of undo/redo calls during testing.
    """
    DEFAULT_WHAT = "Thing"

    def __init__(self, log=None):
        self.log = log if log is not None else []

    def execute_args(self, what=DEFAULT_WHAT):
        """
        :return: execute(d) compatible tuple of do,undo,what
        """
        return (self.do_gen(what), self.undo_gen(what), what)

    def __call__(self, s=None, what=DEFAULT_WHAT):
        """
        Returns a real or virtual do/undo log for use in validation.

        :param s: If none returns the do/undo log. Otherwise creates one from the given string.
        :param what: If s is given determines the what used in log creation
        :return: Virtual or real do/undo log depending on parameters.
        """
        if s is None:
            return self.log

        log = []
        for c in s:
            if c == "+":
                log.append((True, what))
            else:
                log.append((False, what))

        return log

    def do_gen(self, what):
        def do():
            self.log.append((True, what))

        return do

    def undo_gen(self, what):
        def undo():
            self.log.append((False, what))

        return undo


class ActionStackModelTest(unittest.TestCase):
    """
    Tests actions.action_stack_model.ActionStackModel class with dependencies.
    """

    def setUp(self):
        self.app = QtCore.QCoreApplication.instance()
        if not self.app:
            # FIXME: Want self.app = QtCore.QCoreApplication([]) but tearDown can't really clean up that singleton
            self.app = QtGui.QApplication([])

        self.model = ActionStackModel("first")

    def test_execute(self):
        """
        Ensure that execute executes the do action and that it can be undone.
        """
        log = DoUndoLog()
        self.model.execute(*log.execute_args())
        self.assertEqual(log("+"), log())
        self.model.undo()
        self.assertEqual(log("+-"), log())
        self.assertEqual(2, self.model.rowCount())
        self.model.redo()
        self.assertEqual(log("+-+"), log())
        self.assertEqual(2, self.model.rowCount())

    def test_executed(self):
        """
        Ensure that executed does not execute the do action and can be undone.
        """
        log = DoUndoLog()
        self.model.executed(*log.execute_args())
        self.assertEqual(log(""), log())
        self.model.undo()
        self.assertEqual(log("-"), log())
        self.assertEqual(2, self.model.rowCount())
        self.model.redo()
        self.assertEqual(log("-+"), log())
        self.assertEqual(2, self.model.rowCount())

    def test_base_action(self):
        """
        Check we have the virtual first row with correct contents
        """
        self.assertEqual(1, self.model.rowCount())
        self.assertEqual(0, self.model.rowCount(self.model.index(0, 0)))  # Make sure we don't signal unexpected rows
        self.assertEqual("First", self.model.data(self.model.index(0, 0)))  # note the capital f

    def test_reset_model(self):
        """
        After a reset the model shouldn't have any lines and shouldn't be able to undo.
        """
        log = DoUndoLog()
        self.model.execute(*log.execute_args())
        self.model.reset("bernd")
        self.assertEqual(log("+"), log())  # Mustn't be undone
        self.assertEqual(1, self.model.rowCount())  # Other actions must be gone
        self.assertEqual("Bernd", self.model.data(self.model.index(0, 0)))  # New base_action text should be applied

    def test_undo_redo(self):
        """
        Checks if redo and undo works as expected and triggers the right signals.
        """
        log = DoUndoLog()
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())
        self.assertEqual(5, self.model.rowCount())
        self.model.undo()
        self.model.undo()
        self.model.undo()
        self.assertEqual(log("++++---"), log())
        self.assertEqual(5, self.model.rowCount())
        self.model.execute(*log.execute_args())
        self.assertEqual(log("++++---+"), log())
        self.assertEqual(3, self.model.rowCount())

    def test_clean_dirty(self):
        """
        Tests whether the model accurately tracks its dirty and clean state.
        """
        self.assertTrue(self.model.isClean())

        clean_log = CallTrack()
        self.model.cleanChanged.connect(clean_log.slot)
        log = DoUndoLog()

        # Check the model becomes dirty if changes happen
        self.model.execute(*log.execute_args())
        self.assertFalse(self.model.isClean())
        self.assertEqual([False], clean_log())

        # Check whether it becomes clean again if we undo them
        self.model.undo()
        self.assertTrue(self.model.isClean())
        self.assertEqual([False, True], clean_log())

        # Check whether we receive dirty callbacks only when things change
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())

        self.assertFalse(self.model.isClean())
        self.assertEqual([False, True, False], clean_log())

        # If we save the model we will manually declare it clean, check that behaves correctly
        self.model.setClean()
        self.assertTrue(self.model.isClean())
        self.assertEqual([False, True, False, True], clean_log())
        self.assertTrue(self.model.canUndo())  # This shouldn't affect the content of the stack

    def test_undo_redo_actions(self):
        """
        Tests whether the action generator for undo redo works correctly.
        Especially if they correctly track the changes in the model
        """

        # Check initial state and text
        undo_action = self.model.createUndoAction(prefix="undo")
        redo_action = self.model.createRedoAction(prefix="redo")

        self.assertFalse(undo_action.isEnabled())
        self.assertFalse(redo_action.isEnabled())

        self.assertEqual("undo ", undo_action.text())  # The space is expected
        self.assertEqual("redo ", redo_action.text())

        # Make sure we cannot break things by triggering them when disabled
        undo_action.trigger()
        redo_action.trigger()

        # Perform an action
        log = DoUndoLog()
        self.model.execute(*log.execute_args("this"))

        self.assertTrue(undo_action.isEnabled())
        self.assertFalse(redo_action.isEnabled())

        self.assertEqual("undo this", undo_action.text())
        self.assertEqual("redo ", redo_action.text())

        # Undo it
        undo_action.trigger()
        self.assertFalse(undo_action.isEnabled())
        self.assertTrue(redo_action.isEnabled())

        self.assertEqual("undo ", undo_action.text())
        self.assertEqual("redo this", redo_action.text())

        # Redo it, do another and undo that
        redo_action.trigger()
        self.model.execute(*log.execute_args("that"))
        undo_action.trigger()

        self.assertTrue(undo_action.isEnabled())
        self.assertTrue(redo_action.isEnabled())

        self.assertEqual("undo this", undo_action.text())
        self.assertEqual("redo that", redo_action.text())

        # Check reset
        self.model.reset()

        self.assertFalse(undo_action.isEnabled())
        self.assertFalse(redo_action.isEnabled())

        self.assertEqual("undo ", undo_action.text())  # The space is expected
        self.assertEqual("redo ", redo_action.text())

    def test_model_data(self):
        """
        Tests the models data methods
        """

        # Test header data usual and error cases
        self.assertEqual("Action", self.model.headerData(0, QtCore.Qt.Horizontal))  # Base case
        self.assertIsNone(self.model.headerData(1, QtCore.Qt.Horizontal))  # Invalid section
        self.assertIsNone(self.model.headerData(0, QtCore.Qt.Vertical))  # Invalid orientation
        self.assertIsNone(self.model.headerData(0, QtCore.Qt.Horizontal, QtCore.Qt.UserRole))  # Invalid role

        # Test data function in usual and error cases
        log = DoUndoLog()
        self.model.execute(*log.execute_args("this"))
        self.model.execute(*log.execute_args("that"))
        self.model.execute(*log.execute_args("foo"))
        self.model.execute(*log.execute_args("bar"))
        self.model.undo()
        self.model.undo()

        # Data display role
        self.assertEqual("First", self.model.data(self.model.index(0, 0)))
        self.assertEqual("This", self.model.data(self.model.index(1, 0)))
        self.assertEqual("That", self.model.data(self.model.index(2, 0)))
        self.assertEqual("Foo", self.model.data(self.model.index(3, 0)))
        self.assertEqual("Bar", self.model.data(self.model.index(4, 0)))
        self.assertIsNone(self.model.data(ModelIndexMock(5, 0)))  # OOB
        self.assertIsNone(self.model.data(ModelIndexMock(0, 1)))  # OOB
        self.assertIsNone(self.model.data(ModelIndexMock(0, 0, False)))  # Invalid

        # Data foreground role (used for undo indication)
        undone = QtGui.QBrush(QtCore.Qt.lightGray)
        self.assertIsNone(self.model.data(self.model.index(0, 0), QtCore.Qt.ForegroundRole))
        self.assertIsNone(self.model.data(self.model.index(1, 0), QtCore.Qt.ForegroundRole))
        self.assertIsNone(self.model.data(self.model.index(2, 0), QtCore.Qt.ForegroundRole))
        self.assertEqual(undone, self.model.data(self.model.index(3, 0), QtCore.Qt.ForegroundRole))
        self.assertEqual(undone, self.model.data(self.model.index(4, 0), QtCore.Qt.ForegroundRole))
        self.assertIsNone(self.model.data(ModelIndexMock(5, 0), QtCore.Qt.ForegroundRole))  # OOB
        self.assertIsNone(self.model.data(ModelIndexMock(0, 1), QtCore.Qt.ForegroundRole))  # OOB
        self.assertIsNone(self.model.data(ModelIndexMock(0, 0, False), QtCore.Qt.ForegroundRole))  # Invalid

        # Other roles and invalid inputs should return None
        self.assertIsNone(self.model.data(self.model.index(0, 0), QtCore.Qt.UserRole))  # First row is special cased
        self.assertIsNone(self.model.data(self.model.index(1, 0), QtCore.Qt.UserRole))

    def test_undo_redo_to_index(self):
        """
        Tests the models batch undo/redo functions
        """
        log = DoUndoLog()
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())
        self.model.execute(*log.execute_args())

        index_changes = CallTrack()
        self.model.currentModelIndexChanged.connect(index_changes.slot)

        # Undo all
        idx = self.model.index(0, 0)
        self.assertTrue(self.model.undoRedoToIndex(idx))
        self.app.processEvents()  # currentModelIndexChanged is queued. Process.
        self.assertEqual(log("++++----"), log())
        self.assertEqual(idx, index_changes()[-1])

        # Redo first
        idx = self.model.index(1, 0)
        self.assertTrue(self.model.undoRedoToIndex(idx))
        self.app.processEvents()
        self.assertEqual(log("++++----+"), log())
        self.assertEqual(idx, index_changes()[-1])

        # Redo rest
        idx = self.model.index(4, 0)
        self.assertTrue(self.model.undoRedoToIndex(idx))
        self.app.processEvents()
        self.assertEqual(log("++++----++++"), log())
        self.assertEqual(idx, index_changes()[-1])

        self.assertTrue(self.model.undoRedoToIndex(idx))  # Shouldn't do anything
        self.assertEqual(log("++++----++++"), log())
        self.assertEqual(idx, index_changes()[-1])

        # Check failure conditions
        self.assertFalse(self.model.undoRedoToIndex(ModelIndexMock(0, 0, False)))
        self.assertFalse(self.model.undoRedoToIndex(ModelIndexMock(0, 1, True)))
        self.assertFalse(self.model.undoRedoToIndex(ModelIndexMock(5, 0, True)))
        self.assertFalse(self.model.undoRedoToIndex(ModelIndexMock(-1, 0, True)))

    def test_redo_undo_signals(self):
        """
        There are various signals associated with undoing and redoing actions which are tested here.
        """
        can_redo_changed = CallTrack()
        redo_text_changed = CallTrack()

        self.model.canRedoChanged.connect(can_redo_changed.slot)
        self.model.redoTextChanged.connect(redo_text_changed.slot)

        can_undo_changed = CallTrack()
        undo_text_changed = CallTrack()

        self.model.canUndoChanged.connect(can_undo_changed.slot)
        self.model.undoTextChanged.connect(undo_text_changed.slot)

        log = DoUndoLog()

        about_to_undo_log_length = -1

        def about_to_undo_slot():
            nonlocal about_to_undo_log_length
            # As the aboutTo* slots should be called before the actual action
            # we persist the length of our undo/redo log. If this functions were
            # called beforehand they should have the length before the undo/redo.
            about_to_undo_log_length = len(log())

        about_to_redo_log_length = -1

        def about_to_redo_slot():
            nonlocal about_to_redo_log_length
            about_to_redo_log_length = len(log())

        self.model.aboutToUndo.connect(about_to_undo_slot)
        self.model.aboutToRedo.connect(about_to_redo_slot)

        # Check whether events track actions
        self.model.execute(*log.execute_args("this"))
        self.assertTrue(can_undo_changed()[-1])
        self.assertEqual("this", undo_text_changed()[-1])

        self.model.execute(*log.execute_args("that"))
        self.assertEqual("that", undo_text_changed()[-1])

        self.model.execute(*log.execute_args("foo"))
        self.assertEqual("foo", undo_text_changed()[-1])

        self.model.execute(*log.execute_args("bar"))
        self.assertEqual("bar", undo_text_changed()[-1])
        self.assertFalse(can_redo_changed()[-1])
        self.assertEqual("", redo_text_changed()[-1])

        self.model.undo()
        self.assertEqual(4, about_to_undo_log_length)
        self.model.undo()
        self.assertEqual(5, about_to_undo_log_length)

        self.assertEqual("foo", redo_text_changed()[-1])
        self.assertEqual("that", undo_text_changed()[-1])
        self.assertTrue(can_undo_changed()[-1])
        self.assertTrue(can_redo_changed()[-1])

        self.model.redo()
        self.assertEqual(6, about_to_redo_log_length)

        # Make sure the about to signals fire correctly for undoRedoToIndex
        prev_log_len = len(log())
        self.assertTrue(self.model.undoRedoToIndex(self.model.index(1, 0)))
        self.assertEqual(prev_log_len, about_to_undo_log_length)

        prev_log_len = len(log())
        self.assertTrue(self.model.undoRedoToIndex(self.model.index(3, 0)))
        self.assertEqual(prev_log_len, about_to_redo_log_length)

        self.model.reset()

        self.assertEqual("", redo_text_changed()[-1])
        self.assertEqual("", undo_text_changed()[-1])

        self.assertFalse(can_undo_changed()[-1])
        self.assertFalse(can_redo_changed()[-1])

    def tearDown(self):
        self.action_stack = None
        self.model = None
