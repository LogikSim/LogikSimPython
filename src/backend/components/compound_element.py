#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from backend.element import Element
from backend.component_library import ComponentType
from copy import copy
import random


class InputOutputBank(ComponentType):
    """
    Zero latency indirection element.
    """
    METADATA = {"GUID": "ab47bdb4-b44d-4c16-9cbb-1a3810ad830f",
                "name": "In/Out Bank",
                "description": "Input out bank used in compound elements"}

    @classmethod
    def instantiate(cls, element_id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = element_id
        return InputOutputBankInstance(parent, metadata)


class InputOutputBankInstance(Element):
    """
    Zero latency indirection element instance.
    """
    def __init__(self, parent, metadata):
        super().__init__(parent, metadata, InputOutputBank)
        self.mapping = {}

    def connect(self, element, output_port=0, input_port=0):
        self.mapping[output_port] = (element, input_port)
        # FIXME: Implement rest of this
        return True

    def disconnect(self, output_port):
        val = self.mapping.pop(output_port, None)
        # FIXME: Implement rest of this
        return val is not None

    def connected(self, element, output_port=0, input_port=0):
        # FIXME: Implement this
        return True

    def disconnected(self, input_port):
        # FIXME: Implement this
        return True

    def edge(self, input_port, state):
        """
        Handles a rising or falling edge and maps it to the corresponding
        element.

        :param input_port: Index of the input
        :param state: Value of the input (True/False) at time `when`
        :return: List of one or more future Event s
        """
        if input_port not in self.mapping:
            # Pin is not connected.
            return

        element, element_input = self.mapping[input_port]
        element.edge(element_input, state)

    def clock(self, when):
        """
        Triggered when all egdes for a point in time have been received.

        :param when: Point in time
        :return: List of none or more future Event s
        """
        result = []
        for element in set([element for element, _ in self.mapping.values()]):
            result.extend(element.clock(when))

        return result


class CompoundElement(ComponentType):
    """
    Element wrapping other elements.
    """
    METADATA = {"GUID": "14328e37-1969-40e4-806f-cfe58e7fb6a0",
                "name": "Compound element",
                "description": "Element consisting of multiple other elements"}

    @classmethod
    def instantiate(cls, element_id, parent, additional_metadata={}):
        metadata = copy(additional_metadata)
        metadata["id"] = element_id
        return CompoundElementInstance(parent, metadata)


class CompoundElementInstance(Element):
    """
    Element wrapping other elements
    """
    def __init__(self, parent, metadata):
        super().__init__(parent, metadata, CompoundElement)

        lib = self.get_library()

        rand = random.Random(self.id())  # FIXME: This isn't a good idea...
        self.input_bank = lib.instantiate(InputOutputBank.GUID(),
                                          rand.getrandbits(128),
                                          self)
        self.output_bank = lib.instantiate(InputOutputBank.GUID(),
                                           rand.getrandbits(128),
                                           self)

    def __str__(self):
        return "CompoundElement(name={0})"\
            .format(self.get_metadata_field("name"))

    def edge(self, input_port, state):
        """
        Handles a rising or falling edge and maps it to the corresponding
        internal element.

        :param input_port: Index of the input
        :param state: Value of the input (True/False) at time `when`
        """
        self.input_bank.edge(input_port, state)

    def clock(self, when):
        """
        Triggered when all egdes for a point in time have been received.
        Clocks all elements connected to inputs.

        :param when: Point in time
        :return: List of none or more future Event s
        """
        return self.input_bank.clock(when)

    def connect(self, element, output_port=0, input_port=0):
        """
        Connects output posts to external element.

        :param element: Element to connect
        :param output_port: Output of post to connect to element
        :param input_port: Input on element to connect to
        :return: True if connected successful
        """
        return self.output_bank.connect(element, output_port, input_port)

    def disconnect(self, output_port):
        return self.output_bank.disconnect(output_port)

    def connected(self, element, output_port=0, input_port=0):
        return self.output_bank.connected(element, output_port, input_port)

    def disconnected(self, input_port):
        return self.output_bank.disconnected(input_port)
