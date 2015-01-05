#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Connectable items are items that can be connected to.
'''

from PySide import QtGui

from .itembase import ItemBase
from .insertable_item import InsertableItem


class OutputConnectionInfo:
    """Stores all information of an output connection in the backend."""
    def __init__(self, sink_id, sink_port, delay):
        assert sink_id is not None
        self.sink_id = sink_id
        self.sink_port = sink_port
        self.delay = delay

    def __eq__(self, other):
        return isinstance(other, OutputConnectionInfo) and \
            self.sink_id == other.sink_id and \
            self.sink_port == other.sink_port and \
            self.delay == other.delay

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<Output {}, {}, {}>".format(self.sink_id, self.sink_port,
                                            self.delay)


class InputConnectionInfo:
    """Stores all information of an input connection in the backend."""
    def __init__(self, source_id, source_port):
        assert source_id is not None
        self.source_id = source_id
        self.source_port = source_port

    def __repr__(self):
        return "<Input {}, {}>".format(self.source_id, self.source_port)


class Disconnect:
    """Indicates an outstanding disconnect"""
    def __repr__(self):
        return "<Disconnect>"


class ConnectableItem(InsertableItem):
    def __init__(self, parent, metadata):
        # list of input connections
        # index: port, value: InputConnectionInfo or None
        self._input_connections = []

        # list of output connections
        # index: port, value: OutputConnectionInfo or None
        self._output_connections = []

        # input connections during inactivity
        # key: port, value: InputConnectionInfo or Disconnect or None
        self._input_cache = {}

        # output connections during inactivity, not reported to the backend
        # they are submitted to the backend once the scene becomes active
        # key: port, value: OutputConnectionInfo or Disconnect or None
        self._output_cache = {}

        super().__init__(parent, metadata)

        self.setFlag(QtGui.QGraphicsItem.ItemSendsScenePositionChanges)

    def update_connections(self):
        """
        Instruct item to update all of its connections.

        This function is called automatically when the position
        of the item is changing or it is registered.

        The item should
        - disconnect obsolete outputs with either
          'notify_backend_disconnect' or 'disconnect_all_outputs' and
        - discover new inputs and outputs at the current position.
        """
        raise NotImplementedError

    def connect(self, item):
        """Setup connection with given item."""
        raise NotImplementedError

    def apply_update_frontend(self, metadata):
        # TODO: refactor
        super().apply_update_frontend(metadata)

        # TODO: handle #inputs change -> delete connection of invalid index

        inputs = metadata.get('inputs', None)
        if inputs is not None:
            self._input_connections = []
            for source_id, source_port in inputs:
                if source_id is None:
                    info = None
                else:
                    info = InputConnectionInfo(source_id, source_port)
                self._input_connections.append(info)

        outputs = metadata.get('outputs', None)
        if outputs is not None:
            self._output_connections = []
            for sink_id, sink_port, delay in outputs:
                if sink_id is None:
                    info = None
                else:
                    info = OutputConnectionInfo(sink_id, sink_port, delay)
                self._output_connections.append(info)

    def update_metadata_output_connection(self, source_port, sink_id,
                                          sink_port, delay):
        """
        Update output connection information.

        Call this whenever the item gets a metadata update with connection
        information.
        """
        self._output_connections[source_port] = OutputConnectionInfo(
            sink_id, sink_port, delay)

    def disconnect_all_outputs(self):
        """Disconnect all outputs."""
        for port in range(len(self._output_connections)):
            if self._output_connections[port] or \
                    self._output_cache.get(port, None):
                self.notify_backend_disconnect(port)

    def is_connected(self, check_input, port):
        """Returns True if given connection is present."""
        if check_input:
            return len(self._input_connections) > port and \
                self._input_connections[port] is not None
        else:
            return len(self._output_connections) > port and \
                self._output_connections[port] is not None

    def output_delay(self, port):
        """Return delay of given output or None if it is not connected."""
        if len(self._output_connections) > port:
            info = self._output_connections[port]
            if info is not None:
                return info.delay

    def _notify_input_connect(self, sink_port, source_id, source_port):
        """Notify item that input connection has been made."""
        self._input_cache[sink_port] = InputConnectionInfo(source_id,
                                                           source_port)

    def notify_backend_connect(self, source_port, sink_id,
                               sink_port, delay=0):
        if self.is_inactive():
            # store locally
            self._output_cache[source_port] = \
                OutputConnectionInfo(sink_id, sink_port, delay)
            print("connected locally", self._output_cache)
            self.scene().register_change_during_inactivity(self)
            # notify connected item to update input cache
            other = self.scene().registry().get_frontend_item(sink_id)
            other._notify_input_connect(sink_port, self.id(), source_port)
        else:
            self.scene().interface().connect(
                self.id(), source_port, sink_id, sink_port, delay)

    def _notify_input_disconnect(self, sink_port):
        """Notify item that input connection has been disconnected."""
        self._input_cache[sink_port] = Disconnect()

    def notify_backend_disconnect(self, source_port):
        if self.is_inactive():
            # notify connected item to update input cache
            if source_port in self._output_cache:
                info = self._output_cache.get(source_port)
            else:
                info = self._output_connections[source_port]
            if isinstance(info, InputConnectionInfo):
                other = self.scene().registry().get_frontend_item(
                    info.source_id)
                other._notify_input_disconnect(info.source_id)
            # store locally
            self._output_cache[source_port] = Disconnect()
            print("disconnected locally", self._output_cache)
            self.scene().register_change_during_inactivity(self)
        else:
            self.scene().interface().disconnect(self.id(), source_port)

    def _submit_cached_connections(self):
        for source_port, info in self._output_cache.items():
            if len(self._output_connections) > source_port:
                curr_con = self._output_connections[source_port]
            else:
                curr_con = None
            # connect / re-connect
            if isinstance(info, OutputConnectionInfo):
                if curr_con != info:
                    if curr_con is not None:
                        self.notify_backend_disconnect(source_port)
                    self.notify_backend_connect(
                        source_port, info.sink_id, info.sink_port, info.delay)
            # disconnect
            if isinstance(info, Disconnect) and curr_con is not None:
                self.notify_backend_disconnect(source_port)
        self._input_cache = {}
        self._output_cache = {}

    def _issue_connection_update(self):
        """
        Issue connection update when item is moved or newly registered

        This will call update_connections on itself and all
        connected input items, since ConnectableItems only manager
        their output connections.
        """
        # notify all connected inputs to update their connections
        # since we are only keeping track of outputs
        input_items = set()
        for i, info in enumerate(self._input_connections):
            if i in self._input_cache:
                info = self._input_cache[i]
            if isinstance(info, InputConnectionInfo):
                input_items.add(self.scene().registry().get_frontend_item(
                    info.source_id))
        for item in input_items:
            item.update_connections()

        # update our output connections
        self.update_connections()

    def on_registration_status_changed(self):
        """Overrides on_registration_status_changed"""
        # TODO: refactor
        if not self.is_registered():
            self._input_connections = []
            self._output_connections = []
            self._input_cache = {}
            self._output_cache = {}
        else:
            self._issue_connection_update()
        super().on_registration_status_changed()

    def itemChange(self, change, value):
        if self.scene() is not None:
            if change == ItemBase.ItemSceneActivatedChange:
                self._issue_connection_update()
            # submit cache when becoming active
            if change == ItemBase.ItemSceneActivatedHasChanged and value:
                self._submit_cached_connections()
            # update connections when moved in scene
#            if change == QtGui.QGraphicsItem.ItemScenePositionHasChanged:
#                self._issue_connection_update()

        return super().itemChange(change, value)
