# -*- coding: utf-8 -*-
from types import ModuleType

import pytest

from minimongo import Model, configure, AttrDict
from minimongo.options import _Options
from minimongo.model import to_underscore


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
    # etc.


class AttrDictDerived(AttrDict):
    def __setitem__(self, key, value):
        print "setitem %s %s" % (str(key), str(value))
        if isinstance(value, (int, float)):
            value *= 2
        super(AttrDictDerived, self).__setitem__(key, value)

    def __setattr__(self, attr, value):
        print "setattr %s %s" % (str(attr), str(value))
        if isinstance(value, (int, float)):
            value += 0.5
        return super(AttrDictDerived, self).__setattr__(attr, value)

    def __delattr__(self, key):
        print "delattr %s" % key
        if not hasattr(self, 'old_attrs'):
            super(AttrDictDerived, self).__setattr__('old_attrs', set())
        self.old_attrs.add(key)
        return super(AttrDictDerived, self).__delattr__(key)

    def __delitem__(self, key):
        print "delitem %s" % key
        if not hasattr(self, 'old_items'):
            super(AttrDictDerived, self).__setattr__('old_items', set())
        self.old_items.add(key)
        return super(AttrDictDerived, self).__delitem__(key)

    def __getattr__(self, attr):
        print "getattr %s" % attr
        value = super(AttrDictDerived, self).__getattr__(attr)
        if isinstance(value, (int, float)):
            value += 3
        return value


class test_attr_dict_derived():
    """Test classes that are derived from AttrDict that also override
    setitem and getattr, etc.  This is actually a test of the behavior of
    AttrDict itself, and that it doesn't generate infinite recursion when
    these methods are overridden.  """
    test_derived = AttrDictDerived()
    test_derived.x = 3
    assert test_derived['x'] == 3.5
    assert test_derived.x == 6.5
    test_derived['y'] = 5
    assert test_derived['y'] == 10
    assert test_derived.y == 13

    test_derived_too = AttrDictDerived()
    test_derived_too['x'] = 1
    test_derived_too['y'] = 1
    test_derived_too['z'] = 1
    del test_derived_too['x']
    del test_derived_too['z']
    del test_derived_too['y']
    test_derived_too.f = 1
    assert test_derived_too.f == 4.5
    del test_derived_too.f
    with pytest.raises(AttributeError):
        assert test_derived_too.f == 1
    assert test_derived_too.old_items == set(['x', 'y', 'z'])
    assert test_derived_too['old_items'] == set(['x', 'y', 'z'])
    assert test_derived_too.old_attrs == set(['f'])
    assert test_derived_too['old_attrs'] == set(['f'])
