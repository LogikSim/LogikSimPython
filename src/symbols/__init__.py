#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Auto discovery of symbols, as they might be user defined.
'''

# TODO: fix dynamic importing
# dynamic importing of symbols is currently not working with installer,
# that's why we do it manually until we need the flexibility
# import symbols.rect


def load_all_symbols():
    pass
    # dirname = os.path.dirname(__file__)
    # if file.endswith('.py') and not file.startswith('__init__') and
    #        os.path.isfile(os.path.join(dirname, file))}
    # for module in modules:
    #    __import__(__name__ + "."+module, globals(), locals())

# until it works we load them manually

from symbols.text_item import TextItem

__all__ = ('TextItem',)
