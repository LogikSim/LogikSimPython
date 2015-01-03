#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

from copy import copy

from backend.simple_element import SimpleElement
from backend.component_library import ComponentType
from symbols import TextItem


class And(ComponentType):
    """
    Simple AND gate.
    """
    METADATA = {"GUID": "7793F2A0-B313-4489-ABF3-8570ECDFE3EE",
                "GUI-GUID": TextItem.GUI_GUID(),  # Override GUI item
                "name": "And",
                "description": "And logic gate",
                "text": "&",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 2}

    @classmethod
    def instantiate(cls, id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return AndInstance(parent, metadata)


class AndInstance(SimpleElement):
    def __init__(self, parent, additional_metadata):
        super().__init__(parent, additional_metadata, And,
                         lambda inputs: [all(inputs)],)


class Or(ComponentType):
    """
    Simple OR gate.
    """
    METADATA = {"GUID": "43DD02B5-968D-488B-BAF5-FC63B7C928E7",
                "GUI-GUID": TextItem.GUI_GUID(),  # Override GUI item
                "name": "Or",
                "text": "≥1",
                "description": "Or logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 2}

    @classmethod
    def instantiate(cls, id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return OrInstance(parent, metadata)


class OrInstance(SimpleElement):
    def __init__(self, parent, additional_metadata):
        super().__init__(parent, additional_metadata, And,
                         lambda inputs: [any(inputs)],)


class Xor(ComponentType):
    """
    Simple XOR gate.
    """
    METADATA = {"GUID": "61E01C17-D81E-4F49-B665-01B1C519B8C6",
                "GUI-GUID": TextItem.GUI_GUID(),  # Override GUI item
                "name": "Xor",
                "text": "=1",
                "description": "Xor logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 2}

    @classmethod
    def instantiate(cls, id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return XorInstance(parent, metadata)


class XorInstance(SimpleElement):
    def __init__(self, parent, additional_metadata):
        super().__init__(parent, additional_metadata, Xor,
                         lambda inputs: [sum(inputs) == 1],)


class Nand(ComponentType):
    """
    Simple Nand gate.
    """
    METADATA = {"GUID": "B50A8E0D-319C-4DB9-87A3-61F6F3EAC4D8",
                "GUI-GUID": TextItem.GUI_GUID(),  # Override GUI item
                "name": "Nand",
                "description": "Nand logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 2}

    @classmethod
    def instantiate(cls, element_id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = element_id
        return NandInstance(parent, metadata)


class NandInstance(SimpleElement):
    def __init__(self, parent, additional_metadata):
        super().__init__(parent, additional_metadata, Nand,
                         lambda inputs: [not all(inputs)],)


class Nor(ComponentType):
    """
    Simple Nor gate.
    """
    METADATA = {"GUID": "B634DF23-0994-46E0-AF52-A99D35F3231C",
                "GUI-GUID": TextItem.GUI_GUID(),  # Override GUI item
                "name": "Nor",
                "description": "Nor logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 2}

    @classmethod
    def instantiate(cls, id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return NorInstance(parent, metadata)


class NorInstance(SimpleElement):
    def __init__(self, parent, additional_metadata):
        super().__init__(parent, additional_metadata, Nor,
                         lambda inputs: [not any(inputs)],)


def register(library):
    library.register(And)
    library.register(Or)
    library.register(Xor)
    library.register(Nand)
    library.register(Nor)
