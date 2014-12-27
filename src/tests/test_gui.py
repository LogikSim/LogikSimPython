#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

import unittest

from PySide import QtCore, QtGui
from PySide.QtTest import QTest

import main_window
from settings import setup_settings
from tests.mocks import SettingsMock
from tests.helpers import delayed_perform_on_modal, try_repeatedly
import logicitems


class MainWindowTest(unittest.TestCase):
    def setUp(self):
        self.app = QtGui.QApplication.instance()
        if not self.app:
            self.app = QtGui.QApplication([])

        settings_mock = SettingsMock()
        setup_settings(settings_mock)

        self.mw = main_window.MainWindow()
        self.mw.show()

        QTest.qWaitForWindowShown(self.mw)

    def test_hiding_history_widget_from_menu(self):
        """
        Tests hiding and showing the history widget from the view menu.
        """
        self.assertTrue(self.mw.history_dock_widget.isVisible())

        # Open view menu
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_bar.actionGeometry(
                self.mw.menu_view.menuAction()).center())
        self.assertTrue(self.mw.menu_view.isVisible())

        # Toggle visibility action to hide it
        QTest.mouseClick(
            self.mw.menu_view,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_view.actionGeometry(
                self.mw.toggle_history_dock_widget_view_qaction).center())

        self.assertFalse(self.mw.history_dock_widget.isVisible())

        # Open view menu again
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_bar.actionGeometry(
                self.mw.menu_view.menuAction()).center())
        self.assertTrue(self.mw.menu_view.isVisible())

        # Toggle visibility action to show it again
        QTest.mouseClick(
            self.mw.menu_view,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_view.actionGeometry(
                self.mw.toggle_history_dock_widget_view_qaction).center())

        self.assertTrue(self.mw.history_dock_widget.isVisible())

    def test_exit(self):
        """
        Tests exiting the application via File->Exit
        """

        # Open file menu
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_bar.actionGeometry(
                self.mw.menu_file.menuAction()).center())
        self.assertTrue(self.mw.menu_file.isVisible())

        # Click exit
        QTest.mouseClick(
            self.mw.menu_file,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_view.actionGeometry(self.mw.action_exit).center())

        self.app.processEvents()
        self.assertFalse(self.mw.isVisible())

    def test_place_item(self):
        """
        Tests the workflow of placing an item
        """
        # Make sure the dockwidget is out of the way
        self.mw.history_dock_widget.hide()

        # Select insertion mode
        QTest.keyClick(self.mw, QtCore.Qt.Key_F2)

        self.app.processEvents()

        # Place item
        QTest.mouseClick(
            self.mw._view.viewport(),
            QtCore.Qt.LeftButton,
            pos=self.mw._view.geometry().center()
        )
        self.app.processEvents()

        logic_item_count = 0
        for item in self.mw._view.scene().items():
            if isinstance(item, logicitems.LogicItem):
                logic_item_count += 1

        self.assertEqual(1, logic_item_count)

    def test_about_box(self):
        """
        Tests whether the about dialog opens correctly via the menu
        """
        # Make sure the dock widget is out of the way
        self.mw.history_dock_widget.hide()

        # Open file menu
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_bar.actionGeometry(
                self.mw.menu_help.menuAction()).center())

        self.assertTrue(self.mw.menu_help.isVisible())

        # As the modal about dialog will block in it's event queue,
        # queue the check itself.
        called = False

        def check_open_and_dismiss(window):
            nonlocal called
            self.assertIsInstance(window, QtGui.QMessageBox)
            QTest.keyClick(window, QtCore.Qt.Key_Escape)
            QtGui.QApplication.instance().processEvents()
            called = True

        delayed_perform_on_modal(check_open_and_dismiss)

        # Click about
        QTest.mouseClick(
            self.mw.menu_help,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_help.actionGeometry(
                self.mw.action_about).center())

        #
        # Modal event queue running here until dialog is dismissed
        #

        self.assertTrue(called)

        def is_main_window_active_yet():
            self.app.processEvents()
            return self.app.activeWindow() == self.mw

        try_repeatedly(is_main_window_active_yet)
        self.assertEqual(self.app.activeWindow(), self.mw)

    def test_lulu_about_qt_box(self):
        """
        Tests whether the about Qt dialog opens correctly via the menu
        """
        # Make sure the dock widget is out of the way
        self.mw.history_dock_widget.hide()

        # Open file menu
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_bar.actionGeometry(
                self.mw.menu_help.menuAction()).center())

        self.assertTrue(self.mw.menu_help.isVisible())

        # As the modal about dialog will block in it's event queue,
        # queue the check itself.
        called = False

        def check_open_and_dismiss(window):
            nonlocal called
            self.assertIsInstance(window, QtGui.QMessageBox)
            QTest.keyClick(window, QtCore.Qt.Key_Escape)
            QtGui.QApplication.instance().processEvents()
            called = True

        delayed_perform_on_modal(check_open_and_dismiss)

        # Click about
        QTest.mouseClick(
            self.mw.menu_help,
            QtCore.Qt.LeftButton,
            pos=self.mw.menu_help.actionGeometry(
                self.mw.action_about_qt).center())

        #
        # Modal event queue running here until dialog is dismissed
        #

        self.assertTrue(called)

        def is_main_window_active_yet():
            self.app.processEvents()
            return self.app.activeWindow() == self.mw

        try_repeatedly(is_main_window_active_yet)
        self.assertEqual(self.app.activeWindow(), self.mw)

    def tearDown(self):
        self.mw.close()
        self.mw.deleteLater()
        self.mw._view.scene()._core.quit()  # FIXME: Stupid workaround
        self.mw._view.scene()._registry._registry_handler.quit(True)
        self.mw = None
        self.app.processEvents()
