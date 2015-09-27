# -*- coding: utf-8 -*-

from __future__ import absolute_import

from types import ModuleType

import pytest

from .. import Model, configure, AttrDict
from ..model import to_underscore
from ..options import _Options


def test_nometa():
    configure(database='test')

    try:
        class SomeModel(Model):
            pass
    except Exception:
        pytest.fail('A model with no Meta is perfectly fine :)')

    del _Options.database


def test_to_underscore():
    assert to_underscore('Foobar') == 'foobar'
    assert to_underscore('fooBar') == 'foo_bar'
    assert to_underscore('FooBar42') == 'foo_bar42'
    assert to_underscore('Foo42Bar') == 'foo42_bar'
    assert to_underscore('FOOBar') == 'foo_bar'
    assert to_underscore('fooBAR') == 'foo_bar'


def test_configure():
    # a) keyword arguments
    assert not hasattr(_Options, 'foo')
    configure(foo='bar')
    assert hasattr(_Options, 'foo')
    del _Options.foo

    # b) module
    assert not hasattr(_Options, 'foo')
    module = ModuleType('config')
    module.MONGODB_FOO = 'bar'
    module.NON_MONGO_ATTR = 'bar'
    configure(foo='bar')
    assert not hasattr(_Options, 'NON_MONGO_ATTR')
    assert not hasattr(_Options, 'MONGODB_FOO')
    assert hasattr(_Options, 'foo')
    del _Options.foo

    # c) non-module (fails silently)
    try:
        configure(42)
        configure(None)
        configure('foobar')
    except Exception:
        pytest.fail('configure() should fail silently on invalid input.')


def test_options_init():
    class Meta:
        foo = 'bar'

    options = _Options(Meta)
    assert options.foo, 'bar'


def test_optoins_configure():
    # Options have no defaults yet -- configure() was never called.
    with pytest.raises(AttributeError):
        _Options.foo

    configure(foo='bar')

    try:
        assert _Options.foo == 'bar'
    except AttributeError:
        pytest.fail('Options.foo should\'ve been set.')

    del _Options.foo


def test_attr_dict():
    d = AttrDict()
    d.x = 1
    d.y = {}
    d.y.z = 2
    d.q = AttrDict()
    d.q.r = 3
    d.q.s = AttrDict(AttrDict({}))  # I'm just being weird
    d['q']['s']['t'] = 4

    assert d.x == 1
    assert d.y.z == d['y']['z']
    assert d.y.z == 2
    assert d.q.r == d['q']['r']
    assert d.q.r == 3
    assert d.q.s.t == d['q'].s['t']  # Don't do this in real code.
    assert isinstance(d, dict)
    assert isinstance(d.y, dict)
    assert isinstance(d['y'], dict)
    assert isinstance(d.q.s, dict)
    assert isinstance(d['q']['s'], dict)
    assert isinstance(d.q.s, dict)
    assert isinstance(d['q']['s'], dict)

    # We can say AttrDict(AttrDict({'foo': 'bar'})) with no ill effects.
    e = AttrDict(d)
    assert e == d
    assert e.x == 1
    assert e.y.z == d['y']['z']
    assert e.y.z == 2
    assert e.q.r == d['q']['r']
    assert e.q.r == 3
    assert isinstance(e, dict)
    assert isinstance(e.y, dict)
    assert isinstance(e['y'], dict)


def test_attr_dict_kwargs():
    """Test that attributes can be set as named arguments"""
    d = AttrDict(x=0, y=1)
    assert d.x == 0
    assert d.y == 1
    # We can stil have an initial document and named values
    # named values take over.
    e = AttrDict({'x':0, 'y':1}, x=1)
    assert e.x == 1
    assert e.y == 1
    #We can pass a dictionary as a value
    f = AttrDict( x = {'a':1 })
    assert f.x.a == 1


def test_attrdict_del():
    f = AttrDict()
    f.x = 1
    del f.x
    with pytest.raises(AttributeError):
        tmp = f.x
    with pytest.raises(KeyError):
        tmp = f['x']

    f['x'] = 1
    del f['x']

    with pytest.raises(KeyError):
        tmp = f['x']
    with pytest.raises(AttributeError):
        tmp = f.x


def test_attr_dict_from_dict():
    d = {
        'a': 1,
        'b': {
            'c': 2,
            'd': {
                'e': 3,
                'f': 4,
               },
            'g': 5,
            },
        'h': 6,
        'i': 7,
        }
    attr_dict = AttrDict(d)
    assert attr_dict.a == 1
    assert attr_dict['a'] == 1

    assert attr_dict.b.c == 2
    assert attr_dict['b'].c == 2
    assert attr_dict['b']['c'] == 2
    assert attr_dict.b['c'] == 2

    assert attr_dict.b.d.e == 3
    assert attr_dict['b']['d']['e'] == 3



class AttrDictDerived(AttrDict):

    def __setitem__(self, key, value):
        if isinstance(value, (int, float)):
            value *= 5
        super(AttrDictDerived, self).__setitem__(key, value)

    def __setattr__(self, attr, value):
        if isinstance(value, (int, float)):
            value += 7
        return super(AttrDictDerived, self).__setattr__(attr, value)

    def __delattr__(self, key):
        if not hasattr(self, 'old_attrs'):
            super(AttrDictDerived, self).__setattr__('old_attrs', set())
        self.old_attrs.add(key)
        return super(AttrDictDerived, self).__delattr__(key)

    def __delitem__(self, key):
        if not hasattr(self, 'old_items'):
            super(AttrDictDerived, self).__setattr__('old_items', set())
        self.old_items.add(key)
        return super(AttrDictDerived, self).__delitem__(key)

    def __getattr__(self, attr):
        value = super(AttrDictDerived, self).__getattr__(attr)
        if isinstance(value, (int, float)):
            value += 11
        return value


class test_attr_dict_derived():
    """Test classes that are derived from AttrDict that also override
    setitem and getattr, etc.  This is actually a test of the behavior of
    AttrDict itself, and that it doesn't generate infinite recursion when
    these methods are overridden.  The math below and modifying values in
    setitem and setattr is crazy, so please forgive me."""
    test_derived = AttrDictDerived()
    test_derived.x = 3
    assert test_derived['x'] == (3 + 7) * 5

    assert test_derived.x == ((3+7) * 5) + 11
    test_derived['y'] = 5
    assert test_derived['y'] == 5 * 5
    assert test_derived.y == (5 * 5) + 11

    test_derived_too = AttrDictDerived()
    test_derived_too['x'] = 1
    test_derived_too['y'] = 1
    test_derived_too['z'] = 1
    del test_derived_too['x']
    del test_derived_too['z']
    del test_derived_too['y']
    test_derived_too.f = 1
    assert test_derived_too.f == ((1 + 7) * 5) + 11
    del test_derived_too.f
    with pytest.raises(AttributeError):
        assert test_derived_too.f == 1
    # Easiest way to test override of delattr and delitem is by keeping
    # track of what happened.
    assert test_derived_too.old_items == set(['x', 'y', 'z'])
    assert test_derived_too['old_items'] == set(['x', 'y', 'z'])
    assert test_derived_too.old_attrs == set(['f'])
    assert test_derived_too['old_attrs'] == set(['f'])
