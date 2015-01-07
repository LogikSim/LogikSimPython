#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtCore
from backend.interface import Handler
from backend.component_library import gen_component_id
from logicitems.itembase import ItemBase
from logging import getLogger
from copy import copy


class GuiTypeNotFoundException(Exception):
    def __init__(self, metadata):
        super().__init__("Have no item type that matches {0}".format(metadata))


class ItemRegistry(QtCore.QObject):
    """
    The item registry is the front-end counterpart to the backends component
    library and controller. It handles frontend item type registrations as well
    as handling of backend updates.
    """
    def __init__(self, controller, parent=None):
        """
        Instantiates a clean registry and connects its handler to the
        given controller.

        Note: You must call start_handling() on the registry instance
              to make it start to poll for updates from the backend.

        :param controller: Controller to connect handler to
        :param parent: Parent in Qt hierarchy
        """
        super().__init__(parent)

        self.log = getLogger("registry")

        self._item_types = {}  # GUID -> item type
        self._backend_types = {}  # GUID -> metadata associations

        self._items = {}  # Remembers backend id -> item associations

        self._clock = -1  # Backend clock

        self._registry_handler = ItemRegistryHandler(self)
        self._registry_handler.update.connect(self.handle_backend_update)
        controller.connect_handler(self._registry_handler)

        self.destroyed.connect(lambda: self._registry_handler.quit(True))

        self._handlers = {
            'simulation-properties': self._on_simulation_properties_changed,
            'alive': self._on_alive,
            'change': self._on_change,
            'enumerate_components': self._on_enumerate_components,
            'serialization': self._on_serialization,
            'deserialization-start': self._on_deserialization_start,
            'deserialization-end': self._on_deserialization_complete,
            'error': self._on_error
        }

    def clock(self):
        """Returns current backend clock."""
        return self._clock

    def register_type(self, item_type):
        assert issubclass(item_type, ItemBase), \
            "Item type must be derived from ItemBase"

        guid = item_type.GUI_GUID()
        assert guid not in self._item_types, \
            "Tried to register {0} {1} a second time".format(item_type,
                                                             guid)

        self._item_types[guid] = item_type

    def start_handling(self):
        """
        Once called the registry starts handling updates received from
        the backend. Delay calling this until you have registered all
        frontend types you intend to use and your infrastructure is
        properly connected to all registry signals you want to receive.
        Calling this function before this all is in order may result in
        instantiation errors and/or lost updates.
        """
        self._registry_handler.start()

    def frontend_item(self, backend_id):
        """
        Return frontend item with given backend id.

        :param backend_id: Backend id of the requested item.
        """
        return self._items[backend_id]

    def instantiate_frontend_item(self,
                                  backend_guid,
                                  additional_metadata={}):
        """
        Instantiates a frontend item without backend backing.

        The element will still be registered in this registry but no
        instantiated signal will be emitted for it.

        :param backend_guid: Backend element GUID to instantiate.
        :param additional_metadata: Additional metadata to pass
        :return: Element instance
        """
        metadata = copy(self._backend_types[backend_guid])
        metadata.update(additional_metadata)
        # always generate new id, we don't want to have two
        # objects with the same id
        metadata['id'] = gen_component_id()

        return self._instantiate_for(metadata,
                                     announce=False)

    def instantiated_frontend_item(self, item):
        """
        Registers an already instantiated frontend element with the registry.
        This can be used to re-use previously created frontend items that
        were deleted from the backend but have a re-creation pending.

        :param item: Item to register
        """
        if self._items.get(item.id()) is item:
            return
        assert item.id() not in self._items
        self._items[item.id()] = item

    def _instantiate_for(self, metadata={}, announce=True):
        """
        Instantiates a front-end element from the given meta-data.

        Requires at least a GUID and an id field to be present in the metadata.
        Other requirements depend on the type being instantiated.

        :param metadata: Metadata to instantiate from
        :param announce: If True emits the instantiated signal for the new
                         element.
        :return: Item instance.
        """
        guid = metadata.get("GUI-GUID") or metadata.get("GUID")
        item_type = self._item_types.get(guid)
        if not item_type:
            raise GuiTypeNotFoundException(metadata)

        parent = self._items.get(metadata.get("parent"))

        instance = item_type(parent, metadata)
        self._items[instance.id()] = instance

        if announce:
            self.instantiated.emit(instance)

        return instance

    @QtCore.Slot(dict)
    def handle_backend_update(self, update):
        """
        Dispatches incoming backend updates to corresponding handlers.

        :param update: Free form dictionary with update. Only guaranteed to
                       have basic framing.
        """
        message_type = update['type']
        new_clock = update['clock']
        if new_clock != self._clock:
            assert new_clock > self._clock
            self.tick.emit(new_clock)
            self._clock = new_clock

        handler = self._handlers.get(message_type)
        if not handler:
            self.log.warning("No handler for message_type %s: %s",
                             message_type,
                             update)
        else:
            handler(update)

    def _on_alive(self, message):
        """
        The backend sends alive messages from time to time so we know it's
        still ready to process.
        """
        pass

    def _on_change(self, message):
        """
        Reacts to change updates. These are sent by the backend for backend
        element changes (creation, update, deletion) as well connectivity
        changes.

        :param message: Free form dict.
        """
        update = message['data']
        uid = update.get('id')
        if uid is not None:
            # Item related message
            item = self._items.get(uid)
            if not item:
                self._instantiate_for(update)
            elif not update.get('GUID', True):
                # GUID is None, item was deleted, remove from registry and
                # notify slots
                item = self._items[uid]
                del self._items[uid]
                self.deleted.emit(item)
            else:
                # Simple update
                item.update_frontend(update)
                self.updated.emit(item, update)
        else:
            # Must be connection related then
            source = self._items[update['source_id']]
            source_port = update['source_port']
            sink = self._items.get(update['sink_id'])
            sink_port = update['sink_port']
            delay = update['delay']

            if sink:
                self.connected.emit(source,
                                    source_port,
                                    sink,
                                    sink_port,
                                    delay)
            else:
                self.disconnected.emit(source, source_port)

    def _on_enumerate_components(self, message):
        """
        Emits the enumeration_complete signal for enumeration_complete updates
        from the backend.

        :param message: Free form dict
        """
        self._backend_types = {}
        for backend_type in message['data']:
            guid = backend_type['GUID']
            self._backend_types[guid] = backend_type

        self.enumeration_complete.emit(message['data'])

    def _on_serialization(self, message):
        """
        Emits the serialized signal.
        :param message: Free form dict
        """
        self.serialization_complete.emit(message['in-reply-to'],
                                         message['data'])

    def _on_deserialization_start(self, message):
        """
        Emits the deserialization start signal
        """
        self.deserialization_start.emit(message['in-reply-to'])

    def _on_deserialization_complete(self, message):
        """
        Emits the deserialization end signal
        """
        self.deserialization_complete.emit(message['in-reply-to'],
                                           message['ids'])

    def _on_simulation_properties_changed(self, message):
        """
        Emits the simulation_properties_changed signal.
        """
        self.simulation_properties_changed.emit(message['properties'])

    def _on_error(self, message):
        """
        Emits the error signal.
        """
        self.error.emit(message['message'], message['exception'])

    # Emitted on item creation triggered from the backend (item)
    instantiated = QtCore.Signal(ItemBase)
    # Emitted on item update triggered from the backend (item, update)
    updated = QtCore.Signal(ItemBase, dict)
    # Emitted on item deletion triggered from the backend (item)
    deleted = QtCore.Signal(ItemBase)
    # Emitted when output is connected (source, output, sink, input, delay)
    connected = QtCore.Signal(ItemBase, int, ItemBase, int, object)
    # Emitted when item output is disconnected (source, output)
    disconnected = QtCore.Signal(ItemBase, int)
    # Emitted when backend type enumeration completes (list of metadata sets)
    enumeration_complete = QtCore.Signal(list)
    # Emitted when a serialization request completes (request id, dump)
    serialization_complete = QtCore.Signal(object, object)
    # Emitted when a deserialization request starts (req. id)
    deserialization_start = QtCore.Signal(object)
    # Emitted when a deserialization request completes (req. id, list of ids)
    deserialization_complete = QtCore.Signal(object, list)
    # Emitted when the backend simulation time changed (new clock)
    tick = QtCore.Signal(object)
    # Emitted when a simulation property update is received
    simulation_properties_changed = QtCore.Signal(dict)
    # Emitted if an error occurs in the backend (message, exception)
    error = QtCore.Signal(str, str)


class ItemRegistryHandler(QtCore.QThread, Handler):
    """
    Handler for converting backend updates into Qt signals.
    Implemented as a separate thread that is started as part of
    the ItemRegistry.
    """
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent=parent)
        Handler.__init__(self)

        self._quit = False

    def run(self):
        self._quit = False
        while not self._quit:
            self.poll_blocking(timeout=0.01)

    @QtCore.Slot()
    def quit(self, blocking=False):
        self._quit = True

        if blocking:
            self.wait()

    def handle(self, update):
        self.update.emit(update)

    update = QtCore.Signal(dict)
