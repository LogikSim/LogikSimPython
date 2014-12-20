#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.simple_element import SimpleElement
from backend.component_library import ComponentType
from copy import copy


class And(ComponentType):
    """
    Simple AND gate.
    """
    METADATA = {"GUID": "7793F2A0-B313-4489-ABF3-8570ECDFE3EE",
                "name": "And",
                "description": "And logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 1}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return AndInstance(metadata)


class AndInstance(SimpleElement):
    def __init__(self, additional_metadata):
        super().__init__(
            additional_metadata,
            component_type=And,
            logic_function=lambda inputs: [all(inputs)],)


class Or(ComponentType):
    """
    Simple OR gate.
    """
    METADATA = {"GUID": "43DD02B5-968D-488B-BAF5-FC63B7C928E7",
                "name": "Or",
                "description": "Or logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 1}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return OrInstance(metadata)


class OrInstance(SimpleElement):
    def __init__(self, additional_metadata):
        super().__init__(
            additional_metadata,
            component_type=Or,
            logic_function=lambda inputs: [any(inputs)],)


class Xor(ComponentType):
    """
    Simple XOR gate.
    """
    METADATA = {"GUID": "61E01C17-D81E-4F49-B665-01B1C519B8C6",
                "name": "Xor",
                "description": "Xor logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 1}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return XorInstance(metadata)


class XorInstance(SimpleElement):
    def __init__(self, additional_metadata):
        super().__init__(
            additional_metadata,
            component_type=Xor,
            logic_function=lambda inputs: [sum(inputs) == 1],)


class Nand(ComponentType):
    """
    Simple Nand gate.
    """
    METADATA = {"GUID": "B50A8E0D-319C-4DB9-87A3-61F6F3EAC4D8",
                "name": "Nand",
                "description": "Nand logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 1}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return NandInstance(metadata)


class NandInstance(SimpleElement):
    def __init__(self, additional_metadata):
        super().__init__(
            additional_metadata,
            component_type=Nand,
            logic_function=lambda inputs: [not all(inputs)],)


class Nor(ComponentType):
    """
    Simple Nor gate.
    """
    METADATA = {"GUID": "B634DF23-0994-46E0-AF52-A99D35F3231C",
                "name": "Nor",
                "description": "Nor logic gate",
                "#inputs": 2,
                "#outputs": 1,
                "delay": 1}

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = id
        return NorInstance(metadata)


class NorInstance(SimpleElement):
    def __init__(self, additional_metadata):
        super().__init__(
            additional_metadata,
            component_type=Nor,
            logic_function=lambda inputs: [not any(inputs)],)


def register(library):
    library.register_type(And)
    library.register_type(Or)
    library.register_type(Xor)
    library.register_type(Nand)
    library.register_type(Nor)
