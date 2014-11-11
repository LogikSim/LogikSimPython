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
import os
import fnmatch
import subprocess
from distutils.core import Command

from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable(
    script="main.py",
    targetName="LogikSim.exe",
    icon="resources/LogikSim.ico",
    base=base,
)


class GenerateCommand(Command):
    description = "Generates .py files from Qt .ui and .qrc files"
    user_options = [('no-uic', None, 'Disables UIC'),
                    ('no-rcc', None, 'Disables RCC')]

    def initialize_options(self):
        self.no_uic = False
        self.no_rcc = False

    def finalize_options(self):
        self.no_uic = bool(self.no_uic)
        self.no_rcc = bool(self.no_rcc)
        self.dry_run = bool(self.dry_run)  # Global option

    def recursive_search(self, filter, search_directory='.'):
        """
        Recursively searches for files matching the glob filter
        and returns them as a list of directory, filename tuples.
        """
        found = []
        for root, directories, files in os.walk(search_directory):
            for file in fnmatch.filter(files, filter):
                found.append((root, file))

        return found

    def run(self):
        if self.dry_run:
            def check_call_emu(params, cwd=None):
                print("In '{0}' would run: {1}".format(cwd, " ".join(params)))

            call = check_call_emu
        else:
            call = subprocess.check_call

        if not self.no_uic:
            print("Running uic...")
            for (root, source_file) in self.recursive_search("*.ui"):
                target_file = "ui_{0}.py".format(os.path.splitext(source_file)[0])
                print("  " + os.path.join(root, source_file))
                call(["pyside-uic", source_file, "-o", target_file], cwd=root)
            print("Done")

        if not self.no_rcc:
            print("Running rcc...")
            for (root, source_file) in self.recursive_search("*.qrc"):
                target_file = "{0}_rc.py".format(os.path.splitext(source_file)[0])
                print("  " + os.path.join(root, source_file))
                call(["pyside-rcc", "-py3", source_file, "-o", target_file], cwd=root)
            print("Done")


setup(
    name="QCanvasTest",
    version="0.0.1",
    description="Test QCanvas Capabilities",
    options={"build_exe": {"compressed": True,
                           "includes": ["PySide.QtXml"],
                           "include_files": ["../LICENSE.txt",
                                             "../AUTHORS.txt"]}},
    cmdclass={"generate": GenerateCommand},
    executables=[exe]
)
