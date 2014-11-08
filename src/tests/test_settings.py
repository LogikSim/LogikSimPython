#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.

import unittest
from mocks import SettingsMock
from PySide import QtCore, QtGui
from collections import defaultdict
import settings


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.app = QtCore.QCoreApplication.instance()
        if not self.app:
            #FIXME: Want to use self.app = QtCore.QCoreApplication([]) but can't because tearDown can't really clean up the singleton
            self.app = QtGui.QApplication([])

        self.settings_mock = SettingsMock()
        settings.setup_settings(self.settings_mock)

    def test_default_configuration(self):
        """
        Checks the default configuration and presence of all properties.
        """
        s = settings.settings()

        self.assertEqual(s.main_window_geometry, QtCore.QByteArray())
        self.assertEqual(s.main_window_state, QtCore.QByteArray())

    def test_setters_and_signals(self):
        """
        Checks the singleton properties of settings as well as setters, signals and save behavior.
        """
        s = settings.settings()
        s2 = settings.settings()

        changed = defaultdict(lambda: False)
        def track_changed(onwhat, name):
            def slot():
                changed[name] = True
            getattr(onwhat, name + "_changed").connect(slot)

        track_changed(s, "main_window_geometry")
        track_changed(s, "main_window_state")

        s.main_window_geometry = QtCore.QByteArray("hi")
        self.assertTrue(changed["main_window_geometry"])
        self.assertEqual(s2.main_window_geometry, QtCore.QByteArray("hi"))

        s.main_window_state = QtCore.QByteArray("there")
        self.assertTrue(changed["main_window_state"])
        self.assertEqual(s2.main_window_state, QtCore.QByteArray("there"))

        s.save()
        self.assertEqual(self.settings_mock.values["main_window_geometry"], QtCore.QByteArray("hi"))
        self.assertEqual(self.settings_mock.values["main_window_state"], QtCore.QByteArray("there"))

    def test_existing_settings(self):
        """
        Tests whether existing settings are picked up but the Settings class.
        """
        my_settings_mock = SettingsMock({"main_window_geometry" : QtCore.QByteArray("foo")})
        settings.setup_settings(my_settings_mock)

        self.assertEqual(settings.settings().main_window_geometry, QtCore.QByteArray("foo"))
        self.assertEqual(settings.settings().main_window_state, QtCore.QByteArray())

        settings.settings().save()

        self.assertEqual(my_settings_mock.values["main_window_geometry"], QtCore.QByteArray("foo"))
        self.assertEqual(my_settings_mock.values["main_window_state"], QtCore.QByteArray())

    def test_error_handling(self):
        s = SettingsMock()
        s.status_value = QtCore.QSettings.FormatError
        self.assertRaises(Exception, settings.setup_settings, s)

        s = SettingsMock()
        settings.setup_settings(s)
        s.status_value = QtCore.QSettings.AccessError
        self.assertRaises(Exception, settings.settings().save)
