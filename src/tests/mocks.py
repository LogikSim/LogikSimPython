#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtCore

class SettingsMock:
    """
    Mocks QSettings for
    """
    def __init__(self, values = {}):
        self.values = values

    def status(self):
        return QtCore.QSettings.NoError

    def value(self, name, default):
        return self.values.get(name, default)

    def setValue(self, name, value):
        self.values[name] = value

    def sync(self):
        pass
