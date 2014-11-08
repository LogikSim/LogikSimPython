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
        self.assertTrue(self.mw.history_dock_widget.isVisible())

        # Open view menu
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos = self.mw.menu_bar.actionGeometry(self.mw.menu_view.menuAction()).center(),
            delay = 200)
        self.assertTrue(self.mw.menu_view.isVisible())

        # Toggle visibility action to hide it
        QTest.mouseClick(
            self.mw.menu_view,
            QtCore.Qt.LeftButton,
            pos = self.mw.menu_view.actionGeometry(self.mw.toggle_history_dock_widget_view_qaction).center(),
            delay = 200)

        self.assertFalse(self.mw.history_dock_widget.isVisible())

        # Open view menu again
        QTest.mouseClick(
            self.mw.menu_bar,
            QtCore.Qt.LeftButton,
            pos = self.mw.menu_bar.actionGeometry(self.mw.menu_view.menuAction()).center(),
            delay = 200)
        self.assertTrue(self.mw.menu_view.isVisible())

        # Toggle visibility action to show it again
        QTest.mouseClick(
            self.mw.menu_view,
            QtCore.Qt.LeftButton,
            pos = self.mw.menu_view.actionGeometry(self.mw.toggle_history_dock_widget_view_qaction).center(),
            delay = 200)

        self.assertTrue(self.mw.history_dock_widget.isVisible())

    def tearDown(self):
        self.mw.close()
        self.app.exit()

