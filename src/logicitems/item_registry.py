#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
from PySide import QtCore
from backend.interface import Handler
from logicitems.itembase import ItemBase


class ItemRegistryHandler(QtCore.QThread, Handler):
    """
    Handler for converting backend updates into Qt signals.
    Uses a separate
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
        self.wait()

    def handle(self, update):
        self.update.emit(update)

    update = QtCore.Signal(dict)


class ItemRegistry(QtCore.QObject):
    def __init__(self, controller, parent=None):
        super().__init__(parent)

        self.item_types = {}
        self.items = {}  # Remembers backend id -> item associations

        self._registry_handler = ItemRegistryHandler(self)
        self._registry_handler.update.connect(self.handle_backend_update)
        controller.connect_handler(self._registry_handler)

        self.destroyed.connect(lambda: self._registry_handler.quit(True))

    def register_type(self, item_type):
        assert issubclass(item_type, ItemBase), \
            "Item type must be derived from ItemBase"

        guid = item_type.GUID()
        assert guid not in self.item_types, \
            "Tried to register {0} {1} a second time".format(item_type,
                                                             guid)

        self.item_types[guid] = item_type

    def start_handling(self):
        self._registry_handler.start()

    def instantiate_for(self, metadata={}):
        """
        Instantiates
        :param metadata:
        :return:
        """
        guid = metadata.get("GUI-GUID") or metadata.get("GUID")
        item_type = self.item_types.get(guid)
        assert item_type, "Have no item type that matches {0}".format(metadata)

        parent = self.items.get(metadata.get("parent"))

        instance = item_type(parent, metadata)
        self.items[metadata['id']] = instance

        self.instantiated.emit(metadata['id'], instance)

        return instance

    @QtCore.Slot(dict)
    def handle_backend_update(self, update):
        uid = update.get('id')
        if uid is not None:
            # Item related message
            item = self.items.get(uid)
            if not item:
                self.instantiate_for(update)
            elif not update.get('GUID', True):
                # GUID is None, item was deleted
                self.deleted.emit(update['id'])
            else:
                # Simple update
                item.update(update)
                self.updated.emit(item, update)
        else:
            # Must be connection related then
            source = self.items[update['source_id']]
            source_port = self.update['source_port']
            sink = self.items.get(update['sink_id'])
            sink_port = self.update['sink_port']

            if self.sink:
                self.connected.emit(source, source_port, sink, sink_port)
            else:
                self.disconnected.emit(source, source_port)

    # Emitted on item creation triggered from the backend (backend id, item)
    instantiated = QtCore.Signal(int, ItemBase)
    # Emitted on item update triggered from the backend (item, update)
    updated = QtCore.Signal(ItemBase, dict)
    # Emitted on item deletion triggered from the backend (backend item id)
    deleted = QtCore.Signal(int)
    # Emitted when item output is connected (source, output, sink, input)
    connected = QtCore.Signal(ItemBase, int, ItemBase, int)
    # Emitted when item output is disconnected (source, output)
    disconnected = QtCore.Signal(ItemBase, int)
