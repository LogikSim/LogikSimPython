#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2011

@author: Christian
'''

import unittest

from mouse_modes import generate_mouse_mode_base

class TestSubclassing(unittest.TestCase):
    def test_enter_leave(self):
        calls = []
        class Base(object):
            pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            def enter(self):
                super(A, self).enter()
                calls.append('A.enter')
            def leave(self):
                super(A, self).leave()
                calls.append('A.leave')
        class B(BaseMouseMode):
            def enter(self):
                super(B, self).enter()
                calls.append('B.enter')
            def leave(self):
                super(B, self).leave()
                calls.append('B.leave')
        class User(A, B, Base):
            pass
        
        u = User()
        self.assertEqual(calls, [])
        u.set_mouse_mode(A)
        self.assertEqual(calls, ['A.enter'])
        u.set_mouse_mode(A)
        self.assertEqual(calls, ['A.enter'])
        u.set_mouse_mode(B)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter'])
        u.set_mouse_mode(None)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter', 'B.leave'])
    
    def test_member_resolution(self):
        calls = []
        class Base(object):
            def __getattribute__(self, attrname):
                
            def foo(self):
                calls.append('Base.foo')
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            def foo(self):
                super(A, self).foo()
                calls.append('A.foo')
        class B(BaseMouseMode):
            def foo(self):
                super(B, self).foo()
                calls.append('B.foo')
        class User(A, B, Base):
            def foo(self):
                super(User, self).foo()
                calls.append('User.foo')
        
        # None
        u = User()
        u.foo()
        self.assertEqual(calls, ['Base.foo', 'User.foo'])
        # B
        del calls[:]
        u.set_mouse_mode(B)
        u.foo()
        self.assertEqual(calls, ['Base.foo', 'B.foo', 'User.foo', ])
        # A
        del calls[:]
        u.set_mouse_mode(A)
        u.foo()
        self.assertEqual(calls, ['Base.foo', 'A.foo', 'User.foo', ])
    
    def test_base_class_with_metaclass(self):
        class BaseMeta(type): pass
        class Base(object):
            __metaclass__ = BaseMeta
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode): pass
        class User(A, Base): pass
        
        u = User()
        self.assertIsInstance(u, A)
        self.assertIsInstance(u, Base)
        self.assertIsInstance(User, BaseMeta)
    
    def test_underlined_methods(self):
        calls = []
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            def _foo(self):
                calls.append('A._foo')
        class User(A, Base): pass
        
        u = User()
        u.set_mouse_mode(None)
        u._foo()
        self.assertListEqual(calls, ['A._foo'])
    
    def test_attributes(self):
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            cls_attr = 'test_cls'
            def __init__(self, *args, **kargs):
                super(A, self).__init__(*args, **kargs)
                self.inst_attr = 'test_inst'
        class User(A, Base): pass
        
        u = User()
        u.set_mouse_mode(None)
        self.assertEqual(u.inst_attr, 'test_inst')
        self.assertEqual(u.cls_attr, 'test_cls')
    
    def test_classmethods(self):
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @classmethod
            def foo(cls):
                return 1
        class User(A, Base): pass
        
        u = User()
        u.set_mouse_mode(None)
        self.assertEqual(u.foo(), 1)

