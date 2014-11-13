#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Define the main window of the LogikSim GUI.
'''

from PySide import QtGui, QtCore

# import item_list_widget
import schematics
from ui_main_window import Ui_MainWindow
from settings import settings


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)

        # FIXME: Only a test setup, replace it by proper circuit instance handling
        self._view = schematics.EditSchematicView(self)
        self.tab_widget.addTab(self._view, self.tr("New circuit"))
        self.tab_widget.tabBar().hide()  # For now we only have one so hide

        # Build tool-bar
        self.tool_actions = QtGui.QActionGroup(self)
        self.tool_actions.triggered.connect(self._on_tool_action_triggered)

        self.tool_selection = self.tool_actions.addAction(QtGui.QIcon(":/resources/connection.png"),
                                                          self.tr("Selection (F1)"))
        self.tool_selection.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1))
        self.tool_logic = self.tool_actions.addAction(QtGui.QIcon(":/resources/and.png"),
                                                      self.tr("Insert Logic Items (F2)"))
        self.tool_logic.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F2))
        self.tool_connector = self.tool_actions.addAction(QtGui.QIcon(":/resources/or.png"),
                                                          self.tr("Insert Connectors (F3)"))
        self.tool_connector.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F3))
        self.tool_lines = self.tool_actions.addAction(QtGui.QIcon(":/resources/xor.png"), self.tr("Insert Lines (F4)"))
        self.tool_lines.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F4))

        for action in self.tool_actions.actions():
            action.setCheckable(True)

        self.tool_bar.addActions(self.tool_actions.actions())
        self.tool_selection.setChecked(True)

        scene = self._view.scene()

        actions = scene.actions

        self.action_stack_view.setModel(actions)

        # Prepend undo/redo QActions to menu_edit
        first_menu_edit_qaction = self.menu_edit.actions()[0] if len(self.menu_edit.actions()) > 0 else None

        undo_qaction = actions.createUndoAction(self)
        undo_qaction.setShortcut(QtGui.QKeySequence.Undo)
        self.menu_edit.insertAction(first_menu_edit_qaction, undo_qaction)

        redo_qaction = actions.createRedoAction(self)
        redo_qaction.setShortcut(QtGui.QKeySequence.Redo)
        self.menu_edit.insertAction(first_menu_edit_qaction, redo_qaction)

        # Add toggle view actions for dockwidgets
        self.toggle_history_dock_widget_view_qaction = self.history_dock_widget.toggleViewAction()
        self.menu_view.addAction(self.toggle_history_dock_widget_view_qaction)

        s = settings()
        # Restore layout
        self.restoreGeometry(s.main_window_geometry)
        self.restoreState(s.main_window_state)

    def closeEvent(self, event):
        s = settings()
        # Save layout
        s.main_window_geometry = self.saveGeometry()
        s.main_window_state = self.saveState()

    def view(self):
        return self._view

    @QtCore.Slot()
    def on_action_about_triggered(self):
        content = self.tr(
            "<p>A logic simulator that makes it easy and fun to explore and design digital circuits "
            "starting from simple AND gates, up to complex computing systems as we use them today.</b></p>"
            "<p>Copyright (C) 2011-2014 The LogikSim Authors</p>"
            "<p>Distribution of this application and its source is governed by the GNU GPLv3 license that can "
            "be found in the LICENSE.txt file.</p>"
            "<p>For more information visit <a href=\"http://www.logiksim.org\">www.logiksim.org</a></p>")

        QtGui.QMessageBox.about(self,
                                self.tr("About LogikSim"),
                                content)

    @QtCore.Slot()
    def on_action_about_qt_triggered(self):
        QtGui.QMessageBox.aboutQt(self)

    @QtCore.Slot(QtGui.QAction)
    def _on_tool_action_triggered(self, action):
        if action == self.tool_selection:
            self._view.setMouseMode(schematics.mouse_modes.SelectItemsMode)
        elif action == self.tool_logic:
            self._view.setMouseMode(schematics.mouse_modes.InsertItemMode)
        elif action == self.tool_connector:
            self._view.setMouseMode(schematics.mouse_modes.InsertConnectorMode)
        elif action == self.tool_lines:
            self._view.setMouseMode(schematics.mouse_modes.InsertLineMode)
        else:
            assert False, "Unexpected action {0} triggered".format(action)
