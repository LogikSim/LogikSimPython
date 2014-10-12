#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Entry script to start the LogikSim GUI.
'''

import sys

from PySide import QtGui, QtCore
from settings import setup_settings

import main_window
import symbols

def main():
    symbols.load_all_symbols()

    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setOrganizationName("LogikSim")
    QtCore.QCoreApplication.setOrganizationDomain("logiksim.org")
    QtCore.QCoreApplication.setApplicationName("LogikSim")

    # Load settings
    settings = setup_settings()

    # Run application
    mw = main_window.MainWindow()
    mw.show()
    return_code = app.exec_()

    # Save configuration
    settings.save()

    return return_code


if __name__ == '__main__':
    return_code = main()
    sys.exit(return_code)
