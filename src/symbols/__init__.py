#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

import os

def load_all_symbols():
    dirname = os.path.dirname(__file__)
    modules = {os.path.splitext(file)[0] for file in os.listdir(dirname) 
            if file.endswith('.py') and not file.startswith('__init__') and 
            os.path.isfile(os.path.join(dirname, file))}
    for module in modules:
        __import__(module, globals(), locals())
