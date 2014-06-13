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

from cx_Freeze import setup, Executable

exe = Executable(
        script = "main.py",
        #base = "Win32GUI",
)

setup(
        name = "QCanvasTest",
        version = "0.0.1",
        description = "Test QCanvas Capabilities",
        #options = {"build_exe": {"compressed": True}}, 
        executables = [exe]
)
