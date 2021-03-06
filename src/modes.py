#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Defines a meta class mechanism to group context specific functionality of
one object into separate classes.

This mechanism abstract context sensitive behaviour of GUI elements like
mouse behaviour that is only valid for specific modes like inserting line
elements. With modes it is possible to define the functionality for
inserting lines in a separate class. After defining all relevant contexts
you can create classes based on these context and switch between them in
a controled fashion.

The mechanism is extremely useful for state sensitive mouse event,
where you often have to write matching code in several event handlers like
mousePressEvent, mouseMoveEvent and mouseLeaveEvent.
'''


def generate_mode_base(base_class, name):
    """
    returns base class which can be used to create mouse mode implementations
    of base_class and a decorator which can be used to mask mode specific
    methods

    See ModeBase.__doc__ for more information.

    @retun: ModeBase, mode_filtered
    """

    mode_attr_name = '_ModeBase__mode_' + name
    assert not hasattr(base_class, mode_attr_name)
    mode_setter_name = 'set%sMode' % (name.capitalize())
    assert not hasattr(base_class, mode_setter_name)
    mode_enter_name = '%s_enter' % name.lower() if name else 'enter'
    assert not hasattr(base_class, mode_enter_name)
    mode_leave_name = '%s_leave' % name.lower() if name else 'leave'
    assert not hasattr(base_class, mode_leave_name)

    # decorator
    class mode_filtered(object):
        def __init__(self, func):
            self.func = func

        def __repr__(self):
            return "<@filter_%s_mode: %s>" % (name, self.func)

    def generate_filter(inst, func, attr_name):
        def filter(self, *args, **kargs):
            mode = getattr(self, mode_attr_name)
            if mode is inst or (mode is not None and
                                issubclass(mode, inst)):
                return func(self, *args, **kargs)
            else:
                try:
                    super_attr = getattr(super(inst, self), attr_name)
                except AttributeError:
                    pass
                else:
                    return super_attr(*args, **kargs)

        filter.__name__ = name + '_filtered_' + attr_name + ': ' + repr(func)
        return filter

    class ModeMeta(type(base_class)):
        def __new__(cls, clsname, bases, attrs):
            inst = super().__new__(cls, clsname, bases, attrs)
            for name, attr in attrs.items():
                if isinstance(attr, mode_filtered):
                    func = attr.func
                elif name in [mode_enter_name, mode_leave_name]:
                    func = attr
                else:
                    continue
                setattr(inst, name, generate_filter(inst, func, name))
            return inst

    class ModeBase(base_class, metaclass=ModeMeta):
        """
        Base Class for implementing a specific mouse mode

        To use this class you should derive from InteractiveGridView and as
        many BaseMouseMode subclasses you want. Then you can use set_mouse_mode
        to select a specific enable / switch mouse modes.

        Methods masked with the decorator returned by generate_mode_base will
        only be resolved when self._mouse_mode is the subclass.

        Modes can be set with a special method named according to the mode
        name. Examples:
            name='mouse' --> self.setMouseMode( ... )
            name='InSeRt' --> self.setInsertMode( ... )
            name='' --> self.setMode( ... )

        Use super to call base class implementations

        When a mode is set the approriate Mode.enter method is calld,
        respectively when the mode is disabled. The naming convention is:
            name='mouse' --> mouse_enter, mouse_leave
            name='InSeRt' --> insert_enter, insert_leave
            name='' --> enter, leave
        These methods are automatically mode filtered.
        """

        def __init__(self, *args, **kargs):
            super().__init__(*args, **kargs)
            setattr(self, mode_attr_name, None)

        locals()[mode_enter_name] = lambda self: None  # noqa
        locals()[mode_enter_name].__doc__ = \
            """
            called when the mouse mode is activated

            This method gets automatically mode_filtered.
            """

        locals()[mode_leave_name] = lambda self: None  # noqa
        locals()[mode_leave_name].__doc__ = \
            """
            called when the mouse mode is  activated

            This method gets automatically mode_filtered.
            """

        def _mode_setter(self, mode):
            assert mode is None or issubclass(mode, ModeBase)
            old_mode = getattr(self, mode_attr_name)
            if mode is not old_mode:
                try:
                    if old_mode is not None:
                        getattr(old_mode, mode_leave_name)(self)
                finally:
                    setattr(self, mode_attr_name, mode)
                    if mode is not None:
                        getattr(mode, mode_enter_name)(self)

        _mode_setter.__name__ = mode_setter_name
        locals()[mode_setter_name] = _mode_setter
        del locals()['_mode_setter']

    return ModeBase, mode_filtered
