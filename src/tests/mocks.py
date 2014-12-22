#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

'''
Contains mocks helpful for creating unit tests.
'''

from PySide import QtCore


class SettingsMock:
    """
    Mocks QSettings for
    """

    def __init__(self, values={}):
        self.values = values
        self.status_value = QtCore.QSettings.NoError

    def status(self):
        return self.status_value

    def value(self, name, default):
        return self.values.get(name, default)

    def setValue(self, name, value):
        self.values[name] = value

    def sync(self):
        pass


class ModelIndexMock:
    """
    Mocks a QtCore.QModelIndex in very basic ways.
    """

    def __init__(self, row, column, valid=True):
        self._row = row
        self._column = column
        self._valid = valid

    def row(self):
        return self._row

    def column(self):
        return self._column

    def isValid(self):
        return self._valid


class ElementParentMock:
    def __init__(self):
        self.history = []

    def propagate_change(self, data):
        self.history.append(data)
