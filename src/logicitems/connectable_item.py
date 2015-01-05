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
            self._delay == other.delay

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


class ConnectableItem(InsertableItem):
    def __init__(self, parent, metadata):
        # list of input connections
        # index: port, value: InputConnectionInfo or None
        self._input_connections = []

        # list of output connections
        # index: port, value: OutputConnectionInfo or None
        self._output_connections = []

        # connections during inactivity, not reported to the backend
        # key: port, value: OutputConnectionInfo or Disconnect or None
        self._inactive_connection_cache = {}

        super().__init__(parent, metadata)

    def apply_update(self, metadata):
        super().apply_update(metadata)

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

    def connect(self, item):
        """Setup connection with given item."""
        raise NotImplementedError

    def disconnect(self, item):
        """unset connection with given item."""
        raise NotImplementedError

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

    def _notify_backend_connect(self, source_port, sink_id,
                                sink_port, delay=0):
        if self.is_inactive():
            # store locally
#            assert not isinstance(
#                self._inactive_connection_cache.get(source_port, None),
#                OutputConnectionInfo), "double connection"
            self._inactive_connection_cache[source_port] = \
                OutputConnectionInfo(sink_id, sink_port, delay)
            print("connected locally", self._inactive_connection_cache)
            self.scene().register_change_during_inactivity(self)
        else:
            self.scene().interface().connect(
                self.id(), source_port, sink_id, sink_port, delay)

    def _notify_backend_disconnect(self, source_port):
        if self.is_inactive():
            # store locally
#            assert not isinstance(
#                self._inactive_connection_cache.get(source_port, None),
#                Disconnect), "double disconnect"
            self._inactive_connection_cache[source_port] = Disconnect()
            print("disconnected locally", self._inactive_connection_cache)
            self.scene().register_change_during_inactivity(self)
        else:
            self.scene().interface().disconnect(self.id(), source_port)

    def _on_has_become_active(self):
        for source_port, info in self._inactive_connection_cache.items():
            if len(self._output_connections) > source_port:
                curr_con = self._output_connections[source_port]
            else:
                curr_con = None
            # connect / re-connect
            if isinstance(info, OutputConnectionInfo):
                if curr_con != info:
                    if curr_con is not None:
                        self._notify_backend_disconnect(source_port)
                    self._notify_backend_connect(
                        source_port, info.sink_id, info.sink_port, info.delay)
            # disconnect
            if isinstance(info, Disconnect) and curr_con is not None:
                self._notify_backend_disconnect(source_port)
        self._inactive_connection_cache = {}

    def itemChange(self, change, value):
        if self.scene() is not None:
            # after becoming active
            if change == ItemBase.ItemSceneActivatedHasChanged:
                self._on_has_become_active()

        return super().itemChange(change, value)
