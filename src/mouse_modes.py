#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2011

@author: Christian
'''

import new

from PySide import QtCore

from base_graphics_framework import BasicGridView
import logic_item


def generate_mouse_mode_base(base_class):
    """
    returns base class which can be used to create mouse mode implementations
    of base_class.
    
    See generate_mouse_mode_base.BaseMouseMode.__doc__ for more information.
    """
    class MouseModeMeta(type(base_class)):
        def __new__(cls, name, bases, attrs):
            inst = super(MouseModeMeta, cls).__new__(cls, name, bases, attrs)
            # modify attribute resolution except for classes that derive
            # from base_class. This will be our BaseMouseMode and the one
            # that want to use specific mouse modes.
            print inst, base_class not in bases
            if base_class not in bases:
                def __getattribute__(self, attrname):
                    attr = super(inst, self).__getattribute__(attrname)
                    if not name.startswith('_') and isinstance(attr, 
                            new.instancemethod) and super(inst, self).\
                            __getattribute__('_mouse_mode') is not inst:
                        print name, attrname, 'dummy'
                        def dummy(*args, **kargs):
                            try:
                                super_func = getattr(super(inst, self), 
                                        attrname)
                            except AttributeError:
                                return
                            else:
                                return super_func(*args, **kargs)
                        return dummy
                    else:
                        print name, attrname, 'attr'
                        return attr
                inst.__getattribute__ = __getattribute__
            else:
                inst.__getattribute__ = base_class.__getattribute__
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
            pass
        
        def enter(self):
            """ called when the mouse mode is  activated """
        
        def leave(self):
            """ called when the mouse mode is deactivated """
    
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




