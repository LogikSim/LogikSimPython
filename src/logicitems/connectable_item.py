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

from .insertable_item import InsertableItem


class OutputConnectionInfo:
    """Stores all information of an output connection in the backend."""
    def __init__(self, sink_id, sink_port, delay):
        assert sink_id is not None
        self.sink_id = sink_id
        self.sink_port = sink_port
        self.delay = delay

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


class ConnectableItem(InsertableItem):
    def __init__(self, parent, metadata):
        # list of input connections
        # index: port, value: InputConnectionInfo or None
        self._input_connections = []

        # list of output connections
        # index: port, value: OutputConnectionInfo or None
        self._output_connections = []

        super().__init__(parent, metadata)

    def connect(self, item):
        """Setup connection with given item."""
        raise NotImplementedError

    def apply_update_frontend(self, metadata):
        super().apply_update_frontend(metadata)

        # TODO: handle #inputs, #output change
        #   -> delete connection of invalid index

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

    def connected_input_items(self):
        """Return set of all connected input items."""
        items = set()
        for info in self._input_connections:
            if info is not None:
                items.add(self.scene().registry().frontend_item(
                    info.source_id))
        return items

    def items_at_inputs(self):
        """Return set of all items in the scene located at the inputs."""
        raise NotImplementedError

    def disconnect_all_outputs(self):
        """Disconnect all outputs of this item."""
        for port, info in enumerate(self._output_connections):
            if info is not None:
                self.notify_backend_disconnect(port)

    def connect_all_outputs(self):
        """Connect all output ports."""
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

    def notify_backend_connect(self, source_port, sink_id,
                                sink_port, delay=0):
            self.scene().interface().connect(
                self.id(), source_port, sink_id, sink_port, delay)

    def notify_backend_disconnect(self, source_port):
            self.scene().interface().disconnect(self.id(), source_port)



    def itemChange(self, change, value):
        # delete stored connections on scene change
        if change == QtGui.QGraphicsItem.ItemSceneHasChanged:
            self._input_connections = []
            self._output_connections = []

        if self.scene() is not None:
            # when registered tell scene that connections might have changed
            if change == InsertableItem.ItemRegistrationHasChanged and value:
                self.scene().register_change_during_inactivity(self)

        return super().itemChange(change, value)
