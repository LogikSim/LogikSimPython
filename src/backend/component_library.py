#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
"""
This module contains the classes necessary to implement and manage a
metadata driven component architecture. Types are identified by a GUID that
can be used to register them in the ComponentLibrary. A type is described in
form of a ComponentType which contains non-modifiable metadata shared by all
instances of the type as well as well as the capability to instantiate a
concrete instance of the type. The base-class ComponentInstance for these
instances has its own set of instance specific metadata as well as machinery
to modify it and notify others of such modifications.

Example use:
>>> class MyComponentType(ComponentType):
...     METADATA={'GUID': '628AAFE2-82B3-4465-83A6-87D0FC46071F',
...               'key':'value'}
...     @classmethod
...     def instantiate(cls, component_id, parent, additional_metadata):
...         additional_metadata['id'] = component_id
...         return MyComponent(parent, additional_metadata, cls)
...
>>> class MyComponent(ComponentInstance):
...     def __init__(self, parent, metadata, component_type):
...         super().__init__(parent, metadata, component_type)
...
>>> class MyComponentRoot(ComponentRoot):
...     def propagate_change(self, data): pass
...     def get_library(self): pass
...     def child_added(self, child): pass
...
>>> cl = ComponentLibrary()  # Instantiate the library
>>> root = MyComponentRoot()  # Instantiate our component root
>>> cl.register(MyComponentType)  # Register out component type with the lib
>>> inst = cl.instantiate('628AAFE2-82B3-4465-83A6-87D0FC46071F', 5, root)
>>> assert inst.get_metadata_field('key') == 'value'  # Check we have metadata
"""

from abc import ABCMeta, abstractmethod
from copy import copy


class ComponentType(object):
    """
    Base-class for the description of a component type.
    Contains the basic metadata and functionality to instantiate
    a component.
    """
    METADATA = None  # Must override this in component types

    @classmethod
    def GUID(cls):
        """
        :return: GUID for this type
        """
        return cls.get_metadata_field("GUID")

    @classmethod
    def get_metadata_field(cls, field, default=None):
        """
        Returns the value of one field in the meta-data
        :param field: Fieldname to query
        :param default: Default value to return if field does not exist.
        :return: Contents of field or default
        """
        return cls.METADATA.get(field, default)

    @classmethod
    def get_metadata(cls):
        """
        :return: Metadata of the component. Make sure to copy before modifying
        """
        return cls.METADATA

    @classmethod
    def instantiate(cls, component_id, parent, additional_metadata):
        """
        This method must instantiate a component of the type represented
        by this class.

        :param component_id: Simulation unique ID for the new instance
        :param parent: Parent component (must be given)
        :param additional_metadata: Optional additional metadata to use
        :return: Instance of the component
        """
        pass


class ComponentRoot(metaclass=ABCMeta):
    """
    Interface required on the virtual root component all top-level
    components are parented to. This configuration was chosen to
    enable uniform event propagation without special casing in root
    components or storing additional redundant references in the components.
    """
    @abstractmethod
    def propagate_change(self, data):
        """
        Function for propagating changes up into the simulation frontend.
        Propagation follows child-parent-relationships so parent components
        can employ filtering.

        :param data: metadata update message.
        """
        pass

    @abstractmethod
    def get_library(self):
        """
        :return: Library instance this simulation is working with.
        """
        pass

    @abstractmethod
    def child_added(self, child):
        """
        Top level components of the simulation will register themselves
        with the component root using this function

        :param child: Simulation top-level component
        """
        pass


