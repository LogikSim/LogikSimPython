#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from abc import ABCMeta


class ComponentType(object):
    METADATA = None  # Must override this in component types

    @classmethod
    def GUID(cls):
        return cls.get_metadata_field("GUID")

    @classmethod
    def get_metadata_field(cls, field, default=None):
        return cls.METADATA.get(field, default)

    @classmethod
    def instantiate(cls, id, additional_metadata={}):
        pass


class ComponentInstance(metaclass=ABCMeta):
    def __init__(self, metadata, component_type):
        assert "id" in metadata

        self.metadata = metadata
        self.component_type = component_type

    def id(self):
        return self.get_metadata_field("id")

    def get_metadata_field(self, field, default=None):
        return self.metadata.get(field,
                                 self.component_type.get_metadata_field(
                                     field, default))


class ComponentLibrary(object):
    def __init__(self):
        self.component_types = {}
        self.id_counter = 0

    def register_type(self, component_type):
        guid = component_type.GUID()
        assert guid not in self.component_types,\
            "Tried to register {0} {1} a second time".format(component_type,
                                                             guid)

        self.component_types[guid] = component_type

    def instantiate_type(self, guid, additional_metadata={}):
        assert guid in self.component_types

        instance = self.component_types[guid].instantiate(self.id_counter,
                                                          additional_metadata)
        self.id_counter += 1

        return instance


global_component_library = ComponentLibrary()


def get_library():
    return global_component_library
