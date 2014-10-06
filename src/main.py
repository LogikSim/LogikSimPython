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

import main_window
import symbols

def main():
    symbols.load_all_symbols()
    
    app = QtGui.QApplication(sys.argv)
    mw = main_window.MainWindow()
    mw.show()
    app.exec_()

if __name__ == '__main__':
    main()
