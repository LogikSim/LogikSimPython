#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#

"""
Contains configuration storage and loaded related functionality
"""

from PySide import QtCore

def Setting(settings_type, name, doc = None):
    """
    Class decorator for adding one setting to the Settings class.
    A setting consists of a underlying variable "_<name>" holding the value,
    a property "<name>" for manipulating the value as well as a signal
    "<name>_changed" which notifies of changes to the property.

    :param settings_type: Type of the variable
    :param name: Name of the property/setting
    :param doc: Optional docstring for the property
    :return: Decorated Settings class
    """
    def decorator(cls):
        variable_name = "_" + name
        signal_name = name + "_changed"
        setattr(cls, signal_name, QtCore.Signal())
        setattr(cls, name, QtCore.Property(type = settings_type,
                                           fget = lambda self: getattr(self, variable_name),
                                           fset = lambda self, value: setattr(self, variable_name, value),
                                           notify = getattr(cls, signal_name),
                                           #doc = doc)) #FIXME: If I set a docstring here the application crashes on shutdown
                                            ))

        cls._settings_list.append((name, settings_type))
        cls.__doc__ += "    {0:10s} {1:15s} {2}\n".format(name, str(type), doc) #FIXME: For some reason this won't chain properly
        return cls

    return decorator

@Setting(QtCore.QByteArray, "geometry", "Stores main window geometry")
#@Setting(QtCore.QByteArray, "state", "Stores main window state")
class Settings(QtCore.QObject):
    """
    Class for storing and loading LogikSim settings.
    Every setting is reflected as a property in this object
    and has a corresponding signal settingsname_changed
    which can be used to react to changes.

    Get global singleton from settings() function for normal use.

    For adding settings use the "Settings" decorator (see prior uses).
    """
    def __init__(self, settings = None, parent = None):
        super().__init__(parent)

        self._settings = QtCore.QSettings(self) if settings is None else settings
        self._raise_on_error("initializing settings")

        # Set default values, we initialize those explicitly here so
        # IDEs pick them up and offer auto-completion.
        self.geometry = QtCore.QByteArray()
        self.state = QtCore.QByteArray()

        self.load()

        # Wire up global changed signal
        for (name, _) in self._settings_list:
            getattr(self, name + "_changed").connect(self.changed)

    def _raise_on_error(self, action):
        if self._settings.status() is QtCore.QSettings.NoError:
            return

        what = self._settings.status()
        if self._settings.status() is QtCore.QSettings.AccessError:
            what = "An access error occurred (e.g. trying to write to a read-only file)"
        elif self._settings.status() is QtCore.QSettings.AccessError:
            what = "A format error occurred (e.g. loading a malformed INI file)."

        raise Exception("{1} when {0}".format(action, what))

    def load(self):
        """
        Load configuration from settings.
        """
        self._settings.sync()
        self._raise_on_error("loading settings")

        for (name, settingsType) in self._settings_list:
            setattr(self, name, self._settings.value(name, getattr(self, name)))
            self._raise_on_error("loading {0} setting".format(name))

    def save(self):
        """
        Store configuration to settings.
        """
        for (name, settingsType) in self._settings_list:
            self._settings.setValue(name, getattr(self, name))
            self._raise_on_error("saving {0} setting".format(name))

        self._settings.sync()
        self._raise_on_error("saving settings")

    changed = QtCore.Signal()

    _settings_list = []


_settings = None # Settings singleton stored here

def settings():
    """
    Returns the global settings singleton.
    Expects setupSettings to be called first
    """
    global _settings
    assert _settings is not None, "setupSettings not yet called"
    return _settings

def setup_settings(qsettingsObject = None, parent = None):
    """
    Initializes the global settings singleton.

    :param qsettingsObject QSettings object to use. Use None for default.
    :param parent QObject parent of global Settings singleton.
    """
    global _settings
    _settings = Settings(qsettingsObject, parent)
    return settings()


if __name__ == "__main__":
    # When imported directly setup basic global settings configuration
    # to make sure the class can properly initialize.
    QtCore.QCoreApplication.setOrganizationName("logiksim.org")
    QtCore.QCoreApplication.setOrganizationDomain("logiksim.org")
    QtCore.QCoreApplication.setApplicationName("LogikSim")
