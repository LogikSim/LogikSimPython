#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Insertable items are items that are backed by a backend instance.
'''

from PySide import QtGui

from .itembase import ItemBase


class InsertableItem(ItemBase):
    """
    Insertable items have a position and are backed by a backend instance.
    """
    def __init__(self, parent=None, metadata={}):
        super().__init__(parent)

        self.setX(metadata.get('x', 0))
        self.setY(metadata.get('y', 0))

        self._cached_metadata = metadata
        self._registered_scene = None

    def GUID(self):
        """Return GUID of this instance."""
        return self._cached_metadata['GUID']

    @classmethod
    def GUI_GUID(cls):
        """Return GUI_GUID of this class."""
        raise NotImplementedError

    def id(self):
        """Return id, used to communicate with backend."""
        return self._cached_metadata['id']

    def name(self):
        """Return name."""
        return self._cached_metadata.get('name', '<name>')

    def metadata(self):
        """Return the complete metadata."""
        return self._cached_metadata

    def update(self, metadata):
        self._cached_metadata.update(metadata)

        return
        x = metadata.get('x')
        if x is not None:
            self.setX(x)

        y = metadata.get('y')
        if y is not None:
            self.setY(y)

    def set_temporary(self, temp):
        """
        Overrides set_temporary.

        Temporary insertable items have no instance in the backend.
        """
        ItemBase.set_temporary(self, temp)

        if temp:
            self._unregister()
        else:
            self._register()

    def _unregister(self):
        """Delete backend instance."""
        if self._registered_scene is not None:
            self._registered_scene.interface().delete_element(self.id())
            self._registered_scene = None

    def _register(self):
        """Create new backend instance."""
        scene = self.scene()
        if scene is not None and not self.is_temporary():
            scene.interface().create_element(
                guid=self.GUID(),
                parent=None,
                additional_metadata=self.metadata())
            self._registered_scene = scene

    def itemChange(self, change, value):
        if change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            # re-register
            self._unregister()
            self._register()
        return super().itemChange(change, value)
