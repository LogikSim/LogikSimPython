#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2011

@author: Christian
'''

import os

def load_all_symbols():
    dirname = os.path.dirname(__file__)
    modules = {os.path.splitext(file)[0] for file in os.listdir(dirname) 
            if file.endswith('.py') and not file.startswith('__init__') and 
            os.path.isfile(os.path.join(dirname, file))}
    for module in modules:
        __import__(module, globals(), locals())