class ComponentInstance(metaclass=ABCMeta):
    """
    Base-class for component instances. This class implements all the basic
    functionality required by the meta-data machinery in the simulation.
    This includes querying, modifying and propagating metadata as well as
    handling parent child relationships and hierarchical destruction.
    """
    def __init__(self, parent, metadata, component_type):
        """
        Creates a new instances of this type and registers it with the
        given parent.

        :param parent: Parent component (must be given)
        :param metadata: Metadata to instantiate with. Must have 'id' field.
        :param component_type: Type description with type metadata
        """
        assert "id" in metadata

        self._parent = parent
        self._children = []
        self._metadata = metadata
        self._component_type = component_type  # Used for type metadata query

        self._parent.child_added(self)

    def child_added(self, child):
        """
        Registers a new child with this component.

        Note: Does not set this component as a parent in the child.

        :param child: Child to add.
        """
        self._children.append(child)

    def id(self):
        """
        :return: Simulation unique id of the instance
        """
        return self.get_metadata_field("id")

    def propagate_change(self, data):
        """
        Function for propagating events up into the simulation frontend.
        Propagation follows child-parent-relationships so parent components
        can employ filtering.

        :param data: metadata update message.
        """
        self._parent.propagate_change(data)

    def get_library(self):
        """
        Returns the library used in the simulation.
        """
        return self._parent.get_library()

    def get_metadata_field(self, field, default=None):
        """
        Returns the value of a given metadata field. Values set on the
        instance override values available from the ComponentType. Only if
        a field isn't available in the ComponentType is the default value
        returned.

        :param field: Field to query
        :param default: Default to return if field doesn't exist
        :return: Value of field or default
        """
        return self._metadata.get(field,
                                  self._component_type.get_metadata_field(
                                      field, default))

    def get_metadata(self):
        """
        :return: Returns all metadata available for the instance. This
        includes all fields available in the type description.
        """
        metadata_combined = copy(self._component_type.get_metadata())
        metadata_combined.update(self._metadata)
        return metadata_combined

    def updated(self):
        """
        Trigger full metadata propagation for this component.
        """
        self.propagate_change(self.get_metadata())

    def set_metadata_field(self, field, value, propagate=True):
        """
        Sets a single metadata field on the instance and propagates
        any changes using propagate_change.

        :param field: Field to set
        :param value: Value to set field to
        :param propagate: If false disables propagation for this change
        """
        previous_value = self.get_metadata_field(field)
        self._metadata[field] = value

        if propagate and value != previous_value:
            self.propagate_change({'id': self.id(), field: value})

    def set_metadata_fields(self, data, propagate=True):
        """
        Sets multiple metadata fields. Equivalent to calling
        set_metadata_field for each item in the given data.
        :param data: Dictionary with field:value items to set.
        :param propagate: If false disables propagation for changes
        """
        changed = {}
        for field, value in data.items():
            previous_value = self.get_metadata_field(field)
            self._metadata[field] = value

            if previous_value != value:
                changed[field] = value

        if propagate and changed:
            changed['id'] = self.id()
            self.propagate_change(changed)

    def destruct(self):
        """
        Recursively destructs this component and all of its children with
        regards to simulation integration. Also propagates this change.

        :return: List of IDs of components destructed by this call in order
        of destruction.
        """
        destroyed_components = []
        for child in self._children:
            destroyed_components.extend(child.destruct())
        self._children = []

        destroyed_components.append(self.id())

        self.propagate_change({'id': self.id(), 'GUID': None})  # FIXME: Yuk

        return destroyed_components


class ComponentLibrary(object):
    """
    Class to enable instantiation of ComponentInstances using only the GUID
    of a ComponentType after registering it with a library.
    """
    def __init__(self):
        """
        Creates a new component library instance with no types registered.
        """
        self.component_types = {}
        self.components = {}

    def register(self, component_type):
        """
        Register a ComponentType with this library enabling it to be
        instantiated by this class.

        :param component_type: Component type to register
        """
        guid = component_type.GUID()
        assert guid not in self.component_types,\
            "Tried to register {0} {1} a second time".format(component_type,
                                                             guid)

        self.component_types[guid] = component_type

    def instantiate(self, guid, component_id, parent,
                    additional_metadata=None):
        """
        Instantiates a component for the ComponentType with the given guid.

        :param guid: GUID to instantiate
        :param component_id: Simulation unique id for the new component
        :param parent: Parent component or component root for component
        :param additional_metadata: Additional metadata to pass to use during
        construction.
        :return: New component instance
        """
        assert guid in self.component_types
        additional_metadata = additional_metadata or {}

        instance = self.component_types[guid].instantiate(component_id,
                                                          parent,
                                                          additional_metadata)

        self.components[component_id] = instance

        return instance

    def enumerate_types(self):
        """
        :return: Returns a list of type metadata with one entry for each type
                 registered to this library.
        """
        return [t.get_metadata() for t in self.component_types.values()]

    def destruct(self, component_id):
        """
        Triggers the simulation related destruction of the component instance
        with the given id.

        :param component_id: ID of the component to destruct
        :return: False if component instance didn't exist.
        """

        component = self.components.get(component_id)
        if not component:
            return False

        component.destruct()
        return True

global_component_library = ComponentLibrary()


def get_library():
    """
    :return: Global ComponentLibrary singleton.
    """
    return global_component_library

if __name__ == "__main__":
    import doctest
    doctest.testmod()
