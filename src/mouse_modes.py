#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2011

@author: Christian
'''

from PySide import QtCore

from base_graphics_framework import BasicGridView
import logic_item


class mouse_mode_filtered(object):
    def __init__(self, func):
        self.func = func

def _generate_filter(inst, func, name):
    def filter(self, *args, **kargs):
        mode = self._mouse_mode
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
    filter.func_name = 'filter_' + name
    return filter

def generate_mouse_mode_base(base_class):
    """
    returns base class which can be used to create mouse mode implementations
    of base_class.
    
    See generate_mouse_mode_base.BaseMouseMode.__doc__ for more information.
    """
    class MouseModeMeta(type(base_class)):
        def __new__(cls, clsname, bases, attrs):
            inst = super(MouseModeMeta, cls).__new__(cls, clsname, bases, attrs)
            
            for name, attr in attrs.iteritems():
                if isinstance(attr, mouse_mode_filtered):
                    func = attr.func
                elif name in ['enter', 'leave']:
                    func = attr
                else:
                    continue
                setattr(inst, name, _generate_filter(inst, func, name))
            
            return inst
    
    class BaseMouseMode(base_class):
        """
        Base Class for implementing a specific mouse mode
    
        To use this class you should derive from BasicGridView and as many
        BaseMouseMode subclasses you want. Then you can use set_mouse_mode
        to select a specific enable / switch mouse modes.
        
        Methods will only be resolved for subclasses when self._mouse_mode is 
        the subclass. (or if they start with a underline)
        
        Implement any mouse methods you need from QGraphicsView
        You can use all methods from BasicGridView
        Use super to call base class implementations
        """
        __metaclass__ = MouseModeMeta
        
        def __init__(self, *args, **kargs):
            super(BaseMouseMode, self).__init__(*args, **kargs)
            self._mouse_mode = None
        
        def set_mouse_mode(self, mode):
            if mode is not self._mouse_mode:
                if self._mouse_mode is not None:
                    self._mouse_mode.leave(self)
                self._mouse_mode = mode
                if mode is not None:
                    mode.enter(self)
        
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
    
    return BaseMouseMode


#BaseGridViewMouseMode = generate_mouse_mode_base(BasicGridView)
#
#
#class SelectItemsMode(BaseGridViewMouseMode):
#    def __init__(self, *args, **kargs):
#        super(SelectItemsMode, self).__init__(*args, **kargs)
#    
#    def enter(self):
#        super(SelectItemsMode, self).enter()
#    
#    def leave(self):
#        super(SelectItemsMode, self).enter()
#
#
#class InsertConnectorMode(BaseGridViewMouseMode):
#    def __init__(self, *args, **kargs):
#        super(InsertConnectorMode, self).__init__(*args, **kargs)
#        # stores start position and connector while inserting connectors
#        self._insert_connector_start = None
#        self._inserted_connector = None
#    
#    def mousePressEvent(self, event):
#        super(InsertConnectorMode, self).mousePressEvent(event)
#        
#        # left button
#        if event.button() is QtCore.Qt.LeftButton:
#            gpos = self.mapToSceneGrid(event.pos())
#            self._insert_connector_start = gpos
#            self._inserted_connector = logic_item.ConnectorItem(
#                    QtCore.QLineF(gpos, gpos))
#            self.scene().addItem(self._inserted_connector)




