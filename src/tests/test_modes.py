#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2014 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can 
# be found in the LICENSE.txt file.
#
'''
Test the modes meta class mechanism.
'''

import unittest

from modes import generate_mode_base

class TestSubclassing(unittest.TestCase):
    def test_mode_name(self):
        class Base(object): pass
        BaseMode, _ = generate_mode_base(Base, 'Mouse')
        class User(BaseMode, Base): pass
        self.assertTrue(hasattr(User, 'setMouseMode'))
    
    def test_enter_leave(self):
        calls = []
        class Base(object):
            pass
        BaseMode, _ = generate_mode_base(Base, '')
        class A(BaseMode):
            def enter(self):
                super(A, self).enter()
                calls.append('A.enter')
            def leave(self):
                super(A, self).leave()
                calls.append('A.leave')
        class B(BaseMode):
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
        u.setMode(A)
        self.assertEqual(calls, ['A.enter'])
        u.setMode(A)
        self.assertEqual(calls, ['A.enter'])
        u.setMode(B)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter'])
        u.setMode(None)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter', 'B.leave'])
    
    def test_enter_leave_special_name(self):
        calls = []
        class Base(object):
            pass
        BaseMode, _ = generate_mode_base(Base, 'fOo')
        class A(BaseMode):
            def foo_enter(self):
                super(A, self).foo_enter()
                calls.append('A.enter')
            def foo_leave(self):
                super(A, self).foo_leave()
                calls.append('A.leave')
        class B(BaseMode):
            def foo_enter(self):
                super(B, self).foo_enter()
                calls.append('B.enter')
            def foo_leave(self):
                super(B, self).foo_leave()
                calls.append('B.leave')
        class User(A, B, Base):
            pass
        
        u = User()
        self.assertEqual(calls, [])
        u.setFooMode(A)
        self.assertEqual(calls, ['A.enter'])
        u.setFooMode(A)
        self.assertEqual(calls, ['A.enter'])
        u.setFooMode(B)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter'])
        u.setFooMode(None)
        self.assertEqual(calls, ['A.enter', 'A.leave', 'B.enter', 'B.leave'])
    
    def test_member_resolution(self):
        calls = []
        class Base(object):
            def foo(self):
                calls.append('Base.foo')
        BaseMode, mode_filtered = generate_mode_base(Base, '')
        class A(BaseMode):
            @mode_filtered
            def foo(self):
                super(A, self).foo()
                calls.append('A.foo')
        class B(BaseMode):
            @mode_filtered
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
        u.setMode(B)
        u.foo()
        self.assertEqual(calls, ['Base.foo', 'B.foo', 'User.foo', ])
        # A
        del calls[:]
        u.setMode(A)
        u.foo()
        self.assertEqual(calls, ['Base.foo', 'A.foo', 'User.foo', ])
    
    def test_return_value(self):
        class Base(object):
            def foo(self):
                return 1
        BaseMode, mode_filtered = generate_mode_base(Base, '')
        class A(BaseMode):
            @mode_filtered
            def foo(self):
                return super(A, self).foo() + 2
        class User(A, Base):
            def foo(self):
                return super(User, self).foo() + 4
        # None
        u = User()
        self.assertEqual(u.foo(), 5)
        # A
        u.setMode(A)
        self.assertEqual(u.foo(), 7)
    
    def test_filtered_return_value(self):
        class Base(object): pass
        BaseMode, mode_filtered = generate_mode_base(Base, '')
        class A(BaseMode):
            @mode_filtered
            def foo(self):
                return 1
        class User(A, Base): pass
        # None
        u = User()
        self.assertEqual(u.foo(), None)
        # A
        u.setMode(A)
        self.assertEqual(u.foo(), 1)
        
    
    def test_base_class_with_metaclass(self):
        class BaseMeta(type): pass
        class Base(object, metaclass=BaseMeta):
            pass
        BaseMode, _ = generate_mode_base(Base, '')
        class A(BaseMode): pass
        class User(A, Base): pass
        
        u = User()
        self.assertIsInstance(u, A)
        self.assertIsInstance(u, Base)
        self.assertIsInstance(User, BaseMeta)
    
    def test_unfiltered_methods(self):
        calls = []
        class Base(object): pass
        BaseMode, _ = generate_mode_base(Base, '')
        class A(BaseMode):
            def foo(self):
                calls.append('A.foo')
        class User(A, Base): pass
        
        u = User()
        u.setMode(None)
        u.foo()
        self.assertListEqual(calls, ['A.foo'])
    
    def test_attributes(self):
        class Base(object): pass
        BaseMode, _ = generate_mode_base(Base, '')
        class A(BaseMode):
            cls_attr = 'test_cls'
            def __init__(self, *args, **kargs):
                super(A, self).__init__(*args, **kargs)
                self.inst_attr = 'test_inst'
        class User(A, Base): pass
        
        u = User()
        u.setMode(None)
        self.assertEqual(u.inst_attr, 'test_inst')
        self.assertEqual(u.cls_attr, 'test_cls')
    
    def test_classmethods(self):
        class Base(object): pass
        BaseMode, _ = generate_mode_base(Base, '')
        class A(BaseMode):
            @classmethod
            def foo(cls):
                return 1
        class User(A, Base): pass
        
        u = User()
        u.setMode(None)
        self.assertEqual(u.foo(), 1)
    
    def test_mouse_mode_sub_classing(self):
        calls = []
        class Base(object): pass
        BaseMode, mode_filtered = generate_mode_base(Base, '')
        class A(BaseMode):
            @mode_filtered
            def foo(self):
                calls.append('A.foo')
        class AA(A):
            @mode_filtered
            def foo(self):
                super(AA, self).foo()
                calls.append('AA.foo')
        class User(AA, Base): pass
        # None
        u = User()
        u.foo()
        self.assertListEqual(calls, [])
        # AA
        u.setMode(AA)
        u.foo()
        self.assertListEqual(calls, ['A.foo', 'AA.foo'])
        # A
        del calls[:]
        u.setMode(A)
        u.foo()
        self.assertListEqual(calls, ['A.foo'])
    
    def test_filter_multiple_methods(self):
        class Base(object): pass
        BaseMode, mode_filtered = generate_mode_base(Base, '')
        class A(BaseMode):
            @mode_filtered
            def foo(self):
                return 'foo'
            @mode_filtered
            def bar(self):
                return 'bar'
        class User(A, Base): pass
        # A
        u = User()
        u.setMode(A)
        self.assertEqual(u.foo(), 'foo')
        self.assertEqual(u.bar(), 'bar')
    
    def test_two_independent_modes(self):
        class Base(object):
            def foo(self):
                return 1
        BaseAlphaMode, alpha_mode_filtered = generate_mode_base(Base, 'alpha')
        class Alpha(BaseAlphaMode):
            @alpha_mode_filtered
            def foo(self):
                return super(Alpha, self).foo() + 2
        BaseBetaMode, beta_mode_filtered = generate_mode_base(Base, 'beta')
        class Beta(BaseBetaMode):
            @beta_mode_filtered
            def foo(self):
                return super(Beta, self).foo() + 4
        class UserMeta(type(Alpha), type(Beta)): pass
        class User(Alpha, Beta, metaclass=UserMeta):
            def foo(self):
                return super(User, self).foo() + 8
        # None, None
        u = User()
        self.assertEqual(u.foo(), 9)
        # Alpha, None
        u.setAlphaMode(Alpha)
        self.assertEqual(u.foo(), 11)
        # Alpha, Beta
        u.setBetaMode(Beta)
        self.assertEqual(u.foo(), 15)
        # None, Beta
        u.setAlphaMode(None)
        self.assertEqual(u.foo(), 13)
    
    def test_nested_sub_mode(self):
        calls = []
        class Base(object):
            def foo(self):
                calls.append('Base.foo')
        BaseLangMode, lang_mode_filtered = generate_mode_base(Base, 'lang')
        BaseGreekMode, greek_mode_filtered = generate_mode_base(
                BaseLangMode, 'greek')
        class Alpha(BaseGreekMode):
            @greek_mode_filtered
            def foo(self):
                super(Alpha, self).foo()
                calls.append('Alpha.foo')
        class Beta(BaseGreekMode):
            @greek_mode_filtered
            def foo(self):
                super(Beta, self).foo()
                calls.append('Beta.foo')
        class Greek(Alpha, Beta):
            @lang_mode_filtered
            def foo(self):
                super(Greek, self).foo()
                calls.append('Greek.foo')
            def lang_enter(self):
                super(Greek, self).lang_enter()
                self.setGreekMode(Alpha)
            def lang_leave(self):
                super(Greek, self).lang_leave()
                self.setGreekMode(None)
        class Latin(BaseLangMode):
            @lang_mode_filtered
            def foo(self):
                super(Latin, self).foo()
                calls.append('Latin.foo')
        class User(Greek, Latin):
            def foo(self):
                super(User, self).foo()
                calls.append('User.foo')
        # None, None
        u = User()
        u.foo()
        self.assertListEqual(calls, ['Base.foo', 'User.foo'])
        # Latin, None
        del calls[:]
        u.setLangMode(Latin)
        u.foo()
        self.assertListEqual(calls, ['Base.foo', 'Latin.foo', 'User.foo'])
        # Greek, Alpha
        del calls[:]
        u.setLangMode(Greek)
        u.foo()
        self.assertListEqual(calls, ['Base.foo', 'Alpha.foo', 'Greek.foo', 
                'User.foo'])
        # Greek, Beta
        del calls[:]
        u.setGreekMode(Beta)
        u.foo()
        self.assertListEqual(calls, ['Base.foo', 'Beta.foo', 'Greek.foo', 
                'User.foo'])
        # Latin, None
        del calls[:]
        u.setLangMode(Latin)
        u.foo()
        self.assertListEqual(calls, ['Base.foo', 'Latin.foo', 'User.foo'])

