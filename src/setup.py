#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on May 23, 2011

@author: Christian
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
        executables = [exe]
)