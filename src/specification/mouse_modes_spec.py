#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jun 11, 2011

@author: Christian
'''

import unittest

from mouse_modes import generate_mouse_mode_base, mouse_mode_filtered

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
            def foo(self):
                calls.append('Base.foo')
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @mouse_mode_filtered
            def foo(self):
                super(A, self).foo()
                calls.append('A.foo')
        class B(BaseMouseMode):
            @mouse_mode_filtered
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
    
    def test_return_value(self):
        class Base(object):
            def foo(self):
                return 1
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @mouse_mode_filtered
            def foo(self):
                return super(A, self).foo() + 2
        class User(A, Base):
            def foo(self):
                return super(User, self).foo() + 4
        # None
        u = User()
        self.assertEqual(u.foo(), 5)
        # A
        u.set_mouse_mode(A)
        self.assertEqual(u.foo(), 7)
    
    def test_filtered_return_value(self):
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @mouse_mode_filtered
            def foo(self):
                return 1
        class User(A, Base): pass
        # None
        u = User()
        self.assertEqual(u.foo(), None)
        # A
        u.set_mouse_mode(A)
        self.assertEqual(u.foo(), 1)
        
    
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
    
    def test_unfiltered_methods(self):
        calls = []
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            def foo(self):
                calls.append('A.foo')
        class User(A, Base): pass
        
        u = User()
        u.set_mouse_mode(None)
        u.foo()
        self.assertListEqual(calls, ['A.foo'])
    
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
    
    def test_mouse_mode_sub_classing(self):
        calls = []
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @mouse_mode_filtered
            def foo(self):
                calls.append('A.foo')
        class AA(A):
            @mouse_mode_filtered
            def foo(self):
                super(AA, self).foo()
                calls.append('AA.foo')
        class User(AA, Base): pass
        # None
        u = User()
        u.foo()
        self.assertListEqual(calls, [])
        # AA
        u.set_mouse_mode(AA)
        u.foo()
        self.assertListEqual(calls, ['A.foo', 'AA.foo'])
        # A
        del calls[:]
        u.set_mouse_mode(A)
        u.foo()
        self.assertListEqual(calls, ['A.foo'])
    
    def test_filter_multiple_methods(self):
        class Base(object): pass
        BaseMouseMode = generate_mouse_mode_base(Base)
        class A(BaseMouseMode):
            @mouse_mode_filtered
            def foo(self):
                return 'foo'
            @mouse_mode_filtered
            def bar(self):
                return 'bar'
        class User(A, Base): pass
        # A
        u = User()
        u.set_mouse_mode(A)
        self.assertEqual(u.foo(), 'foo')
        self.assertEqual(u.bar(), 'bar')
