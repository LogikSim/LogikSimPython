#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2011

@author: Christian
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
    
    # decorator
    class mode_filtered(object):
        def __init__(self, func):
            self.func = func
    
    def generate_filter(inst, func, name):
        def filter(self, *args, **kargs):
            mode = getattr(self, mode_attr_name)
            if mode is inst or (mode is not None and 
                    issubclass(mode, inst)):
                return func(self, *args, **kargs)
            else:
                try:
                    super_attr = getattr(super(inst, self), name)
                except AttributeError:
                    pass
                else:
                    return super_attr(*args, **kargs)
        filter.func_name = 'filtered_' + name
        return filter
    
    class ModeMeta(type(base_class)):
        def __new__(cls, clsname, bases, attrs):
            inst = super(ModeMeta, cls).__new__(cls, clsname, bases, attrs)
            
            for name, attr in attrs.iteritems():
                if isinstance(attr, mode_filtered):
                    func = attr.func
                elif name in ['enter', 'leave']:
                    func = attr
                else:
                    continue
                setattr(inst, name, generate_filter(inst, func, name))
            
            return inst
    
    class ModeBase(base_class):
        """
        Base Class for implementing a specific mouse mode
    
        To use this class you should derive from BasicGridView and as many
        BaseMouseMode subclasses you want. Then you can use set_mouse_mode
        to select a specific enable / switch mouse modes.
        
        Methods masked with the decorator returned by generate_mode_base will 
        only be resolved when self._mouse_mode is the subclass.
        
        Modes can be set with a special method named according to the mode
        name. Examples:
            name='mouse' --> self.setMouseMode( ... )
            name='insert' --> self.setInsertMode( ... )
            name='' --> self.setMode( ... )
        
        Use super to call base class implementations
        """
        __metaclass__ = ModeMeta
        
        def __init__(self, *args, **kargs):
            super(ModeBase, self).__init__(*args, **kargs)
            setattr(self, mode_attr_name, None)
        
        def enter(self):
            """
            called when the mouse mode is  activated
            
            This method gets automatically mouse_mode_filtered.
            """
        
        def leave(self):
            """
            called when the mouse mode is deactivated
            
            This method gets automatically mouse_mode_filtered.
            """
        
        def _mode_setter(self, mode):
            assert mode is None or issubclass(mode, ModeBase)
            old_mode = getattr(self, mode_attr_name)
            if mode is not old_mode:
                if old_mode is not None:
                    old_mode.leave(self)
                setattr(self, mode_attr_name, mode)
                if mode is not None:
                    mode.enter(self)
        _mode_setter.func_name = mode_setter_name
        locals()[mode_setter_name] = _mode_setter
        del locals()['_mode_setter']
    
    return ModeBase, mode_filtered
