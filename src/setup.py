#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Script to build LogikSim binaries with cx_Freeze for Windows.
'''

import sys
from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable(
        script = "main.py",
        targetName = "LogikSim.exe",
        icon = "resources/LogikSim.ico",
        base = base,
)

setup(
        name = "QCanvasTest",
        version = "0.0.1",
        description = "Test QCanvas Capabilities",
        options = {"build_exe": {"compressed": True,
                                 "includes" : ["PySide.QtXml"],
                                 "include_files" : ["../LICENSE.txt",
                                                    "../AUTHORS.txt"]}}, 
        executables = [exe]
)
