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
    def instantiate(cls, element_id, parent, additional_metadata={}):
        pass


class ComponentInstance(metaclass=ABCMeta):
    def __init__(self, parent, metadata, component_type):
        assert "id" in metadata

        self.parent = parent
        self.children = []
        self.metadata = metadata
        self.component_type = component_type

        self.parent.child_added(self)

    def child_added(self, child):
        self.children.append(child)

    def id(self):
        return self.get_metadata_field("id")

    def propagate_change(self, data):
        """
        Function for propagating events up into the simulation frontend.
        Propagation follows child-parent-relationships so parent elements
        can employ filtering.

        :param data: metadata update message.
        :return:
        """
        self.parent.propagate_change(data)

    def get_library(self):
        return self.parent.get_library()

    def get_metadata_field(self, field, default=None):
        return self.metadata.get(field,
                                 self.component_type.get_metadata_field(
                                     field, default))

    def set_metadata_field(self, field, value, propagate=True):
        previous_value = self.get_metadata_field(field)
        self.metadata[field] = value

        if propagate and value != previous_value:
            self.propagate_change({'id': self.id(), field: value})

    def set_metadata_fields(self, data, propagate=True):
        changed = {}
        for field, value in data.iteritems():
            previous_value = self.get_metadata_field(field)
            self.metadata[field] = value

            if previous_value != value:
                changed[field] = value

        if propagate and changed:
            changed['id'] = self.id()
            self.propagate_change(changed)

    def destruct(self):
        for child in self.children:
            child.destruct()

        self.propagate_change({'id': self.id(), 'GUID': None})  # FIXME: Yuk


class ComponentLibrary(object):
    def __init__(self):
        self.component_types = {}
        self.id_counter = 0
        self.elements = {}

    def register(self, component_type):
        guid = component_type.GUID()
        assert guid not in self.component_types,\
            "Tried to register {0} {1} a second time".format(component_type,
                                                             guid)

        self.component_types[guid] = component_type

    def instantiate(self, guid, parent, additional_metadata={}):
        assert guid in self.component_types

        instance = self.component_types[guid].instantiate(self.id_counter,
                                                          parent,
                                                          additional_metadata)

        self.elements[self.id_counter] = instance
        self.id_counter += 1

        return instance

    def destruct(self, id):
        element = self.elements.get(id)
        if not element:
            return False

        element.destruct()

global_component_library = ComponentLibrary()


def get_library():
    return global_component_library
